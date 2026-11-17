"""Invented kickoff acceptance through actual M1/M4, runner transport and M2.

No match labels, kickoff anchors or restricted files are read by these tests.
"""
import unittest
import io
from unittest.mock import patch

import numpy as np

import games
import kickoff_check
from module4.stoppages import restart_windows
import run_possession as rp
from test_integrated_pipeline import pipeline
from test_stoppage_m2_gate import observation, missing, movement, pause


def kickoff(start=0, end=70, side=None):
    return dict(type="Kick Off (Start)", start_frame=start, end_frame=end, side=side)


class KickoffPipelineTests(unittest.TestCase):
    def test_graded_half_before_kickoff_is_dead_despite_close_players(self):
        frames = [dict(x=52.65)] * 100
        e, labels = pipeline(frames, [kickoff(60, 90)])
        self.assertEqual(labels, ["D"] * 100)
        self.assertTrue(e["initial_dead"][0])
        self.assertEqual(int(e["initial_dead"].sum()), 1)
        self.assertTrue(np.all(e["score_home"] == 1.))
        self.assertTrue(np.all(e["restart_score"] == 0))

    def test_approximate_tag_entry_and_expiry_do_not_restart_stationary_play(self):
        frames = [dict(x=52.65)] * 80 + [dict(x=52.65 + .5 * (i + 1), speeds=(3., 3., 3.)) for i in range(30)]
        e, labels = pipeline(frames, [kickoff(15, 45, "A")])
        self.assertEqual(labels[:80], ["D"] * 80)
        positives = np.flatnonzero(e["restart_score"] >= .5)
        self.assertGreater(len(positives), 3)
        confirm = int(positives[0]) + 2
        self.assertEqual(labels[confirm - 1], "D")
        self.assertEqual(labels[confirm], "X")  # expired side context is not reused
        self.assertEqual(labels[-1], "H")

    def test_supported_kickoff_known_and_unknown_sides(self):
        frames = [dict(x=52.65)] * 25 + [dict(x=52.65 + .5 * (i + 1), speeds=(3., 3., 3.)) for i in range(35)]
        for side in ("H", "A", None):
            with self.subTest(side=side):
                e, labels = pipeline(frames, [kickoff(0, 100, side)])
                first = int(np.flatnonzero(e["restart_score"] >= .5)[0])
                self.assertEqual(labels[:first + 2], ["D"] * (first + 2))
                self.assertEqual(labels[first + 2], side or "X")
                self.assertEqual(labels[-1], "H")

    def test_already_live_at_graded_start_can_recover_without_observed_pause(self):
        frames = [dict(x=40 + .5 * i, speeds=(3., 3., 3.)) for i in range(35)]
        e, labels = pipeline(frames, [kickoff(-10, 15)])
        self.assertTrue(np.any(e["restart_score"] >= .5))
        self.assertEqual(labels[0], "D")  # uncertain tag-backed prior, not exact kickoff truth
        self.assertEqual(labels[-1], "H")
        self.assertNotIn("D", labels[10:])
        # A half without half-start kickoff context keeps the existing untagged policy.
        _, untagged = pipeline(frames)
        self.assertEqual(untagged[:11], ["X"] * 11)
        self.assertEqual(untagged[11:], ["H"] * 24)

    def test_missing_observations_do_not_erase_tag_supported_initial_dead(self):
        e, labels = pipeline(missing(3), [kickoff(10, 40)])
        self.assertEqual(labels, ["D"] * 75)
        self.assertFalse(np.any(e["ball_visible"]))
        self.assertFalse(np.any(e["restart_available"]))
        _, unknown = pipeline(missing(3))
        self.assertEqual(unknown, ["X"] * 75)

    def test_ambiguous_kickoff_tags_do_not_create_a_confident_initial_prior(self):
        for windows in ([kickoff(5, 30, "H"), kickoff(10, 50, "A")], [kickoff(10, 10)]):
            e, labels = pipeline(missing(3), windows)
            self.assertFalse(np.any(e["initial_dead"]))
            self.assertEqual(labels, ["X"] * 75)

    def test_conflicting_side_context_does_not_invent_a_restart_owner(self):
        frames = [dict(x=52.65)] * 25 + [dict(x=52.65 + .5 * (i + 1), speeds=()) for i in range(30)]
        ordinary = dict(type="Throw-in", start_frame=0, end_frame=100, side="A")
        e, labels = pipeline(frames, [kickoff(0, 100, "H"), ordinary])
        first = int(np.flatnonzero(e["restart_score"] >= .5)[0])
        self.assertEqual(labels[first + 2:], ["X"] * (len(labels) - first - 2))
        self.assertTrue(all(s is None for s in e["restart_side"]))

    def test_warmup_motion_before_kickoff_phase_and_jitter_do_not_release_D(self):
        frames = movement(30) + [dict(x=50 + (.1 if i % 2 else -.1), speeds=(3., 3., 3.)) for i in range(80)]
        e, labels = pipeline(frames, [kickoff(30, 70)])
        self.assertEqual(labels, ["D"] * len(frames))
        self.assertTrue(np.all(e["restart_score"] == 0))

    def test_subsequent_turnover_and_ordinary_stoppage_still_work(self):
        frames = movement(60) + pause(25) + missing(4) + movement(40)
        obs = [observation(i, **f) for i, f in enumerate(frames)]
        for i in range(30, 60):
            for p in obs[i]["players"]:
                p["x_m"] = obs[i]["ball"]["x_m"] + (0 if p["team"] == "A" else 10)
        e, labels = pipeline(frames, [kickoff(0, 20)], reader=iter(obs))
        self.assertEqual(labels[29], "H")
        self.assertEqual(labels[40], "H")
        self.assertEqual(labels[41:60], ["A"] * 19)
        self.assertEqual(labels[84:185], ["D"] * 101)
        self.assertEqual(labels[-1], "H")

    def test_second_half_starts_fresh_with_its_own_kickoff_prior(self):
        first = movement(50)
        second = [dict(x=52.65)] * 40 + movement(30)
        windows = [kickoff(0, 20), kickoff(75, 95)]
        e, labels = pipeline(first + second, windows, [(1, 0, 49), (2, 50, 119)])
        fresh, fresh_labels = pipeline(second, [kickoff(25, 45)])
        self.assertEqual(labels[50:], fresh_labels)
        for field in e:
            np.testing.assert_equal(e[field][50:], fresh[field])
        self.assertEqual(labels[50:90], ["D"] * 40)
        self.assertEqual(labels[-1], "H")

    def test_initial_prior_transport_cannot_be_dropped_or_shifted(self):
        e, _ = pipeline([dict()] * 40, [kickoff(20, 30)])
        e.pop("initial_dead")
        with self.assertRaisesRegex(ValueError, "initial_dead"):
            rp.validate_evidence(e, 40)
        e["initial_dead"] = np.zeros(40, dtype=bool)
        e["initial_dead"][1] = True
        with patch.object(rp, "half_video_blocks", return_value=[(1, 0, 39)]):
            with self.assertRaisesRegex(ValueError, "initial_dead"):
                rp.decode_match(e, 40, games.GAME)

    def test_initial_prior_requires_boolean_aligned_array(self):
        e, _ = pipeline([dict()] * 40, [kickoff(20, 30)])
        for invalid in (np.ones(40, dtype=int), np.zeros((40, 1), dtype=bool),
                        np.zeros(39, dtype=bool), np.array(["False"] * 40)):
            with self.subTest(dtype=invalid.dtype, shape=invalid.shape):
                e["initial_dead"] = invalid
                with self.assertRaises(ValueError):
                    rp.validate_evidence(e, 40)

    def test_real_tag_extractor_preserves_kickoff_type_for_initialization(self):
        events = [dict(code="SET PIECES", start_frame=10, end_frame=30,
                       tags={"Type": "Kick Off (Start)", "Team": "N/A"})]
        e, labels = pipeline([dict(x=52.65)] * 50, restart_windows(events))
        self.assertTrue(e["initial_dead"][0])
        self.assertEqual(labels, ["D"] * 50)

    def test_published_diagnostic_uses_FAQ_inclusive_interval_not_clock_anchor(self):
        # Invented constant-D file, not match labels or inference input.
        text = "frame,label\n" + "".join(f"{i},D\n" for i in range(games.source_frames()))
        with patch("builtins.open", return_value=io.StringIO(text)):
            result = kickoff_check.check("invented.csv")
        self.assertEqual((result["first"], result["last"], result["frames"]), (110808, 113741, 2934))
        self.assertEqual(result["counts"]["D"], 2934)


if __name__ == "__main__":
    unittest.main()
