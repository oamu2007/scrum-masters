"""Module 5 checks: would we notice a bad label file?

Everything here is measured with the organizers' own code (evaluation/possession_metrics.py and
evaluation/validate_submission.py), never with a copy of it, so "caught" means "caught by the
scorer that will grade us". The public ground truth is used only to check the pipeline's format
and alignment, never to tune anything.

Run:  python -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(ROOT, "evaluation")
for path in (EVAL, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import possession_metrics as pm  # noqa: E402
from games import GAME, GAMES, half_video_blocks  # noqa: E402

N = GAMES[GAME]["n_video_frames"]
VALIDATOR = os.path.join(EVAL, "validate_submission.py")
RESULTS = os.path.join(EVAL, "results")
GT_CSV = os.path.join(EVAL, "gt", "BAR-ATH_possession_gt_public.csv")


def codes(text):
    """'HHAD X' style text -> label codes (spaces ignored)."""
    return pm.label_codes(list(text.replace(" ", "")))


def table(frames, labels):
    return pd.DataFrame({"frame": frames, "label": labels})


def good_table(n):
    return table(np.arange(n), ["H"] * n)


def shift_late(array, k=1):
    """The same labels, k frames later: what an off-by-k indexing bug produces."""
    return np.concatenate((np.full(k, array[0], dtype=array.dtype), array[:-k]))


def shift_early(array, k=1):
    return np.concatenate((array[k:], np.full(k, array[-1], dtype=array.dtype)))


def match_with_two_handovers():
    """Truth: H 40, A 40, H 40 -- two real changes of possession."""
    return codes("H" * 40 + "A" * 40 + "H" * 40)


class InventedPossessionTests(unittest.TestCase):
    """The spec's example: H H H H H vs H H A H H."""

    gt = codes("HHHHH")
    pred = codes("HHAHH")

    def test_exactly_one_frame_differs(self):
        self.assertEqual(int(np.sum(self.gt != self.pred)), 1)

    def test_one_possession_becomes_three(self):
        runs = pm.valid_runs(self.gt)
        self.assertEqual(len(pm.possession_spells(self.gt, runs)), 1)
        self.assertEqual(len(pm.possession_spells(self.pred, runs)), 3)

    def test_scorer_reports_the_invented_possessions(self):
        result = pm.evaluate(self.gt, self.pred)
        self.assertEqual(result["n_gt_spells"], 1)
        self.assertEqual(result["n_pred_spells"], 3)
        self.assertEqual(result["spell_count_error"], 2)
        self.assertGreater(result["fragmentation"], 1.0)
        self.assertLess(result["spell_f1_mean"], 1.0)

    def test_identical_labels_are_clean(self):
        result = pm.evaluate(self.gt, self.gt.copy())
        self.assertEqual(result["spell_count_error"], 0)
        self.assertEqual(result["spell_f1_mean"], 1.0)
        self.assertEqual(result["fragmentation"], 1.0)

    def test_false_change_inside_a_real_handover(self):
        gt = match_with_two_handovers()
        pred = gt.copy()
        pred[20] = pm.A                       # one frame of "away" in the middle of home's spell
        result = pm.evaluate(gt, pred)
        self.assertEqual(result["n_gt_spells"], 3)
        self.assertEqual(result["n_pred_spells"], 5)
        self.assertGreater(result["fragmentation"], 1.0)

    def test_abstention_inside_a_possession_is_not_a_new_possession(self):
        gt = codes("H" * 30)
        pred = gt.copy()
        pred[10:13] = pm.X
        result = pm.evaluate(gt, pred)
        self.assertEqual(result["n_pred_spells"], 1)
        self.assertEqual(result["n_abstain_on_graded"], 3)

    def test_abstention_across_a_handover_delays_the_change(self):
        gt = codes("H" * 30 + "A" * 30)
        pred = codes("H" * 30 + "X" * 5 + "A" * 25)
        latency = pm.evaluate(gt, pred)["transitions"][12]["mean_latency"]
        self.assertEqual(latency, 5.0)


