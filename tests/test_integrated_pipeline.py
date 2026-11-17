"""Production M3 -> M1/M4 -> M2 transport and behavioral acceptance.

Invented observations and EPTS files, unchanged production algorithms/defaults.
Compact fixtures change only the timeline; the real-match half contract is also tested.
"""

import copy
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import games
from module4 import evidence as m4
import run_possession as rp
from starter import tactical_tracking
from test_stoppage_m2_gate import observation, pause, missing, movement
from test_tactical_tracking import METADATA


def pipeline(frames, windows=(), blocks=None, *, reader=None):
    n = len(frames)
    blocks = [(1, 0, n - 1)] if blocks is None else blocks
    observations = [observation(i, **f) for i, f in enumerate(frames)]
    with ExitStack() as stack:
        stack.enter_context(patch.object(rp, "source_frames", return_value=n))
        stack.enter_context(patch.object(m4, "half_video_blocks", return_value=blocks))
        stack.enter_context(patch.object(rp, "half_video_blocks", return_value=blocks))
        read = stack.enter_context(patch.object(rp, "iter_tracking_frames",
                                               return_value=reader or iter(observations)))
        evidence = rp.collect_evidence(3., games.GAME, None, windows=windows)
        labels = rp.decode_match(evidence, n, games.GAME)
        read.assert_called_once()
    return evidence, labels


