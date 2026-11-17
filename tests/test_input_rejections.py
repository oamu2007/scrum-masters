"""Contradictory or incomplete M2/M4 input must be rejected, not turned into a label.

Field names come from input_checks.py (an assumption until M2/M4 publish their schema).
"""

import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import input_checks as ic  # noqa: E402


def alive(frame=0, distance=1.5, side="H"):
    return {"frame": frame, "ball_available": True, "nearest_distance_m": distance,
            "nearest_side": side}


def unavailable(frame=0):
    return {"frame": frame, "ball_available": False, "nearest_distance_m": None,
            "nearest_side": "?"}


class ConsistentRecordsPass(unittest.TestCase):
    def test_available_with_distance_and_side(self):
        self.assertEqual(ic.validate_record(alive()), [])

    def test_unavailable_with_no_distance_and_unknown_side(self):
        self.assertEqual(ic.validate_record(unavailable()), [])

    def test_zero_distance_is_a_real_distance(self):
        self.assertEqual(ic.validate_record(alive(distance=0.0)), [])


class ContradictionsAreRejected(unittest.TestCase):
    def test_unavailable_but_distance_present(self):
        record = unavailable()
        record["nearest_distance_m"] = 2.0
        self.assertTrue(any("unavailable but a distance" in r for r in ic.validate_record(record)))

    def test_unavailable_but_side_present(self):
        record = unavailable()
        record["nearest_side"] = "H"
        self.assertTrue(any("unavailable but a side" in r for r in ic.validate_record(record)))

    def test_available_but_distance_empty(self):
        for empty in (None, float("nan"), ""):
            record = alive()
            record["nearest_distance_m"] = empty
            self.assertTrue(any("distance is empty" in r for r in ic.validate_record(record)), empty)

    def test_available_but_side_empty(self):
        record = alive()
        record["nearest_side"] = None
        self.assertTrue(any("side is empty" in r for r in ic.validate_record(record)))

    def test_negative_infinite_and_absurd_distances(self):
        for bad in (-0.1, float("inf"), ic.MAX_PLAUSIBLE_DISTANCE_M + 1):
            self.assertTrue(ic.validate_record(alive(distance=bad)), bad)

    def test_distance_that_is_text(self):
        self.assertTrue(any("not a number" in r for r in ic.validate_record(alive(distance="1.5"))))

    def test_availability_must_be_a_real_boolean(self):
        for bad in ("true", 1, None):
            record = alive()
            record["ball_available"] = bad
            self.assertTrue(any("True/False" in r for r in ic.validate_record(record)), bad)

    def test_unknown_side_code(self):
        self.assertTrue(any("not in" in r for r in ic.validate_record(alive(side="Home"))))


class MissingFieldsAreRejected(unittest.TestCase):
    def test_each_required_field_missing_is_named(self):
        for field in ic.REQUIRED_FIELDS:
            record = alive()
            del record[field]
            reasons = ic.validate_record(record)
            self.assertEqual(reasons, ["missing field '{}'".format(field)], field)

    def test_empty_record(self):
        self.assertEqual(len(ic.validate_record({})), len(ic.REQUIRED_FIELDS))


class SequenceChecks(unittest.TestCase):
    def test_clean_sequence_has_no_rejections(self):
        self.assertEqual(ic.validate_records([alive(0), unavailable(1), alive(2, side="A")]), {})

    def test_skipped_repeated_and_reordered_frames(self):
        for frames in ([0, 2], [0, 0], [1, 0]):
            rejected = ic.validate_records([alive(f) for f in frames])
            self.assertIn(1, rejected, frames)
            self.assertTrue(any("gap, repeat or reorder" in r for r in rejected[1]))

    def test_only_the_bad_row_is_reported(self):
        records = [alive(i) for i in range(5)]
        records[3] = copy.deepcopy(records[3])
        records[3]["nearest_distance_m"] = None
        self.assertEqual(list(ic.validate_records(records)), [3])


if __name__ == "__main__":
    unittest.main()