class IndexingShiftTests(unittest.TestCase):
    """A one-frame shift is invisible to possession counts and visible only in latency."""

    def setUp(self):
        self.gt = match_with_two_handovers()

    def test_aligned_has_zero_latency(self):
        result = pm.evaluate(self.gt, self.gt.copy())
        self.assertEqual(result["transitions"][12]["mean_latency"], 0.0)

    def test_one_frame_late_is_caught(self):
        pred = shift_late(self.gt)
        result = pm.evaluate(self.gt, pred)
        self.assertEqual(result["transitions"][12]["mean_latency"], 1.0)
        self.assertEqual(result["transitions"][12]["n_matched"], 2)

    def test_one_frame_early_is_caught(self):
        pred = shift_early(self.gt)
        result = pm.evaluate(self.gt, pred)
        self.assertEqual(result["transitions"][12]["mean_latency"], -1.0)

    def test_shift_does_not_change_possession_count(self):
        # which is exactly why the latency check above is the one that matters
        result = pm.evaluate(self.gt, shift_late(self.gt))
        self.assertEqual(result["spell_count_error"], 0)
        self.assertGreater(result["spell_f1_mean"], 0.99)

    def test_frames_differing_equal_label_changes_times_shift(self):
        pred = shift_late(self.gt)
        n_changes = int(np.sum(self.gt[1:] != self.gt[:-1]))
        self.assertEqual(int(np.sum(pred != self.gt)), n_changes)

    def test_bigger_shift_is_proportionally_bigger(self):
        result = pm.evaluate(self.gt, shift_late(self.gt, 5))
        self.assertEqual(result["transitions"][12]["mean_latency"], 5.0)


class FormatRejectionTests(unittest.TestCase):
    """What the official validator refuses, tested with the official function."""

    n = 50

    def reason(self, frame_table, n=None):
        return pm.validate_submission(frame_table, n or self.n)

    def test_a_correct_table_passes(self):
        self.assertIsNone(self.reason(good_table(self.n)))

    def test_frame_column_starting_at_one(self):
        self.assertIn("frame", self.reason(table(np.arange(1, self.n + 1), ["H"] * self.n)))

    def test_skipped_frame(self):
        frames = np.arange(self.n)
        frames[25:] += 1
        self.assertIsNotNone(self.reason(table(frames, ["H"] * self.n)))

    def test_duplicate_frame(self):
        frames = np.arange(self.n)
        frames[10] = 9
        self.assertIsNotNone(self.reason(table(frames, ["H"] * self.n)))

    def test_reversed_order(self):
        self.assertIsNotNone(self.reason(table(np.arange(self.n)[::-1], ["H"] * self.n)))

    def test_float_frame_column(self):
        self.assertIn("integer", self.reason(table(np.arange(self.n) * 1.0, ["H"] * self.n)))

    def test_one_row_short_and_one_row_long(self):
        self.assertIn("row count", self.reason(good_table(self.n - 1)))
        self.assertIn("row count", self.reason(good_table(self.n + 1)))

    def test_blank_label(self):
        labels = ["H"] * self.n
        labels[7] = None
        self.assertIn("empty label", self.reason(table(np.arange(self.n), labels)))

    def test_illegal_label(self):
        labels = ["H"] * self.n
        labels[3] = "Z"
        self.assertIn("labels outside", self.reason(table(np.arange(self.n), labels)))

    def test_lowercase_is_tolerated_like_the_scorer_does(self):
        self.assertIsNone(self.reason(table(np.arange(self.n), ["h"] * self.n)))

    def test_atd_frame_ids_are_rejected_at_full_length(self):
        # ATD frame_id runs 1..N; the submission wants the video frame 0..N-1
        atd_style = table(np.arange(1, N + 1), ["H"] * N)
        self.assertIn("not 0..", self.reason(atd_style, N))


