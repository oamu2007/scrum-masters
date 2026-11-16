"""Tests for the release runner (run_possession.py).

Invented data only: no match files, no labels, no network. The tracking reader (M3), M1's
score_frame and games.py are replaced with small fakes, so these tests exercise the runner's own
behaviour: single read, frame-order checks, evidence validation, per-half decoding and output.

    python -m unittest discover -s tests -v
"""

import hashlib
import os
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import run_possession as rp  # noqa: E402

N = 70
# Two small "halves", inclusive like games.half_video_blocks: frames 10..29 and 40..59.
BLOCKS = [(1, 10, 29), (2, 40, 59)]
LEGAL = {"H", "A", "D", "X"}


def new_evidence(n=N):
    """Evidence with no ball anywhere: every side unavailable, every score zero."""
    return {
        "ball_visible": np.zeros(n, dtype=bool),
        "d_home": np.full(n, np.nan),
        "d_away": np.full(n, np.nan),
        "score_home": np.zeros(n),
        "score_away": np.zeros(n),
        "home_available": np.zeros(n, dtype=bool),
        "away_available": np.zeros(n, dtype=bool),
    }


def lead(evidence, first, last, side):
    """Frames first..last (inclusive): both sides available and `side` clearly leads."""
    home, away = (0.8, 0.1) if side == "H" else (0.1, 0.8)
    sl = slice(first, last + 1)
    evidence["ball_visible"][sl] = True
    evidence["home_available"][sl] = True
    evidence["away_available"][sl] = True
    evidence["score_home"][sl] = home
    evidence["score_away"][sl] = away
    evidence["d_home"][sl] = 1.0
    evidence["d_away"][sl] = 5.0


def decode(evidence, n=N):
    with mock.patch.object(rp, "half_video_blocks", return_value=BLOCKS):
        return rp.decode_match(evidence, n, "fake-game")


def fake_evidence(observation, tau=3.0):
    """Stand-in for M1.score_frame: a fixed, valid seven-field result keyed on the frame."""
    frame = observation["frame"]
    return {
        "ball_visible": True,
        "d_home": float(frame),
        "d_away": float(frame) + 1.0,
        "score_home": 0.5,
        "score_away": 0.25,
        "home_available": True,
        "away_available": frame % 2 == 0,
    }


class FakeSource:
    """Iterator over invented observations that records whether it was closed."""

    def __init__(self, frames):
        self._frames = iter(frames)
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._frames)

    def close(self):
        self.closed = True


def run_collect(frames, n=5, producers=()):
    """Run collect_evidence over `frames` (a list of observation dicts) with M3/M1 faked."""
    source = FakeSource(frames)
    calls = []

    def score(observation, tau=3.0):
        calls.append(observation)
        return fake_evidence(observation, tau)

    with mock.patch.object(rp, "source_frames", return_value=n), \
            mock.patch.object(rp, "iter_tracking_frames", return_value=source) as reader, \
            mock.patch.object(rp, "score_frame", side_effect=score), \
            mock.patch.object(rp, "PRODUCERS", list(producers)):
        try:
            result = rp.collect_evidence(3.0, "fake-game", "fake-dir")
        finally:
            pass
    return result, source, reader, calls


