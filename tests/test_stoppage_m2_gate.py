"""Required actual M4 -> actual M1 scores -> corrected actual M2 acceptance gate.

Set MTAH_M2_ROOT explicitly. Missing/wrong dependencies are errors, never skips.
All observations are invented; no TinyDecoder or duplicated transition logic.
"""

import copy
import math
import unittest
from unittest.mock import patch

import numpy as np

from games import GAME, GAMES, half_video_blocks
from module1.control_scores import score_frame
from module4 import evidence as m4
from m2_dependency import load_m2


START = half_video_blocks(GAME)[0][1]
FPS = GAMES[GAME]["fps"]
M1_FIELDS = ("score_home", "score_away", "ball_visible", "home_available", "away_available")
M4_FIELDS = ("dead_score", "dead_available", "restart_score", "restart_available", "restart_side")


def pause(n=25):
    return [dict(x=-.3)] * n


def missing(seconds):
    return [dict(x=None)] * round(seconds * FPS)


def movement(n=30, speeds=(3., 3., 3.)):
    return [dict(x=2 + .5 * k, speeds=speeds) for k in range(n)]


def observation(index, x=10., y=34., speeds=(0., 0., 0.), positions=True):
    ball = None if x is None else dict(x_m=x, y_m=y)
    players = [dict(team="A" if j == 1 else "H", track_slot=j + 1, observed=True,
                    x_m=(x if x is not None else 10.) + (10. if j == 1 else 0.),
                    y_m=y, speed_mps=speed) for j, speed in enumerate(speeds)]
    if not positions:
        for player in players:
            player.update(observed=False, x_m=None, y_m=None)
    return dict(frame=index, time_s=index / FPS, ball=ball, players=players)


