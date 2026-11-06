"""Invented fixtures only. Run with python -m unittest discover -s tests -v."""

import copy
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

import games
from starter import tactical_tracking as tracking


METADATA = """<EPTS><Teams>
  <Team id="blue"><Name>Home Example</Name></Team>
  <Team id="red"><Name>Away Example</Name></Team>
</Teams><Players>
  <Player id="z" teamId="red"/><Player id="a" teamId="blue"/>
</Players></EPTS>"""
OBSERVATIONS = "0.5,0.5,2;1.2,-0.1,3:0.5,0.5,NaN"


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.paths = games.asset_paths(data_dir=self.temp.name)
        self.meta = Path(self.paths["atd_meta"])
        self.raw = Path(self.paths["atd_raw"])
        self.meta.parent.mkdir()
        self.meta.write_text(METADATA, encoding="utf-8")

    def write_records(self, ids):
        self.raw.write_text("".join("{}:{}\n".format(i, OBSERVATIONS) for i in ids),
                            encoding="utf-8")

    def frames(self, expected=2):
        return tracking._iter_frames(self.meta, self.raw, expected, 25, (105.3, 68))

    def test_mapping_coordinates_and_independent_frames(self):
        self.write_records([1, 2])
        frames = self.frames()
        first = next(frames)
        saved = copy.deepcopy(first)
        second = next(frames)
        self.assertEqual(first, saved)
        self.assertEqual(first["frame"], 0)
        self.assertEqual(second["frame"], 1)
        self.assertEqual(second["time_s"], 0.04)
        self.assertEqual([p["track_slot"] for p in first["players"]], [1, 2])
        self.assertEqual([p["team"] for p in first["players"]], ["A", "H"])
        for point in (first["players"][0], first["ball"]):
            self.assertEqual(point["x_norm"], 0.5)
            self.assertEqual(point["y_norm"], 0.5)
            self.assertEqual(point["x_m"], 52.65)
            self.assertEqual(point["y_m"], 34)
        self.assertEqual(first["players"][0]["speed_mps"], 2)
        self.assertEqual(first["players"][1]["x_norm"], 1.2)
        self.assertAlmostEqual(first["players"][1]["y_m"], -6.8)
        second["players"][0]["x_m"] = -123
        second["ball"]["x_m"] = -456
        self.assertEqual(first, saved)
        self.assertEqual(list(frames), [])

    def test_missing_position_and_speed_are_independent(self):
        self.raw.write_text(
            "1:NaN,0.5,7;0.5,0.5,NaN:0.1,inf,2\n"
            "2:0.2,-inf,NaN;NaN,NaN,inf:NaN,NaN,NaN\n"
            "3:inf,0.3,4;0,0,0:NaN,0.5,1\n", encoding="utf-8")
        first, second, third = list(self.frames(3))
        self.assertIsNone(first["ball"])
        self.assertIsNone(second["ball"])
        self.assertIsNone(third["ball"])
        for player in [first["players"][0], *second["players"], third["players"][0]]:
            self.assertFalse(player["observed"])
            for field in ("x_norm", "y_norm", "x_m", "y_m"):
                self.assertIsNone(player[field])
        self.assertEqual(first["players"][0]["speed_mps"], 7)
        self.assertTrue(first["players"][1]["observed"])
        self.assertIsNone(first["players"][1]["speed_mps"])
        self.assertTrue(third["players"][1]["observed"])
        self.assertEqual(third["players"][1]["x_m"], 0)
        self.assertTrue(all(p["speed_mps"] is None for p in second["players"]))

    def test_every_id_is_checked(self):
        for ids, bad_record in [([0, 1, 2], 1), ([2, 3, 4], 1), ([1, 1, 3], 2),
                                ([1, 3, 4], 2), ([1, 3, 2], 2), ([1, 2, 1], 3)]:
            with self.subTest(ids=ids):
                self.write_records(ids)
                with self.assertRaises(tracking.TrackingDataError) as caught:
                    list(self.frames(3))
                self.assertIn(str(self.raw), str(caught.exception))
                self.assertIn("record {}".format(bad_record), str(caught.exception))
                self.assertIn("expected tracking frame ID", str(caught.exception))

    def test_final_count_and_lazy_validation(self):
        for ids in ([], [1], [1, 2, 3]):
            with self.subTest(ids=ids):
                self.write_records(ids)
                with self.assertRaises(tracking.TrackingDataError):
                    list(self.frames())
        self.write_records([1])
        frames = self.frames(2)
        self.assertEqual(next(frames)["frame"], 0)
        with self.assertRaisesRegex(tracking.TrackingDataError, "record 2.*end of file"):
            next(frames)

    def test_malformed_raw_has_safe_context(self):
        cases = [
            ("\n", "frame:players:ball"),
            ("1:no-data\n", "frame:players:ball"),
            ("1.0:" + OBSERVATIONS, "frame ID"),
            ("9" * 5000 + ":" + OBSERVATIONS, "frame ID"),
            ("1:0,0,0:0,0,0", "player slots"),
            ("1:0,0,0;0,0,0;0,0,0:0,0,0", "player slots"),
            ("1:0,0;0,0,0:0,0,0", "player slot 1"),
            ("1:0,0,0;0,0,0:0,0", "ball"),
            ("1:0,0,0;0,0,0:0,0,0,0", "ball"),
            ("1:SECRET,0,0;0,0,0:0,0,0", "invalid numeric"),
            ("1:0,0,0;0,0,0:0,0,SECRET", "invalid numeric"),
            ("1:0,0,;0,0,0:0,0,0", "invalid numeric"),
        ]
        for row, message in cases:
            with self.subTest(message=message, row=row):
                self.raw.write_text(row, encoding="utf-8")
                with self.assertRaises(tracking.TrackingDataError) as caught:
                    list(self.frames(1))
                error = str(caught.exception)
                self.assertIn(str(self.raw), error)
                self.assertIn("record 1", error)
                self.assertIn(message, error)
                self.assertNotIn("SECRET", error)
                self.assertTrue(caught.exception.__suppress_context__ or
                                caught.exception.__context__ is None)
        self.raw.write_bytes(b"\xff\n")
        with self.assertRaisesRegex(tracking.TrackingDataError, "record 1: invalid UTF-8"):
            list(self.frames(1))

    def test_bad_metadata(self):
        cases = [
            ("<broken>", "malformed XML"),
            (METADATA.replace('teamId="red"', 'teamId="unknown"'), "Player slot 1"),
            (METADATA.replace('teamId="red"', ''), "Player slot 1"),
            (METADATA.replace('id="red"', 'id="blue"'), "duplicate Team IDs"),
            (METADATA.replace('id="red"', ''), "nonempty IDs"),
            ("<EPTS><Team id='one'/></EPTS>", "two Team entries"),
            ("<EPTS><Team id='one'/><Team id='two'/></EPTS>", "no Player"),
        ]
        self.write_records([1])
        for xml, message in cases:
            with self.subTest(message=message):
                self.meta.write_text(xml, encoding="utf-8")
                with self.assertRaises(tracking.TrackingDataError) as caught:
                    list(self.frames(1))
                self.assertIn(str(self.meta), str(caught.exception))
                self.assertIn(message, str(caught.exception))

    def test_public_api_uses_game_config_and_data_directory(self):
        self.write_records([1, 2])
        with patch.dict(games.SOURCES["tactical"], n_video_frames=2), \
                patch.dict(games.GAMES[games.GAME], fps=10, pitch=(100, 60)):
            frames = list(tracking.iter_tracking_frames(data_dir=self.temp.name))
        self.assertEqual(frames[1]["time_s"], 0.1)
        self.assertEqual(frames[0]["ball"]["x_m"], 50)
        self.assertEqual(frames[0]["ball"]["y_m"], 30)

    def test_environment_override_before_import(self):
        self.write_records([1, 2])
        env = dict(os.environ, MTAH_DATA_DIR=self.temp.name)
        result = subprocess.run(
            [sys.executable, "-c", "import games; "
             "games.SOURCES['tactical']['n_video_frames'] = 2; "
             "from starter.tactical_tracking import iter_tracking_frames; "
             "assert sum(1 for _ in iter_tracking_frames()) == 2"],
            cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_verification_command_and_error_exit(self):
        self.write_records([1, 2])
        output = io.StringIO()
        with patch.dict(games.SOURCES["tactical"], n_video_frames=2), redirect_stdout(output):
            self.assertEqual(tracking.main(["--data-dir", self.temp.name]), 0)
        self.assertIn("indices 0..1, 2 slots", output.getvalue())
        self.assertIn("2 / 2 (100.0%)", output.getvalue())
        self.write_records([1, 1])
        error = io.StringIO()
        with patch.dict(games.SOURCES["tactical"], n_video_frames=2), redirect_stderr(error):
            self.assertEqual(tracking.main(["--data-dir", self.temp.name]), 1)
        self.assertIn("record 2", error.getvalue())


if __name__ == "__main__":
    unittest.main()