class CollectEvidenceTests(unittest.TestCase):
    def test_tracking_is_read_once_and_each_observation_is_shared_unchanged(self):
        frames = [{"frame": i} for i in range(5)]
        snapshot = [dict(f) for f in frames]
        seen = []
        _, source, reader, calls = run_collect(
            frames, producers=[lambda index, observation: seen.append((index, observation))])

        reader.assert_called_once_with(game="fake-game", data_dir="fake-dir")
        self.assertEqual(len(calls), 5)                    # M1 saw every frame exactly once
        self.assertEqual([i for i, _ in seen], [0, 1, 2, 3, 4])  # so did the extra producer
        for observation, (_, shared), original in zip(calls, seen, frames):
            self.assertIs(observation, shared)             # the same object went to both
            self.assertIs(observation, original)
        self.assertEqual(frames, snapshot)                 # and nothing modified it
        self.assertTrue(source.closed)

    def test_values_land_at_their_frame_index(self):
        result, _, _, _ = run_collect([{"frame": i} for i in range(5)])
        self.assertEqual(result["d_home"].tolist(), [0.0, 1.0, 2.0, 3.0, 4.0])
        self.assertEqual(result["home_available"].dtype, np.bool_)
        self.assertEqual(result["away_available"].tolist(), [True, False, True, False, True])
        for array in result.values():
            self.assertEqual(array.shape, (5,))

    def test_out_of_order_frames_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "out of order"):
            run_collect([{"frame": 0}, {"frame": 2}, {"frame": 1}, {"frame": 3}, {"frame": 4}])

    def test_repeated_frame_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "out of order"):
            run_collect([{"frame": 0}, {"frame": 0}, {"frame": 1}, {"frame": 2}, {"frame": 3}])

    def test_observation_without_frame_field_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "no 'frame' field"):
            run_collect([{"frame": 0}, {"x": 1}, {"frame": 2}, {"frame": 3}, {"frame": 4}])

    def test_too_few_frames_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "expected 5 tracking frames, read 4"):
            run_collect([{"frame": i} for i in range(4)])

    def test_too_many_frames_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "more frames than the video"):
            run_collect([{"frame": i} for i in range(6)])

    def test_source_is_closed_when_a_check_fails(self):
        source = FakeSource([{"frame": 0}, {"frame": 3}])
        with mock.patch.object(rp, "source_frames", return_value=5), \
                mock.patch.object(rp, "iter_tracking_frames", return_value=source), \
                mock.patch.object(rp, "score_frame", side_effect=fake_evidence):
            with self.assertRaises(RuntimeError):
                rp.collect_evidence(3.0, "fake-game", None)
        self.assertTrue(source.closed)