class IntegratedPipelineTests(unittest.TestCase):
    def test_pass_occlusion_brief_deflection_then_sustained_turnover(self):
        frames = [dict(x=30 + .2 * i, speeds=(3., 3., 3.)) for i in range(100)]
        obs = [observation(i, **f) for i, f in enumerate(frames)]
        for i in range(24, 28):
            obs[i]["ball"] = None
        for i in [40] + list(range(65, 100)):
            for p in obs[i]["players"]:
                p["x_m"] = obs[i]["ball"]["x_m"] + (0 if p["team"] == "A" else 10)
        _, labels = pipeline(frames, reader=iter(obs))
        self.assertEqual(labels[:11], ["X"] * 11)
        self.assertEqual(labels[11:76], ["H"] * 65)
        self.assertEqual(labels[76:], ["A"] * 24)

    def test_weak_scores_and_unavailable_teams_do_not_force_a_turnover(self):
        frames = [dict(x=30.)] * 90
        obs = [observation(i, **f) for i, f in enumerate(frames)]
        for i in range(20, 50):
            for p in obs[i]["players"]:
                p["x_m"] = 30 + (59 if p["team"] == "A" else 60)
        for i in range(50, 90):
            obs[i]["players"] = [p for p in obs[i]["players"] if p["team"] == "A"]
            obs[i]["players"][0]["x_m"] = 30
        _, labels = pipeline(frames, reader=iter(obs))
        self.assertEqual(labels[11:], ["H"] * 79)

    def test_supported_stop_persistent_D_delayed_recovery_and_restart_sides(self):
        for seconds in (32, 60, 120):
            for sides, expected in ((("H",), "H"), (("A",), "A"), ((None,), "X"), (("H", "A"), "X")):
                with self.subTest(seconds=seconds, sides=sides):
                    frames = pause() + missing(seconds) + movement(speeds=())
                    windows = [dict(start_frame=0, end_frame=len(frames), side=s) for s in sides]
                    evidence, labels = pipeline(frames, windows)
                    self.assertEqual(labels[24:25 + seconds * 25], ["D"] * (1 + seconds * 25))
                    positive = np.flatnonzero(evidence["restart_score"] >= .5)
                    self.assertGreater(len(positive), 3)
                    confirmed = int(positive[0]) + 2
                    self.assertEqual(labels[confirmed - 1], "D")
                    self.assertEqual(labels[confirmed:], [expected] * (len(labels) - confirmed))
                    self.assertTrue(evidence["restart_available"][confirmed])
                    self.assertFalse(evidence["home_available"][confirmed])

    def test_live_boundary_drift_and_reacquired_jitter_are_not_decisive(self):
        for drift in (0., .02):
            evidence, labels = pipeline([dict(x=.2, y=20 + drift * i, speeds=(1., 1., 1.)) for i in range(750)])
            self.assertLessEqual(max(evidence["dead_score"]), .3)
            self.assertNotIn("D", labels)
        for speeds in ((3., 3., 3.), ()):
            jitter = [dict(x=4 + (.1 if i % 2 else -.1), speeds=speeds) for i in range(150)]
            evidence, labels = pipeline(pause() + missing(4) + jitter)
            self.assertTrue(np.all(evidence["restart_score"] == 0))
            self.assertEqual(labels[-1], "D")

    def test_halves_reset_producer_and_decoder_and_keep_inclusive_last_frame(self):
        frames = pause() + movement(40)
        evidence, labels = pipeline(frames, blocks=[(1, 0, 24), (2, 25, 64)])
        fresh, fresh_labels = pipeline(movement(40))
        self.assertEqual(labels[24], "D")
        self.assertEqual(labels[25:], fresh_labels)
        for key in evidence:
            np.testing.assert_equal(evidence[key][25:], fresh[key])
        self.assertEqual(labels[25], "X")
        self.assertEqual(labels[64], "H")

    def test_native_full_length_half_boundaries(self):
        n = games.source_frames()
        e = {k: np.zeros(n) for k in rp.FLOAT_FIELDS + rp.M4_FLOAT_FIELDS}
        e.update({k: np.ones(n, dtype=bool) for k in rp.BOOL_FIELDS + rp.M4_BOOL_FIELDS})
        e["restart_side"] = np.full(n, None, dtype=object)
        e["initial_dead"] = np.zeros(n, dtype=bool)
        e["score_home"][:] = .8
        e["score_away"][:] = .1
        labels = rp.decode_match(e, n, games.GAME)
        inside = np.zeros(n, dtype=bool)
        for half, first, last in games.half_video_blocks(games.GAME):
            inside[first:last + 1] = True
            self.assertEqual(labels[first:first + 11], ["X"] * 11)
            self.assertEqual(labels[first + 11:last + 1], ["H"] * (last - first - 10))
        self.assertEqual(np.count_nonzero(~inside), 40462)
        self.assertTrue(all(l == "X" for l, mask in zip(labels, inside) if not mask))

    def test_real_M3_EPTS_reader_through_both_producers_decoder_and_writer(self):
        with tempfile.TemporaryDirectory() as folder:
            meta, raw = Path(folder) / "tracking.xml", Path(folder) / "tracking.txt"
            meta.write_text(METADATA, encoding="utf-8")
            # Away at 0.7, home and ball at 0.5. Speeds are raw km/h.
            raw.write_text("".join(f"{i + 1}:0.7,0.5,10.8;0.5,0.5,10.8:0.5,0.5,0\n" for i in range(40)))
            stream = tactical_tracking._iter_frames(meta, raw, 40, 25, (105.3, 68))
            evidence, labels = pipeline([dict()] * 40, blocks=[(1, 2, 35)], reader=stream)
            self.assertEqual(evidence["score_home"].tolist(), [1.] * 40)
            self.assertEqual(labels, ["X"] * 13 + ["H"] * 23 + ["X"] * 4)
            path = Path(folder) / "out.csv"
            rp.write_submission(path, labels)
            self.assertEqual(path.read_bytes(), ("frame,label\n" + "".join(f"{i},{l}\n" for i, l in enumerate(labels))).encode())

    def test_same_recursively_readonly_frame_reaches_actual_producers(self):
        original = observation(0)
        saved = copy.deepcopy(original)
        seen = []
        score = rp.score_frame
        producer = m4.StoppageEvidence.__call__
        def check_m1(obs, tau):
            seen.append(obs)
            with self.assertRaises(TypeError):
                obs["players"][0]["x_m"] = 999
            return score(obs, tau)
        def check_m4(instance, index, obs):
            self.assertIs(obs, seen[-1])
            return producer(instance, index, obs)
        with patch.object(rp, "score_frame", side_effect=check_m1), patch.object(m4.StoppageEvidence, "__call__", check_m4):
            pipeline([dict()], reader=iter([original]))
        self.assertEqual(original, saved)

    def test_dropped_M4_returns_and_index_shift_fail_transport(self):
        with patch.object(m4.StoppageEvidence, "__call__", return_value=None):
            with self.assertRaisesRegex(ValueError, "producer frame"):
                pipeline(pause())
        with self.assertRaisesRegex(RuntimeError, "out of order"):
            pipeline(pause(), reader=iter([observation(i + 1) for i in range(25)]))

    def test_fallback_substitution_fails_supported_stoppage_acceptance(self):
        e, real = pipeline(pause() + missing(4) + movement())
        with patch.object(rp, "half_video_blocks", return_value=[(1, 0, len(real) - 1)]):
            fallback = rp.decode_match(e, len(real), games.GAME, mode="fallback")
        self.assertIn("D", real)
        with self.assertRaises(AssertionError):
            self.assertIn("D", fallback, "integrated gate requires actual stopped state")

    def test_missing_required_module_fails_instead_of_fallback(self):
        import builtins
        real_import = builtins.__import__
        for unavailable in ("modulos", "module4"):
            def missing_import(name, *args, **kwargs):
                if name == unavailable:
                    raise ImportError("required module absent")
                return real_import(name, *args, **kwargs)
            with patch("builtins.__import__", side_effect=missing_import):
                with self.assertRaisesRegex(RuntimeError, "requires corrected"):
                    pipeline(pause())

    def test_all_boundary_types_shapes_and_missingness(self):
        e, _ = pipeline(pause())
        damage = [lambda e: e.pop("restart_score"),
                  lambda e: e.__setitem__("dead_score", np.zeros((25, 1))),
                  lambda e: e.__setitem__("dead_available", np.ones(25, dtype=int)),
                  lambda e: e.__setitem__("score_home", np.array(["0"] * 25)),
                  lambda e: e["d_home"].__setitem__(0, np.nan),
                  lambda e: e["d_home"].__setitem__(0, -1),
                  lambda e: e["restart_score"].__setitem__(0, np.inf),
                  lambda e: e["restart_score"].__setitem__(0, 1.1),
                  lambda e: e["restart_score"].__setitem__(0, .1),
                  lambda e: e["restart_side"].__setitem__(0, "?"),
                  lambda e: e["ball_visible"].__setitem__(0, False)]
        for mutate in damage:
            bad = {k: v.copy() for k, v in e.items()}
            mutate(bad)
            with self.assertRaises(ValueError):
                rp.validate_evidence(bad, 25)
        bad = {k: v.copy() for k, v in e.items()}
        bad["home_available"][0] = False
        bad["score_home"][0] = 0
        with self.assertRaisesRegex(ValueError, "NaN when unavailable"):
            rp.validate_evidence(bad, 25)
        for value in (True, "0.1", complex(.1), np.nan):
            row = rp.score_frame(observation(0))
            row["score_home"] = value
            with patch.object(rp, "score_frame", return_value=row):
                with self.assertRaises(ValueError):
                    pipeline([dict()])


if __name__ == "__main__":
    unittest.main()
