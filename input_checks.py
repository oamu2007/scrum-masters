"""Rejection checks for the per-frame records M2/M4 hand to the labeller.

M5 does not implement M2's or M4's algorithms. This module only decides whether a record is
internally consistent enough to be trusted, so contradictory or incomplete input is REJECTED
instead of being turned into a confident H/A label.

FIELD NAMES BELOW ARE AN ASSUMPTION until M2 and M4 push their schema. Change REQUIRED_FIELDS
and the two names in AVAILABILITY_FIELD / DISTANCE_FIELD in one place when they do; the tests
read these constants, so they follow.
"""

import math

REQUIRED_FIELDS = ("frame", "ball_available", "nearest_distance_m", "nearest_side")
AVAILABILITY_FIELD = "ball_available"
DISTANCE_FIELD = "nearest_distance_m"
SIDE_FIELD = "nearest_side"
SIDES = ("H", "A", "?")          # '?' = unknown side, must lead to X, never to a guess
MAX_PLAUSIBLE_DISTANCE_M = 200.0  # longer than a pitch diagonal means a units/parsing bug


def _missing(value):
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and not value.strip()


def validate_record(record):
    """List of reasons this record must be rejected. Empty list = consistent."""
    reasons = []
    for field in REQUIRED_FIELDS:
        if field not in record:
            reasons.append("missing field '{}'".format(field))
    if reasons:
        return reasons          # cannot judge consistency of fields that are not there

    available = record[AVAILABILITY_FIELD]
    distance = record[DISTANCE_FIELD]
    side = record[SIDE_FIELD]

    if not isinstance(available, bool):
        reasons.append("'{}' must be True/False, got {!r}".format(AVAILABILITY_FIELD, available))
        return reasons

    if available:
        if _missing(distance):
            reasons.append("ball marked available but distance is empty")
        elif not isinstance(distance, (int, float)) or isinstance(distance, bool):
            reasons.append("distance is not a number: {!r}".format(distance))
        elif math.isinf(distance) or distance < 0:
            reasons.append("distance {} is not a finite non-negative number".format(distance))
        elif distance > MAX_PLAUSIBLE_DISTANCE_M:
            reasons.append("distance {} m exceeds {} m (units bug?)".format(
                distance, MAX_PLAUSIBLE_DISTANCE_M))
        if _missing(side):
            reasons.append("ball marked available but nearest side is empty")
    else:
        if not _missing(distance):
            reasons.append("ball marked unavailable but a distance ({}) is present".format(distance))
        if not _missing(side) and side != "?":
            reasons.append("ball marked unavailable but a side ({}) is present".format(side))

    if not _missing(side) and side not in SIDES:
        reasons.append("side {!r} not in {}".format(side, SIDES))
    return reasons


def validate_records(records):
    """{index: [reasons]} for every rejected record, plus a check that frames are consecutive."""
    rejected = {}
    previous = None
    for index, record in enumerate(records):
        reasons = validate_record(record)
        frame = record.get("frame") if isinstance(record, dict) else None
        if isinstance(frame, int) and not isinstance(frame, bool):
            if previous is not None and frame != previous + 1:
                reasons = reasons + ["frame {} follows {} (gap, repeat or reorder)".format(
                    frame, previous)]
            previous = frame
        if reasons:
            rejected[index] = reasons
    return rejected