class DecodeMatchTests(unittest.TestCase):
    def test_x_outside_the_graded_halves_and_inclusive_endpoints(self):
        evidence = new_evidence()
        lead(evidence, 0, N - 1, "H")          # clear evidence everywhere, even outside play
        labels = decode(evidence)

        self.assertEqual(len(labels), N)
        self.assertTrue(set(labels) <= LEGAL)
        for frame in list(range(0, 10)) + list(range(30, 40)) + list(range(60, N)):
            self.assertEqual(labels[frame], "X", "frame {} is outside the halves".format(frame))
        for first, last in ((10, 29), (40, 59)):
            self.assertEqual(labels[first], "H")   # first graded frame is inclusive
            self.assertEqual(labels[last], "H")    # last graded frame is inclusive
            self.assertEqual(labels[first - 1], "X")
            self.assertEqual(labels[last + 1], "X")

    def test_second_half_starts_fresh_after_a_confirmed_side(self):
        evidence = new_evidence()
        lead(evidence, 10, 29, "A")            # half one ends with A in control
        lead(evidence, 40, 59, "H")            # half two opens with clear H control
        labels = decode(evidence)
        self.assertEqual(labels[29], "A")
        # Leaked state would keep A for CONFIRM_FRAMES-1 frames; a fresh half says H at once.
        self.assertEqual(labels[40], "H")

    def test_second_half_does_not_inherit_a_pending_switch(self):
        evidence = new_evidence()
        lead(evidence, 10, 24, "H")
        lead(evidence, 25, 29, "A")            # a 5-frame challenge still pending at half time
        lead(evidence, 40, 59, "A")
        labels = decode(evidence)
        self.assertEqual(labels[29], "H")      # 5 frames were not enough to switch
        self.assertEqual(labels[40], "A")      # fresh half: first clear evidence is taken

    def test_a_half_gives_the_same_labels_alone_as_inside_the_full_run(self):
        evidence = new_evidence()
        lead(evidence, 10, 29, "H")
        lead(evidence, 40, 47, "H")
        lead(evidence, 48, 59, "A")
        labels = decode(evidence)
        self.assertEqual(labels[40:60], rp.decode_half(evidence, 40, 59))
        self.assertEqual(labels[10:30], rp.decode_half(evidence, 10, 29))

    def test_x_until_the_first_confirmed_side_then_memory_through_missing_evidence(self):
        evidence = new_evidence()
        lead(evidence, 14, 16, "H")            # control appears only at frame 14
        # frames 17..29: ball lost / no evidence at all (an occluded pass)
        labels = decode(evidence)
        self.assertEqual(labels[10:14], ["X"] * 4)
        self.assertEqual(labels[14:30], ["H"] * 16)

    def test_a_single_opposing_frame_does_not_switch(self):
        evidence = new_evidence()
        lead(evidence, 10, 29, "H")
        lead(evidence, 20, 20, "A")            # one nearest-player flip
        self.assertEqual(decode(evidence)[10:30], ["H"] * 20)

    def test_opposing_control_one_frame_short_of_confirmation_does_not_switch(self):
        evidence = new_evidence()
        lead(evidence, 10, 12, "H")
        lead(evidence, 13, 13 + rp.CONFIRM_FRAMES - 2, "A")    # CONFIRM_FRAMES - 1 frames
        lead(evidence, 13 + rp.CONFIRM_FRAMES - 1, 29, "H")
        self.assertEqual(set(decode(evidence)[10:30]), {"H"})

    def test_sustained_opposing_control_switches_exactly_once(self):
        evidence = new_evidence()
        lead(evidence, 10, 12, "H")
        start = 13
        lead(evidence, start, 29, "A")
        labels = decode(evidence)
        switch = start + rp.CONFIRM_FRAMES - 1                  # the CONFIRM_FRAMES-th A frame
        self.assertEqual(set(labels[10:switch]), {"H"})
        self.assertEqual(set(labels[switch:30]), {"A"})
        changes = sum(1 for a, b in zip(labels[10:30], labels[11:30]) if a != b)
        self.assertEqual(changes, 1)

    def test_missing_home_evidence_never_lets_away_win_by_comparison_with_zero(self):
        evidence = new_evidence()
        lead(evidence, 10, 12, "H")
        sl = slice(13, 30)                      # away is near the ball, home has no evidence
        evidence["ball_visible"][sl] = True
        evidence["away_available"][sl] = True
        evidence["score_away"][sl] = 0.9
        evidence["d_away"][sl] = 0.5
        labels = decode(evidence)
        self.assertEqual(set(labels[10:30]), {"H"})

    def test_weak_or_tied_evidence_keeps_the_current_side(self):
        evidence = new_evidence()
        lead(evidence, 10, 12, "H")
        sl = slice(13, 30)
        evidence["ball_visible"][sl] = True
        evidence["home_available"][sl] = True
        evidence["away_available"][sl] = True
        evidence["score_home"][sl] = 0.02       # both far from the ball: below MIN_SCORE
        evidence["score_away"][sl] = 0.04
        evidence["d_home"][sl] = 12.0
        evidence["d_away"][sl] = 10.0
        self.assertEqual(set(decode(evidence)[10:30]), {"H"})

    def test_invalid_evidence_is_rejected_before_decoding(self):
        bad_cases = {
            "score above 1": lambda e: e["score_home"].__setitem__(15, 1.5),
            "nan score": lambda e: e["score_away"].__setitem__(15, np.nan),
            "availability without ball": lambda e: e["home_available"].__setitem__(5, True),
            "score where unavailable": lambda e: e["score_away"].__setitem__(5, 0.3),
            "negative distance": lambda e: e["d_home"].__setitem__(15, -2.0),
            "short array": lambda e: e.__setitem__("score_home", e["score_home"][:-1]),
            "integer flags": lambda e: e.__setitem__("ball_visible",
                                                     e["ball_visible"].astype(int)),
            "missing field": lambda e: e.pop("d_away"),
        }
        for name, damage in bad_cases.items():
            evidence = new_evidence()
            lead(evidence, 10, 29, "H")
            damage(evidence)
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    decode(evidence)

    def test_every_label_is_legal_and_length_matches(self):
        evidence = new_evidence()
        lead(evidence, 10, 20, "H")
        lead(evidence, 41, 55, "A")
        labels = decode(evidence)
        self.assertEqual(len(labels), N)
        self.assertTrue(set(labels) <= LEGAL)


