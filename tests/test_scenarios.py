"""Football scenarios M5 must be able to catch, as label sequences scored by the official scorer.

These run TODAY against synthetic label sequences, so they prove the scorer and the release
checks notice each failure. They do NOT prove M2/M4 behave: that acceptance is the blocked gate
'scenarios_with_real_M2_M4' in release_gates.json, and approval stays blocked until it passes.

Cases: pass/deflection, persistent D, late restart / unknown side, reset at half-time.
"""

import os
import sys
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (os.path.join(ROOT, "evaluation"), ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import possession_metrics as pm  # noqa: E402


def codes(text):
    return pm.label_codes(list(text.replace(" ", "")))


def spells(array):
    return pm.possession_spells(array, pm.valid_runs(array))


class PassAndDeflectionTests(unittest.TestCase):
    def test_pass_between_teammates_is_one_possession(self):
        truth = codes("H" * 60)
        self.assertEqual(len(spells(truth)), 1)

    def test_deflection_misread_as_opponent_possession_is_caught(self):
        # the ball is deflected off an away player's shin but stays with home
        truth = codes("H" * 60)
        pred = codes("H" * 28 + "A" * 3 + "H" * 29)
        result = pm.evaluate(truth, pred)
        self.assertEqual(result["spell_count_error"], 2)
        self.assertGreater(result["fragmentation"], 1.0)

    def test_real_interception_missed_is_caught(self):
        truth = codes("H" * 40 + "A" * 40 + "H" * 40)
        pred = codes("H" * 120)
        result = pm.evaluate(truth, pred)
        self.assertEqual(result["n_gt_spells"], 3)
        self.assertEqual(result["n_pred_spells"], 1)
        self.assertEqual(result["transitions"][12]["n_missed"], 2)
        self.assertLess(result["spell_f1_mean"], 1.0)

    def test_interception_detected_late_shows_as_latency(self):
        truth = codes("H" * 40 + "A" * 40)
        pred = codes("H" * 45 + "A" * 35)
        self.assertEqual(pm.evaluate(truth, pred)["transitions"][12]["mean_latency"], 5.0)

    def test_interception_credited_to_wrong_team_is_not_a_match(self):
        truth = codes("H" * 40 + "A" * 40)
        pred = codes("H" * 40 + "D" * 40)
        result = pm.evaluate(truth, pred)
        self.assertEqual(result["transitions"][12]["n_matched"], 0)


class PersistentDeadBallTests(unittest.TestCase):
    truth = codes("H" * 40 + "D" * 200 + "A" * 40)

    def test_correct_persistent_d_creates_no_possession(self):
        result = pm.evaluate(self.truth, self.truth.copy())
        self.assertEqual(result["n_pred_spells"], 2)
        self.assertEqual(result["alive_dead_f1"], 1.0)
        self.assertEqual(result["per_class"]["D"]["recall"], 1.0)

    def test_d_that_decays_into_a_team_label_is_caught(self):
        pred = codes("H" * 40 + "D" * 100 + "H" * 100 + "A" * 40)
        result = pm.evaluate(self.truth, pred)
        self.assertEqual(result["per_class"]["D"]["recall"], 0.5)
        self.assertGreater(result["n_pred_spells"], 2)

    def test_flicker_inside_d_invents_possessions(self):
        pred = self.truth.copy()
        pred[100:103] = pm.H
        pred[150:153] = pm.A
        result = pm.evaluate(self.truth, pred)
        self.assertEqual(result["spell_count_error"], 2)

    def test_always_alive_misses_the_whole_stoppage(self):
        pred = codes("H" * 40 + "H" * 200 + "A" * 40)
        self.assertEqual(pm.evaluate(self.truth, pred)["per_class"]["D"]["recall"], 0.0)


class LateRestartUnknownSideTests(unittest.TestCase):
    truth = codes("D" * 50 + "H" * 50)

    def test_restart_detected_late_is_a_latency_not_a_miss(self):
        pred = codes("D" * 50 + "X" * 10 + "H" * 40)
        result = pm.evaluate(self.truth, pred)
        self.assertEqual(result["transitions"][12]["mean_latency"], 10.0)
        self.assertEqual(result["n_abstain_on_graded"], 10)

    def test_restart_later_than_tolerance_is_missed_and_spurious(self):
        pred = codes("D" * 50 + "X" * 30 + "H" * 20)
        transition = pm.evaluate(self.truth, pred)["transitions"][12]
        self.assertEqual((transition["n_matched"], transition["n_missed"], transition["n_spurious"]),
                         (0, 1, 1))

    def test_unknown_side_as_x_invents_no_possession(self):
        pred = codes("D" * 50 + "X" * 50)
        result = pm.evaluate(self.truth, pred)
        self.assertEqual(result["n_pred_spells"], 0)
        self.assertEqual(result["n_abstain_on_graded"], 50)

    def test_guessing_the_side_invents_a_possession_x_does_not(self):
        guess = codes("D" * 50 + "A" * 50)
        abstain = codes("D" * 50 + "X" * 50)
        self.assertEqual(pm.evaluate(self.truth, guess)["n_pred_spells"], 1)
        self.assertEqual(pm.evaluate(self.truth, abstain)["n_pred_spells"], 0)
        self.assertEqual(pm.evaluate(self.truth, guess)["spell_f1_mean"], 0.0)

    def test_abstaining_is_charged_at_frame_level(self):
        abstain = pm.evaluate(self.truth, codes("D" * 50 + "X" * 50))
        self.assertLess(abstain["accuracy"], 1.0)
        self.assertEqual(abstain["per_class"]["H"]["recall"], 0.0)


class HalfTimeResetTests(unittest.TestCase):
    # X(5) | H20 D10 | X(5) | D10 A20 | X(3)  -> halves [5,35) and [40,70)
    truth = codes("X" * 5 + "H" * 20 + "D" * 10 + "X" * 5 + "D" * 10 + "A" * 20 + "X" * 3)

    def test_two_runs_found(self):
        self.assertEqual(pm.valid_runs(self.truth), [(5, 35), (40, 70)])

    def test_d_at_both_sides_of_half_time_is_two_segments_not_one(self):
        runs = pm.valid_runs(self.truth)
        dead = [s for s in pm.segments(self.truth, runs) if s[2] == pm.D]
        self.assertEqual(len(dead), 2)

    def test_no_transition_is_invented_across_half_time(self):
        runs = pm.valid_runs(self.truth)
        for frame, _, _ in pm.transitions(self.truth, runs):
            self.assertFalse(35 <= frame < 40, frame)

    def test_state_does_not_leak_into_second_half(self):
        pred = self.truth.copy()
        pred[40:45] = pm.X                       # model goes quiet at the second-half kickoff
        filled = pm.fill_abstentions(pred, pm.valid_runs(self.truth))
        # back-filled from the second half's own first known label (D), never from half 1's end
        self.assertTrue(np.all(filled[40:45] == pm.D))

    def test_possession_cannot_straddle_the_break(self):
        truth = codes("X" * 2 + "H" * 10 + "X" * 4 + "H" * 10 + "X" * 2)
        self.assertEqual(len(spells(truth)), 2)
        result = pm.evaluate(truth, truth.copy())
        self.assertEqual(result["n_pred_spells"], 2)
        self.assertEqual(result["spell_f1_mean"], 1.0)

    def test_x_outside_the_halves_is_not_graded_or_charged(self):
        pred = self.truth.copy()
        pred[0:5] = pm.H
        result = pm.evaluate(self.truth, pred)
        self.assertEqual(result["n_abstain_on_graded"], 0)
        self.assertEqual(result["macro_f1"], 1.0)


if __name__ == "__main__":
    unittest.main()