class ValidatorCommandTests(unittest.TestCase):
    """The same checks, through the command the team will actually type."""

    def run_validator(self, text, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sub.csv")
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            return subprocess.run(
                [sys.executable, VALIDATOR, path, "--rows", str(rows)],
                capture_output=True, text=True)

    def test_valid_file_exits_zero(self):
        text = "frame,label\n" + "".join("{},H\n".format(i) for i in range(10))
        done = self.run_validator(text, 10)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("OK", done.stdout)

    def test_wrong_row_count_exits_one(self):
        text = "frame,label\n" + "".join("{},H\n".format(i) for i in range(9))
        done = self.run_validator(text, 10)
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAIL", done.stdout)

    def test_frame_starting_at_one_exits_one(self):
        text = "frame,label\n" + "".join("{},H\n".format(i) for i in range(1, 11))
        self.assertEqual(self.run_validator(text, 10).returncode, 1)

    def test_missing_header_exits_one(self):
        text = "".join("{},H\n".format(i) for i in range(10))
        self.assertEqual(self.run_validator(text, 10).returncode, 1)

    def test_missing_file_exits_one(self):
        done = subprocess.run([sys.executable, VALIDATOR, os.path.join(ROOT, "no_such.csv")],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("no such file", done.stdout)


def _have(*paths):
    return all(os.path.isfile(p) for p in paths)


BASELINES = [os.path.join(RESULTS, "baseline_{}.csv".format(n))
             for n in ("raw", "smooth25", "smooth50", "smooth125")]


@unittest.skipUnless(_have(*BASELINES), "baseline CSVs not found")
class BaselineFileTests(unittest.TestCase):
    """The organizers' baselines: full-size files the official validator must accept."""

    def test_all_four_baselines_pass_at_full_length(self):
        for path in BASELINES:
            frame = pm.read_label_csv(path)
            self.assertIsNone(pm.validate_submission(frame, N), os.path.basename(path))

    def test_validator_command_accepts_smooth50(self):
        done = subprocess.run(
            [sys.executable, VALIDATOR, os.path.join(RESULTS, "baseline_smooth50.csv")],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("199319 rows", done.stdout)

    def test_more_smoothing_means_fewer_possessions(self):
        runs = [(a, b + 1) for _, a, b in half_video_blocks(GAME)]
        counts = []
        for path in BASELINES:
            frame_codes = pm.label_codes(pm.read_label_csv(path))
            counts.append(len(pm.possession_spells(frame_codes, runs)))
        self.assertEqual(counts, sorted(counts, reverse=True), counts)

    def test_shifted_baseline_is_detected_by_latency(self):
        reference = pm.label_codes(pm.read_label_csv(BASELINES[2]))
        blocks = half_video_blocks(GAME)
        keep = np.zeros(N, dtype=bool)
        for _, a, b in blocks:
            keep[a:b + 1] = True
        gt_like = np.where(keep, reference, pm.X).astype(np.int8)
        shifted = np.where(keep, shift_late(reference), pm.X).astype(np.int8)
        aligned = pm.evaluate(gt_like, gt_like.copy())["transitions"][12]
        late = pm.evaluate(gt_like, shifted)["transitions"][12]
        self.assertEqual(aligned["median_latency"], 0.0)
        self.assertEqual(late["median_latency"], 1.0)


@unittest.skipUnless(_have(GT_CSV), "public ground truth not found")
class PublicGroundTruthShapeTests(unittest.TestCase):
    """Format and alignment facts only. The public labels are never used to tune anything."""

    def test_public_window_matches_the_first_half_start(self):
        gt = pm.label_codes(pm.read_label_csv(GT_CSV))
        self.assertIsNone(pm.validate_submission(pm.read_label_csv(GT_CSV), N))
        first_start = half_video_blocks(GAME)[0][1]
        self.assertEqual(pm.valid_runs(gt), [(first_start, first_start + 7500)])

    def test_public_label_counts_match_the_meta_file(self):
        gt = pm.label_codes(pm.read_label_csv(GT_CSV))
        self.assertEqual(int(np.sum(gt == pm.H)), 3454)
        self.assertEqual(int(np.sum(gt == pm.A)), 2577)
        self.assertEqual(int(np.sum(gt == pm.D)), 1469)


if __name__ == "__main__":
    unittest.main()