class OutputTests(unittest.TestCase):
    def test_write_submission_format(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "nested", "out.csv")
            rp.write_submission(path, ["X", "H", "A", "D"])
            with open(path, newline="") as handle:
                text = handle.read()
            self.assertEqual(text, "frame,label\n0,X\n1,H\n2,A\n3,D\n")
            self.assertEqual(os.listdir(os.path.dirname(path)), ["out.csv"])

    def test_failed_write_leaves_no_partial_or_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.csv")
            with mock.patch.object(rp.os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    rp.write_submission(path, ["H"] * 10)
            self.assertEqual(os.listdir(folder), [])

    def test_failed_write_keeps_the_previous_good_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.csv")
            rp.write_submission(path, ["H", "A"])
            with mock.patch.object(rp.os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    rp.write_submission(path, ["A", "A"])
            with open(path, newline="") as handle:
                self.assertEqual(handle.read(), "frame,label\n0,H\n1,A\n")

    def test_failure_while_writing_keeps_the_previous_file_and_leaves_no_temporary(self):
        def broken_labels():
            yield "A"
            yield "A"
            raise RuntimeError("labels failed halfway")

        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.csv")
            rp.write_submission(path, ["H", "A", "D"])
            with open(path, "rb") as handle:
                before = handle.read()
            with self.assertRaisesRegex(RuntimeError, "halfway"):
                rp.write_submission(path, broken_labels())
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), before)      # byte for byte, not just "a file"
            self.assertEqual(os.listdir(folder), ["out.csv"])

    def test_repeating_the_write_gives_identical_bytes(self):
        labels = ["X", "X", "H", "H", "A", "D", "A", "X"]
        with tempfile.TemporaryDirectory() as folder:
            first = os.path.join(folder, "first.csv")
            second = os.path.join(folder, "second.csv")
            rp.write_submission(first, labels)
            rp.write_submission(second, labels)
            rp.write_submission(first, labels)               # overwrite the same path
            with open(first, "rb") as a, open(second, "rb") as b:
                data_a, data_b = a.read(), b.read()
            self.assertEqual(data_a, data_b)
            self.assertEqual(hashlib.sha256(data_a).digest(), hashlib.sha256(data_b).digest())

    def test_bytes_are_utf8_with_lf_line_endings_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.csv")
            rp.write_submission(path, ["H", "A", "D", "X"])
            with open(path, "rb") as handle:
                data = handle.read()
        self.assertEqual(data, b"frame,label\n0,H\n1,A\n2,D\n3,X\n")
        self.assertNotIn(b"\r", data)                        # no CRLF even on Windows
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))   # no byte-order mark
        data.decode("utf-8")                                 # decodes without error

    def test_write_uses_utf8_regardless_of_the_default_encoding(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.csv")
            real_open = open
            seen = {}

            def spy(file, mode="r", *args, **kwargs):
                if str(file).endswith(".tmp"):
                    seen["encoding"] = kwargs.get("encoding")
                return real_open(file, mode, *args, **kwargs)

            with mock.patch("builtins.open", side_effect=spy):
                rp.write_submission(path, ["H"])
        self.assertEqual(seen.get("encoding"), "utf-8")

    def test_main_repeat_run_is_byte_identical(self):
        evidence = new_evidence()
        lead(evidence, 10, 29, "H")
        lead(evidence, 40, 59, "A")
        outputs = []
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(rp, "source_frames", return_value=N), \
                    mock.patch.object(rp, "collect_evidence", return_value=evidence), \
                    mock.patch.object(rp, "half_video_blocks", return_value=BLOCKS):
                for name in ("one.csv", "two.csv"):
                    out = os.path.join(folder, name)
                    self.assertEqual(rp.main(["--out", out]), 0)
                    with open(out, "rb") as handle:
                        outputs.append(handle.read())
        self.assertEqual(outputs[0], outputs[1])

    def test_main_writes_one_row_per_frame(self):
        evidence = new_evidence()
        lead(evidence, 10, 29, "H")
        lead(evidence, 40, 59, "A")
        with tempfile.TemporaryDirectory() as folder:
            out = os.path.join(folder, "release", "team.csv")
            with mock.patch.object(rp, "source_frames", return_value=N), \
                    mock.patch.object(rp, "collect_evidence", return_value=evidence), \
                    mock.patch.object(rp, "half_video_blocks", return_value=BLOCKS):
                self.assertEqual(rp.main(["--out", out]), 0)
            with open(out, newline="") as handle:
                lines = handle.read().split("\n")
            self.assertEqual(lines[0], "frame,label")
            self.assertEqual(lines[-1], "")
            rows = lines[1:-1]
            self.assertEqual(len(rows), N)
            self.assertEqual([int(r.split(",")[0]) for r in rows], list(range(N)))
            self.assertEqual({r.split(",")[1] for r in rows}, {"H", "A", "X"})

    def test_main_failure_does_not_create_the_output_file(self):
        with tempfile.TemporaryDirectory() as folder:
            out = os.path.join(folder, "team.csv")
            with mock.patch.object(rp, "source_frames", return_value=N), \
                    mock.patch.object(rp, "collect_evidence",
                                      side_effect=RuntimeError("tracking out of order")):
                with self.assertRaises(RuntimeError):
                    rp.main(["--out", out])
            self.assertFalse(os.path.exists(out))
            self.assertFalse(os.path.exists(out + ".tmp"))


if __name__ == "__main__":
    unittest.main()
