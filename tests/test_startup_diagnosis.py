"""Invented startup timing, safeguards, and explicitly unresolved semantics.

These exercise actual M1/M4 -> runner -> M2. A limitation test passing records
current incorrect football semantics; it is NOT a correctness/approval gate.
No supplied match labels, observations or timestamps are used.
"""
import unittest

import numpy as np

from test_integrated_pipeline import pipeline
from test_kickoff_pipeline import kickoff
from test_stoppage_m2_gate import missing, movement, pause


def moving(n=35, *, start=40., speeds=(3., 3., 3.)):
    return [dict(x=start + .5 * i, speeds=speeds) for i in range(n)]


def first_report(evidence):
    return int(np.flatnonzero(evidence['restart_score'] >= .5)[0])


class StartupSafeguards(unittest.TestCase):
    def test_half_begins_before_kickoff_and_tag_spans_dead_and_live(self):
        frames = [dict(x=40.)] * 50 + moving(start=40.5)
        evidence, labels = pipeline(frames, [kickoff(20, 70)])
        report = first_report(evidence)
        self.assertGreaterEqual(report, 50)
        self.assertEqual(labels[:report + 2], ['D'] * (report + 2))
        self.assertEqual(labels[report + 2], 'X')
        self.assertEqual(labels[-1], 'H')

    def test_approximate_endpoints_do_not_estimate_kickoff(self):
        frames = [dict(x=40.)] * 40 + moving(start=40.5)
        early, early_labels = pipeline(frames, [kickoff(5, 30)])
        spanning, spanning_labels = pipeline(frames, [kickoff(10, 60)])
        self.assertEqual(first_report(early), first_report(spanning))
        self.assertEqual(early_labels, spanning_labels)
        self.assertEqual(early_labels[:40], ['D'] * 40)
        self.assertEqual(early_labels[-1], 'H')

    def test_missing_initial_observations_are_not_backfilled_as_live(self):
        frames = [dict(x=None)] * 7 + moving(speeds=(0., 0., 0.))
        evidence, labels = pipeline(frames, [kickoff(-5, 60)])
        self.assertFalse(np.any(evidence['restart_available'][:7]))
        self.assertEqual(first_report(evidence), 16)
        self.assertEqual(labels[:18], ['D'] * 18)
        self.assertEqual(labels[18:29], ['X'] * 11)
        self.assertEqual(labels[29:], ['H'] * (len(frames) - 29))

    def test_interrupted_confirmation_does_not_backdate_or_release_D(self):
        frames = moving(4) + [dict(x=None)] * 8 + moving(start=44.)
        evidence, labels = pipeline(frames, [kickoff(-5, 60, 'A')])
        self.assertTrue(np.all(evidence['restart_score'][2:4] >= .5))
        self.assertEqual(labels[:12], ['D'] * 12)
        self.assertEqual(labels[16], 'A')  # fresh baseline at 14, confirmation at 16
        self.assertEqual(labels[-1], 'H')

    def test_handling_negatives_do_not_release_initial_D(self):
        cases = {
            'bounded_jitter': [dict(x=40 + (.1 if i % 2 else -.1), speeds=(3.,) * 3) for i in range(100)],
            'slow_retrieval': [dict(x=40 + .04 * i) for i in range(100)],
            'outside_retrieval': [dict(x=-1 - .2 * i) for i in range(100)],
        }
        for name, frames in cases.items():
            with self.subTest(case=name):
                evidence, labels = pipeline(frames, [kickoff(0, 50)])
                self.assertFalse(np.any(evidence['restart_score']))
                self.assertEqual(labels, ['D'] * len(frames))

    def test_ordinary_stop_and_delayed_recovery_keep_confirmation_policy(self):
        frames = pause() + missing(32) + movement(speeds=())
        evidence, labels = pipeline(frames)
        report = first_report(evidence)
        self.assertEqual(labels[24:report + 2], ['D'] * (report + 2 - 24))
        self.assertEqual(labels[report + 2:], ['X'] * (len(frames) - report - 2))
        self.assertFalse(np.any(evidence['initial_dead']))

    def test_new_half_cannot_inherit_pending_initial_confirmation(self):
        first = moving(4)
        second = [dict(x=40.)] * 25 + moving()
        joined, labels = pipeline(first + second, [kickoff(-2, 4), kickoff(10, 40)],
                                  [(1, 0, 3), (2, 4, len(first + second) - 1)])
        fresh, fresh_labels = pipeline(second, [kickoff(6, 36)])
        self.assertEqual(labels[:4], ['D'] * 4)
        self.assertEqual(labels[4:], fresh_labels)
        for field in joined:
            np.testing.assert_equal(joined[field][4:], fresh[field])


class KnownStartupLimitations(unittest.TestCase):
    """Passing assertions expose failures; do not count these as negative controls."""

    def test_actual_kickoff_at_graded_start_still_gets_false_D_prefix(self):
        # Invented truth: play is live from sample 0. No authorization field
        # distinguishes these observations from a preparatory movement.
        for speeds, report, confirmation in (((3.,) * 3, 2, 4), ((0.,) * 3, 9, 11)):
            with self.subTest(speeds=speeds):
                evidence, labels = pipeline(moving(speeds=speeds), [kickoff(-5, 30)])
                self.assertEqual(first_report(evidence), report)
                self.assertEqual(labels[:confirmation], ['D'] * confirmation)
                self.assertEqual(labels[confirmation:confirmation + 11], ['X'] * 11)
                self.assertEqual(labels[confirmation + 11:], ['H'] * (35 - confirmation - 11))

    def test_fast_pre_restart_handling_falsely_releases_D(self):
        # Invented scenario: 3 m/s in-pitch retrieval, then stationary handling,
        # then an actual kickoff at 90. The phase spans both dead and live play.
        retrieval = [dict(x=40 + .12 * (i + 1)) for i in range(40)]
        frames = [dict(x=40.)] * 20 + retrieval + [dict(x=44.8)] * 30 + moving(start=45.3)
        evidence, labels = pipeline(frames, [kickoff(5, 110)])
        report = first_report(evidence)
        self.assertLess(report + 2, 60)
        self.assertEqual(labels[report + 2], 'X')
        self.assertNotIn('D', labels[report + 2:90])
        self.assertEqual(labels[89], 'H')
        # Backdating to report/onset would expand this false-live interval.
        self.assertEqual(labels[report:report + 2], ['D', 'D'])


if __name__ == '__main__':
    unittest.main()
