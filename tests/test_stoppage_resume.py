"""M4 tests for restarts, late returns, weak signals, sparse data and tracking jumps.

Invented plays only. All consumer assertions use actual M1 score_frame and actual
corrected M2 from this checkout. No alternate decoder is used.
"""

import unittest
from unittest.mock import patch

import numpy as np

from module1.control_scores import score_frame
from module4 import evidence as m4
from m2_dependency import load_m2
from test_stoppage_evidence import observation, window

def make(windows=(), config=None, last_frame=2999):
    with patch.object(m4, "half_video_blocks", return_value=((1, 0, last_frame),)):
        return m4.StoppageEvidence(windows, config=config)


def play(producer, frames):
    """frames: list of (x, speeds) or (x, speeds, y). x None = ball missing."""
    rows = []
    for i, f in enumerate(frames):
        x, speeds = f[0], f[1]
        y = f[2] if len(f) > 2 else 34.0
        rows.append(producer(i, observation(i, x=x, y=y, speeds=speeds)))
    return rows


def actual_states(m2, frames, windows=()):
    """Collect actual producer returns; map actual M2 labels to D flags for assertions."""
    rows = play(make(windows), frames)
    for i, frame in enumerate(frames):
        obs = observation(i, x=frame[0], speeds=frame[1], y=frame[2] if len(frame) > 2 else 34.)
        scores = score_frame(obs)
        rows[i].update({name: scores[name] for name in
                        ("score_home", "score_away", "ball_visible", "home_available", "away_available")})
    arrays = {name: np.array([row[name] for row in rows], dtype=object if name == "restart_side" else None)
              for name in rows[0]}
    labels = m2.modulo2(**arrays, half_blocks=[(1, 0, len(rows) - 1)])
    return [label == "D" for label in labels]


STILL = (0, 0, 0)
RUN = (3, 3, 3)


def throw_in(pause_frames=26, missing=0, wait=10, players=STILL):
    """Live ball to the line, stop outside it, (ball missing), reappear, then thrown in."""
    frames = [(12 - 0.8 * i, RUN) for i in range(15)]            # live ball heading to the line
    frames += [(-0.3, STILL)] * pause_frames                     # ball over the line, all quiet
    frames += [(None, STILL)] * missing                          # tracker loses the ball
    frames += [(0.4, STILL)] * wait                              # ball reappears, still
    frames += [(0.4 + 0.8 * k, players) for k in range(1, 16)]   # thrown in, players may stay still
    return frames


class ResumeTests(unittest.TestCase):
    def test_throw_in_with_still_players_gives_restart_evidence(self):
        producer = make()
        rows = play(producer, throw_in(missing=0, wait=0, players=STILL))
        first = 15 + 26
        later = [r["restart_score"] for r in rows[first:]]
        self.assertGreaterEqual(max(later), 0.6)          # ball-only path works
        self.assertEqual(rows[first]["restart_score"], 0)  # but not on the very first frame
        self.assertTrue(all(r["restart_side"] is None for r in rows))

    def test_ball_only_restart_is_not_instant_and_needs_distance(self):
        producer = make()
        frames = [(-0.3, STILL)] * 20
        frames += [(-0.3 + 0.1 * k, STILL) for k in range(1, 12)]   # slow creep, ~2.5 m/s
        rows = play(producer, frames)
        # Creeping ball is fast enough (2.5 m/s) but never 2 m away while still sustained early
        early = [r["restart_score"] for r in rows[20:24]]
        self.assertTrue(all(s == 0 for s in early))

    def test_tag_adds_a_little_to_ball_only_restart(self):
        producer = make([window("H", 0, 400)])
        rows = play(producer, throw_in(wait=0))
        self.assertAlmostEqual(max(r["restart_score"] for r in rows), 0.7)
        self.assertEqual(rows[-1]["restart_side"], "H")

    def test_late_return_after_long_missing_ball(self):
        producer = make()
        rows = play(producer, throw_in(missing=250))     # ball lost about 10 s
        self.assertGreaterEqual(max(r["restart_score"] for r in rows[300:]), 0.6)

    def test_same_half_eligibility_is_not_an_expiring_timeout(self):
        producer = make()
        rows = play(producer, throw_in(missing=1000))    # about 40 s; no age expiry
        self.assertGreaterEqual(max(r["restart_score"] for r in rows[1000:]), 0.6)

    def test_context_is_separate_from_the_short_history(self):
        producer = make()
        frames = throw_in(missing=250, wait=1)[:15 + 26 + 250 + 1]
        play(producer, frames)                           # ball comes back after about 10 s
        self.assertEqual(len(producer.history), 1)       # short history started over ...
        self.assertIsNotNone(producer.context)           # ... but the pause is still remembered

    def test_restart_is_reported_then_forgotten(self):
        producer = make()
        frames = throw_in(wait=0)
        frames += [(15 + 0.5 * k, RUN) for k in range(120)]   # live play afterwards, 4.8 s
        rows = play(producer, frames)
        positives = [i for i, r in enumerate(rows) if r["restart_score"] > 0]
        self.assertGreater(len(positives), 0)
        self.assertLessEqual(positives[-1] - positives[0], 26)   # about 1 s, then consumed
        self.assertIsNone(producer.context)


class WeakSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m2 = load_m2()

    def max_dead(self, frames, windows=()):
        rows = play(make(windows), frames)
        return max(r["dead_score"] for r in rows), actual_states(self.m2, frames, windows)

    def test_slow_play_near_the_line_stays_weak(self):
        # ball 0.2 m inside the line, creeping 0.5 m/s along it, players walking, no tag, 1.6 s
        frames = [(0.2, (1.0, 1.0, 1.0), 20 + 0.02 * i) for i in range(40)]
        top, in_d = self.max_dead(frames)
        self.assertGreater(top, 0)
        self.assertLessEqual(top, 0.30 + 1e-9)
        self.assertFalse(any(in_d))

    def test_long_slow_live_play_near_the_line_stays_weak(self):
        frames = [(0.2, (1.0, 1.0, 1.0), 20 + 0.02 * i) for i in range(75)]   # 3 s
        top, in_d = self.max_dead(frames)
        self.assertLessEqual(top, 0.30)
        self.assertFalse(any(in_d))

    def test_weak_signals_never_enter_d(self):
        cases = {
            "interior stillness, no tag": [(52.65, (0, 0, 0))] * 60,
            "missing ball": [(None, (0, 0, 0))] * 60,
            "two outside samples only": ([(0.2, STILL)] * 10 + [(-0.3, STILL)] * 2
                                         + [(0.2, STILL)] * 30),
            "live fast ball on the line": [(0.1, RUN, 10 + 0.5 * i) for i in range(60)],
        }
        for name, frames in cases.items():
            with self.subTest(name):
                top, in_d = self.max_dead(frames)
                self.assertLess(top, 0.5)
                self.assertFalse(any(in_d))

    def test_tag_with_sustained_collective_pause_can_enter_d(self):
        # Intentionally supersedes the old 0.15 ceiling: this fixture contains
        # tracking corroboration, not a tag alone. Keep missing-ball negatives.
        top, in_d = self.max_dead([(52.65, STILL)] * 60, [window("H", 0, 100)])
        self.assertAlmostEqual(top, .8)
        self.assertFalse(any(in_d[:27]))
        self.assertTrue(all(in_d[27:]))

    def test_tag_alone_and_known_side_alone_never_enter_d(self):
        rows = play(make([window("H", 0, 100)]), [(None, STILL)] * 30)
        self.assertEqual(rows[5]["restart_side"], "H")
        self.assertFalse(any(actual_states(self.m2, [(None, STILL)] * 30, [window("H", 0, 100)])))

    def test_tag_with_ball_near_the_line_counts_as_corroborated(self):
        frames = [(0.2, (1.0, 1.0, 1.0), 20 + 0.02 * i) for i in range(40)]
        top, _ = self.max_dead(frames, [window("A", 0, 100)])
        self.assertGreaterEqual(top, 0.5)

    def test_three_outside_samples_corroborate(self):
        frames = [(0.2, STILL)] * 5 + [(-0.3, STILL)] * 3 + [(0.2, STILL)] * 25
        top, _ = self.max_dead(frames)
        self.assertGreaterEqual(top, 0.5)