class ActualM2Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m2 = load_m2()

    def run_case(self, frames, windows=(), *, start=START, halves=None):
        if halves is None:
            producer = m4.StoppageEvidence(windows)
        else:
            # Explicit compact adjacent-half fixture; production still uses games.py.
            with patch.object(m4, "half_video_blocks", return_value=halves):
                producer = m4.StoppageEvidence(windows)
        rows = []
        for k, frame in enumerate(frames):
            obs = observation(start + k, **frame)
            saved = copy.deepcopy(obs)
            result = producer(start + k, obs)
            scores = score_frame(obs)
            self.assertEqual(obs, saved)
            self.assertEqual(set(result), set(M4_FIELDS))
            for prefix in ("dead", "restart"):
                score, available = result[prefix + "_score"], result[prefix + "_available"]
                self.assertIs(type(available), bool)
                self.assertTrue(math.isfinite(score) and 0 <= score <= 1)
                if not available:
                    self.assertEqual(score, 0)
            self.assertIn(result["restart_side"], ("H", "A", None))
            rows.append(dict(result, **{name: scores[name] for name in M1_FIELDS}))
        arrays = {name: np.array([row[name] for row in rows], dtype=object if name == "restart_side" else None)
                  for name in M1_FIELDS + M4_FIELDS}
        # Rebase native triples to the compact array axis; M4 receives native frame IDs.
        blocks = [(half, max(first, start) - start, min(last, start + len(rows) - 1) - start)
                  for half, first, last in producer.halves if last >= start and first < start + len(rows)]
        labels = self.m2.modulo2(**arrays, half_blocks=blocks)
        self.assertEqual(len(labels), len(rows))
        self.assertTrue(set(labels) <= set("HADX"))
        return rows, labels, producer

    def assert_recovered(self, rows, labels, final="H"):
        threshold = self.m2.CONFIG_M2.restart_min_score
        positives = [i for i, row in enumerate(rows) if row["restart_score"] >= threshold]
        self.assertTrue(positives, "supported resumption emitted no decisive restart evidence")
        first = positives[0]
        count = self.m2.CONFIG_M2.restart_confirm_frames
        self.assertTrue(all(row["restart_available"] and row["restart_score"] >= threshold
                            for row in rows[first:first + count]))
        self.assertEqual(labels[first - 1], "D")
        self.assertNotEqual(labels[first + count - 1], "D")
        self.assertEqual(sum(a == "D" and b != "D" for a, b in zip(labels, labels[1:])), 1)
        self.assertEqual(labels[-1], final)

    def test_long_gap_supported_returns_with_active_stationary_sparse_and_absent_players(self):
        for seconds in (32, 60, 120):
            for speeds in ((3., 3., 3.), (0., 0., 0.), (0., 0.), (), (None, None, None)):
                with self.subTest(seconds=seconds, speeds=speeds):
                    rows, labels, producer = self.run_case(pause() + missing(seconds) + movement(speeds=speeds))
                    self.assert_recovered(rows, labels, "X" if not speeds else "H")
                    self.assertTrue(all(row["restart_score"] == 0 for row in rows[25:25 + round(seconds * FPS)]))
                    self.assertLessEqual(len(producer.history), math.ceil(m4.EvidenceConfig().motion_window_s * FPS) + 2)

    def test_prolonged_live_drift_and_stationary_hold_never_create_default_D(self):
        for n in (75, 250, 750):
            for drift in (0., .02):  # 0 or 0.5 m/s, always 0.2 m inside the line
                with self.subTest(n=n, drift=drift):
                    frames = [dict(x=.2, y=20 + drift * k, speeds=(1., 1., 1.)) for k in range(n)]
                    rows, labels, producer = self.run_case(frames)
                    self.assertLess(max(row["dead_score"] for row in rows), self.m2.CONFIG_M2.dead_min_score)
                    self.assertNotIn("D", labels)
                    self.assertIsNone(producer.context)

    def test_reacquired_local_jitter_does_not_resume_play(self):
        for n in (30, 150):
            for speeds in ((0., 0., 0.), (3., 3., 3.)):
                with self.subTest(n=n, speeds=speeds):
                    jitter = [dict(x=4 + (.1 if k % 2 else -.1), speeds=speeds) for k in range(n)]
                    rows, labels, _ = self.run_case(pause() + missing(4) + jitter)
                    self.assertTrue(all(row["restart_score"] == 0 for row in rows))
                    self.assertEqual(labels[-1], "D")

    def test_supported_outside_stop_and_restart_controls(self):
        for speeds in ((3., 3., 3.), (0., 0., 0.), (0., 0.), ()):
            rows, labels, _ = self.run_case(pause() + movement(speeds=speeds))
            self.assertGreaterEqual(max(row["dead_score"] for row in rows), .5)
            self.assert_recovered(rows, labels, "X" if not speeds else "H")

    def test_missing_stationary_or_intermittent_return_keeps_D(self):
        for returned in ([dict(x=4.)] * 100,
                         [dict(x=None)] * 100,
                         [dict(x=2 + .2 * k, speeds=(0., 0.)) if k % 2 == 0 else dict(x=None)
                          for k in range(100)]):
            rows, labels, _ = self.run_case(pause() + missing(120) + returned)
            self.assertTrue(all(row["restart_score"] == 0 for row in rows))
            self.assertEqual(labels[-1], "D")

    def test_outside_slow_retrieval_and_jump_return_negatives(self):
        for returned in ([dict(x=-.3 - .2 * k) for k in range(60)],
                         [dict(x=-.3 + .04 * k) for k in range(80)],
                         [dict(x=40.), dict(x=-.3)] + pause(20)):
            rows, labels, _ = self.run_case(pause() + returned)
            self.assertTrue(all(row["restart_score"] == 0 for row in rows))
            self.assertEqual(labels[-1], "D")

    def test_known_unknown_conflicting_sides_and_half_open_endpoints(self):
        for sides in (("H",), ("A",), (None,), ("H", "A"), ("H", None)):
            windows = [dict(start_frame=START, end_frame=START + 100, side=side) for side in sides]
            rows, labels, _ = self.run_case(pause() + movement(), windows)
            first = next(i for i, row in enumerate(rows) if row["restart_score"] >= .5)
            confirmed = first + self.m2.CONFIG_M2.restart_confirm_frames - 1
            expected = sides[0] if len(sides) == 1 and sides[0] is not None else "X"
            self.assertEqual(labels[confirmed], expected)
            if expected == "X":
                self.assertTrue(all(row["restart_side"] is None for row in rows))
        windows = [dict(start_frame=START, end_frame=START + 25, side="A")]
        rows, labels, _ = self.run_case(pause() + missing(120), windows)
        self.assertEqual(rows[24]["restart_side"], "A")
        self.assertIsNone(rows[25]["restart_side"])
        self.assertEqual(labels[-1], "D")
        self.assertTrue(all(row["restart_score"] == 0 for row in rows))

    def test_context_consumed_without_later_unsupported_restarts(self):
        frames = pause() + movement(40) + missing(120) + movement(40, speeds=(0., 0.))
        rows, labels, producer = self.run_case(frames)
        self.assert_recovered(rows, labels)
        self.assertTrue(all(row["restart_score"] == 0 for row in rows[65:]))
        self.assertIsNone(producer.context)

    def test_qualified_context_consumption_happens_even_during_missing_ball(self):
        # Three supported samples qualify a report; disappearance must not defer
        # retirement until another positive observation minutes later.
        frames = pause() + movement(5) + missing(120) + movement(40)
        rows, labels, producer = self.run_case(frames)
        self.assert_recovered(rows, labels)
        self.assertTrue(all(row["restart_score"] == 0 for row in rows[30:]))
        self.assertIsNone(producer.context)

    def test_interrupted_subconfirmation_pulse_does_not_spend_recovery_eligibility(self):
        frames = pause() + movement(1) + missing(120) + movement(40)
        rows, labels, _ = self.run_case(frames)
        self.assertEqual(labels[25], "D")  # only one positive, not three
        self.assertTrue(all(label == "D" for label in labels[25:26 + 120 * FPS]))
        later = rows[26 + 120 * FPS:]
        self.assertGreaterEqual(sum(row["restart_score"] >= .5 for row in later), 3)
        self.assertEqual(labels[-1], "H")
        self.assertEqual(sum(a == "D" and b != "D" for a, b in zip(labels, labels[1:])), 1)

    def test_ball_only_restart_with_missing_positions_has_independent_availability(self):
        returned = [dict(x=2 + .5 * k, positions=False) for k in range(30)]
        rows, labels, _ = self.run_case(pause() + missing(60) + returned)
        self.assert_recovered(rows, labels, "X")
        strong = [row for row in rows if row["restart_score"] >= .5]
        self.assertTrue(all(row["restart_available"] and not row["dead_available"]
                            and not row["home_available"] and not row["away_available"] for row in strong))

    def test_faster_inpitch_retrieval_is_an_explicit_observational_ambiguity(self):
        # A 3 m/s retrieval is observationally indistinguishable from some real
        # restarts under the accepted ball-only path. Record, do not hide, this limit.
        frames = pause() + [dict(x=-.3 + .12 * k) for k in range(1, 46)] + [dict(x=5.1)] * 25
        rows, labels, _ = self.run_case(frames)
        self.assertGreaterEqual(max(row["restart_score"] for row in rows), .6)
        self.assertEqual(sum(a == "D" and b != "D" for a, b in zip(labels, labels[1:])), 1)

    def test_half_boundaries_reset_eligibility_and_actual_decoder(self):
        native = half_video_blocks(GAME)
        for start, halves, gap in ((START, [(1, START, START + 24), (2, START + 25, START + 64)], 0),
                                  (native[0][2] - 24, None, native[1][1] - native[0][2] - 1)):
            rows, labels, producer = self.run_case(pause() + [dict(x=None)] * gap + movement(40),
                                                   start=start, halves=halves)
            second = 25 + gap
            fresh, fresh_labels, _ = self.run_case(movement(40), start=start + second, halves=halves)
            self.assertEqual(rows[second:], fresh)
            self.assertEqual(labels[second:], fresh_labels)
            self.assertEqual(labels[second], "X")
            self.assertTrue(all(row["restart_score"] == 0 for row in rows[second:]))
            self.assertTrue(all(label == "X" for label in labels[25:second]))
            self.assertIsNone(producer.context)


if __name__ == "__main__":
    unittest.main()