class SparseObservationTests(unittest.TestCase):
    def test_too_few_nearby_players_means_unavailable_not_zero_evidence(self):
        producer = make()
        rows = play(producer, [(-0.3, (0, 0))] * 30)
        self.assertTrue(all(not r["dead_available"] and r["dead_score"] == 0 for r in rows))

    def test_ball_only_restart_works_when_players_are_sparse(self):
        producer = make()
        frames = throw_in(wait=0)
        rows = play(producer, frames[:15 + 26])
        later = [producer(len(rows) + k, observation(len(rows) + k, x=0.4 + 0.8 * (k + 1),
                                                     speeds=(0, 0))) for k in range(10)]
        self.assertTrue(any(r["restart_available"] for r in later))
        self.assertGreaterEqual(max(r["restart_score"] for r in later), 0.6)
        self.assertTrue(all(not r["dead_available"] for r in later))

    def test_ball_seen_every_third_frame_abstains(self):
        frames = [(-0.3 if i % 3 == 0 else None, STILL) for i in range(90)]
        rows = play(make(), frames)
        self.assertTrue(all(r["dead_score"] == 0 for r in rows))

    def test_ball_seen_every_sixth_frame_has_no_motion_history(self):
        frames = [(-0.3 if i % 6 == 0 else None, STILL) for i in range(90)]
        rows = play(make(), frames)
        self.assertTrue(all(not r["dead_available"] for r in rows))

    def test_speeds_missing_for_most_players_is_unavailable(self):
        producer = make()
        rows = []
        for i in range(30):
            obs = observation(i, x=-0.3, speeds=(0, 0, 0))
            for p in obs["players"][1:]:
                p["speed_mps"] = None
            rows.append(producer(i, obs))
        self.assertTrue(all(not r["dead_available"] for r in rows))


class TrackingJumpTests(unittest.TestCase):
    def test_one_frame_jump_onto_the_line_is_not_a_stoppage(self):
        frames = [(30 + 0.3 * i, STILL) for i in range(40)]
        frames[20] = (-0.3, STILL)
        producer = make()
        rows = play(producer, frames)
        self.assertTrue(all(r["dead_score"] == 0 for r in rows))
        self.assertIsNone(producer.context)

    def test_jump_away_and_back_after_a_pause_is_not_a_restart(self):
        frames = [(-0.3, STILL)] * 26
        frames += [(40.0, RUN), (-0.3, RUN)]            # tracker teleports away and back
        frames += [(-0.3, RUN)] * 10
        rows = play(make(), frames)
        self.assertTrue(all(r["restart_score"] == 0 for r in rows[26:]))

    def test_jump_starts_fresh_motion_history(self):
        producer = make()
        play(producer, [(30 + 0.3 * i, RUN) for i in range(10)] + [(80.0, RUN)])
        self.assertEqual(len(producer.history), 1)

    def test_jump_does_not_erase_the_long_pause_context(self):
        producer = make()
        play(producer, [(-0.3, STILL)] * 26 + [(40.0, RUN)])
        self.assertIsNotNone(producer.context)


class EnterAndLeaveDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m2 = load_m2()

    def labels(self, frames, windows=()):
        return actual_states(self.m2, frames, windows)

    def test_throw_in_with_late_return_enters_and_leaves_d(self):
        frames = throw_in(missing=250, wait=10, players=STILL)
        d = self.labels(frames)
        first_d = d.index(True)
        self.assertGreaterEqual(first_d, 15)              # not during the live approach
        self.assertLess(first_d, 15 + 26)                 # entered while the ball sat on the line
        self.assertTrue(all(d[first_d:15 + 26 + 250]))    # D survives the missing ball
        self.assertFalse(d[-1])                           # and ends when play is thrown in
        self.assertEqual(sum(1 for a, b in zip(d, d[1:]) if a and not b), 1)

    def test_throw_in_with_active_players_also_leaves_d(self):
        d = self.labels(throw_in(missing=0, wait=0, players=RUN))
        self.assertTrue(any(d))
        self.assertFalse(d[-1])

    def test_live_pass_with_occlusion_never_enters_d(self):
        frames = [(None if 6 <= i <= 8 else 30 + i * 0.3, RUN) for i in range(60)]
        self.assertFalse(any(self.labels(frames, [window("H", 0, 100)])))

    def test_slow_live_play_by_the_line_never_enters_d(self):
        frames = [(0.2, (1.0, 1.0, 1.0), 20 + 0.02 * i) for i in range(40)]
        frames += [(0.2 + 0.4 * k, RUN, 28) for k in range(20)]
        self.assertFalse(any(self.labels(frames)))

    def test_known_side_does_not_by_itself_release_d(self):
        frames = throw_in(missing=0, wait=0)[:15 + 26] + [(None, STILL)] * 100
        d = self.labels(frames, [window("A", 0, 200)])
        self.assertTrue(d[-1])


class ConfigTests(unittest.TestCase):
    def test_new_settings_are_validated(self):
        for values in ({"weak_dead_cap": 0.5}, {"min_out_samples": 2.5},
                       {"restart_ball_displacement_m": 0.5}, {"ball_restart_weight": 0.95},
                       {"max_ball_mps": 0}, {"restart_report_samples": 2.5},
                       {"restart_progress_m": 0}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                m4.EvidenceConfig(**values)


if __name__ == "__main__":
    unittest.main()
