"""Invented fixtures only. Run with python -m unittest discover -s tests -v."""

import copy
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

import games
from starter import tactical_tracking as tracking


METADATA = """<EPTS><Metadata><Teams>
  <Team id="blue"><Name>Home Example</Name></Team>
  <Team id="red"><Name>Away Example</Name></Team>
</Teams><Players>
  <Player id="z" teamId="red"/><Player id="a" teamId="blue"/>
</Players><Devices><Device><Sensors><Sensor><Channels>
  <Channel id="horizontal"><Name>position_x</Name><Unit>normalized</Unit></Channel>
  <Channel id="vertical"><Name>position_y</Name><Unit>normalized</Unit></Channel>
  <Channel id="pace"><Name>speed_kph</Name><Unit>kph</Unit></Channel>
</Channels></Sensor></Sensors></Device></Devices><PlayerChannels>
  <PlayerChannel id="a-speed" playerId="a" channelId="pace"/>
  <PlayerChannel id="z-y" playerId="z" channelId="vertical"/>
  <PlayerChannel id="a-x" playerId="a" channelId="horizontal"/>
  <PlayerChannel id="z-speed" playerId="z" channelId="pace"/>
  <PlayerChannel id="a-y" playerId="a" channelId="vertical"/>
  <PlayerChannel id="z-x" playerId="z" channelId="horizontal"/>
</PlayerChannels></Metadata><DataFormatSpecifications>
<DataFormatSpecification separator=":">
  <StringRegister name="frameCount"/>
  <SplitRegister separator=";">
    <SplitRegister separator=",">
      <PlayerChannelRef playerChannelId="z-x"/>
      <PlayerChannelRef playerChannelId="z-y"/>
      <PlayerChannelRef playerChannelId="z-speed"/>
    </SplitRegister>
    <SplitRegister separator=",">
      <PlayerChannelRef playerChannelId="a-x"/>
      <PlayerChannelRef playerChannelId="a-y"/>
      <PlayerChannelRef playerChannelId="a-speed"/>
    </SplitRegister>
  </SplitRegister>
  <SplitRegister separator=",">
    <BallChannelRef channelId="horizontal"/>
    <BallChannelRef channelId="vertical"/>
    <BallChannelRef channelId="pace"/>
  </SplitRegister>
</DataFormatSpecification></DataFormatSpecifications></EPTS>"""
# Raw fixture speeds are km/h: these deliberately represent 2 and 3 m/s.
OBSERVATIONS = "0.5,0.5,7.2;1.2,-0.1,10.8:0.5,0.5,NaN"


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
        self.assertAlmostEqual(first["players"][0]["speed_mps"], 2)
        self.assertAlmostEqual(first["players"][1]["speed_mps"], 3)
        self.assertEqual(first["players"][1]["x_norm"], 1.2)
        self.assertAlmostEqual(first["players"][1]["y_m"], -6.8)
        second["players"][0]["x_m"] = -123
        second["ball"]["x_m"] = -456
        self.assertEqual(first, saved)
        self.assertEqual(list(frames), [])

    def test_missing_position_and_speed_are_independent(self):
        self.raw.write_text(
            "1:NaN,0.5,25.2;0.5,0.5,NaN:0.1,inf,2\n"
            "2:0.2,-inf,NaN;NaN,NaN,inf:NaN,NaN,NaN\n"
            "3:inf,0.3,14.4;0,0,0:NaN,0.5,1\n", encoding="utf-8")
        first, second, third = list(self.frames(3))
        self.assertIsNone(first["ball"])
        self.assertIsNone(second["ball"])
        self.assertIsNone(third["ball"])
        for player in [first["players"][0], *second["players"], third["players"][0]]:
            self.assertFalse(player["observed"])
            for field in ("x_norm", "y_norm", "x_m", "y_m"):
                self.assertIsNone(player[field])
        self.assertAlmostEqual(first["players"][0]["speed_mps"], 7)
        self.assertAlmostEqual(third["players"][0]["speed_mps"], 4)
        self.assertTrue(first["players"][1]["observed"])
        self.assertIsNone(first["players"][1]["speed_mps"])
        self.assertTrue(third["players"][1]["observed"])
        self.assertEqual(third["players"][1]["x_m"], 0)
        self.assertTrue(all(p["speed_mps"] is None for p in second["players"]))
        self.assertEqual(third["players"][1]["speed_mps"], 0)

    def test_kph_regression(self):
        self.raw.write_text("1:0.5,0.5,36;0,0,0:0.5,0.5,36\n", encoding="utf-8")
        frame, = self.frames(1)
        self.assertAlmostEqual(frame["players"][0]["speed_mps"], 10)
        self.assertEqual(frame["players"][1]["speed_mps"], 0)
        self.assertEqual(set(frame["ball"]), {"x_norm", "y_norm", "x_m", "y_m"})

    def test_mps_is_not_converted_again(self):
        self.meta.write_text(METADATA.replace("speed_kph", "speed_mps").replace(
            "<Unit>kph</Unit>", "<Unit>m/s</Unit>"), encoding="utf-8")
        self.raw.write_text("1:0.5,0.5,10;0,0,36:0,0,0\n", encoding="utf-8")
        frame, = self.frames(1)
        self.assertAlmostEqual(frame["players"][0]["speed_mps"], 10)
        self.assertAlmostEqual(frame["players"][1]["speed_mps"], 36)

    def test_nonfinite_speeds_keep_valid_positions(self):
        for value in ("NaN", "inf", "-inf"):
            with self.subTest(value=value):
                self.raw.write_text("1:0.5,0.5,{};0,0,0:0,0,0\n".format(value),
                                    encoding="utf-8")
                frame, = self.frames(1)
                self.assertTrue(frame["players"][0]["observed"])
                self.assertEqual(frame["players"][0]["x_m"], 52.65)
                self.assertIsNone(frame["players"][0]["speed_mps"])

    def test_invalid_channel_metadata_is_rejected_before_streaming(self):
        def change(attribute, value):
            return lambda root: root.find(".//PlayerChannelRef").set(attribute, value)

        cases = [
            (lambda r: r.find(".//Channel[@id='pace']").remove(
                r.find(".//Channel[@id='pace']/Unit")), "speed unit"),
            (lambda r: setattr(r.find(".//Channel[@id='pace']/Unit"), "text", ""),
             "speed unit"),
            (lambda r: ET.SubElement(r.find(".//Channel[@id='pace']"), "Unit").__setattr__(
                "text", "m/s"), "contradictory speed unit"),
            (lambda r: setattr(r.find(".//Channel[@id='pace']/Unit"), "text", "mph"),
             "speed unit"),
            (lambda r: setattr(r.find(".//Channel[@id='pace']/Unit"), "text", "m/s"),
             "conflicting speed"),
            (lambda r: r.find(".//Channel[@id='pace']").remove(
                r.find(".//Channel[@id='pace']/Name")), "speed channel"),
            (change("playerChannelId", "missing"), "channel reference"),
            (change("playerChannelId", "a-x"), "Player order"),
            (change("playerChannelId", "z-y"), "x,y"),
            (lambda r: r.find(".//PlayerChannels").append(
                copy.deepcopy(r.find(".//PlayerChannel"))), "duplicate PlayerChannel"),
            (lambda r: r.find(".//Channels").append(
                copy.deepcopy(r.find(".//Channel"))), "duplicate Channel"),
            (lambda r: r.find(".//DataFormatSpecifications").clear(), "DataFormatSpecification"),
            (lambda r: r.find(".//DataFormatSpecification").set("separator", "|"),
             "frame:players:ball"),
            (lambda r: r.find(".//Channel[@id='horizontal']/Unit").__setattr__(
                "text", "m"), "normalized x,y"),
        ]
        for modify, message in cases:
            with self.subTest(message=message):
                root = ET.fromstring(METADATA)
                modify(root)
                ET.ElementTree(root).write(self.meta, encoding="utf-8")
                # No raw file exists: metadata must fail before opening it or yielding frames.
                with self.assertRaises(tracking.TrackingDataError) as caught:
                    next(self.frames(1))
                self.assertIn(str(self.meta), str(caught.exception))
                self.assertIn(message, str(caught.exception))
                self.assertNotIn("<Channel", str(caught.exception))

    def test_invalid_ball_channel_references_are_rejected_before_streaming(self):
        cases = ("missing-all", "missing-one", "extra", "wrong-type", "swapped",
                 "missing-id-0", "missing-id-1", "missing-id-2",
                 "unknown-id-0", "unknown-id-1", "unknown-id-2")
        self.write_records([1])
        for case in cases:
            with self.subTest(case=case):
                root = ET.fromstring(METADATA)
                ball = root.find(".//DataFormatSpecification")[2]
                if case == "missing-all":
                    ball[:] = []
                elif case == "missing-one":
                    ball.remove(ball[-1])
                elif case == "extra":
                    ball.append(copy.deepcopy(ball[-1]))
                elif case == "wrong-type":
                    ball[0].tag = "PlayerChannelRef"
                elif case == "swapped":
                    ball[0], ball[1] = ball[1], ball[0]
                elif case.startswith("missing-id"):
                    ball[int(case[-1])].attrib.clear()
                else:
                    ball[int(case[-1])].set("channelId", "unknown")
                ET.ElementTree(root).write(self.meta, encoding="utf-8")
                with self.assertRaises(tracking.TrackingDataError) as caught:
                    next(self.frames(1))
                self.assertIn(str(self.meta), str(caught.exception))
                self.assertIn("ball", str(caught.exception))

    def separate_ball_positions(self):
        """Invented ball-only definitions ensure player checks cannot mask ball gaps."""
        root = ET.fromstring(METADATA)
        channels = root.find(".//Channels")
        ball = root.find(".//DataFormatSpecification")[2]
        for axis, channel_id in enumerate(("horizontal", "vertical")):
            channel = copy.deepcopy(root.find(".//Channel[@id='{}']".format(channel_id)))
            channel.set("id", "ball-" + channel_id)
            channels.append(channel)
            ball[axis].set("channelId", channel.get("id"))
        return root

    def assert_ambiguous_positions_rejected(self, owner):
        self.write_records([1])
        for channel_id in ("horizontal", "vertical"):
            for tag in ("Name", "Unit"):
                for variant in ("duplicate", "contradictory"):
                    with self.subTest(owner=owner, channel=channel_id, tag=tag, variant=variant):
                        root = self.separate_ball_positions()
                        definition_id = ("ball-" if owner == "ball" else "") + channel_id
                        channel = root.find(".//Channel[@id='{}']".format(definition_id))
                        extra = ET.SubElement(channel, tag)
                        extra.text = (channel.findtext(tag) if variant == "duplicate" else
                                      "position_z" if tag == "Name" else "m")
                        ET.ElementTree(root).write(self.meta, encoding="utf-8")
                        with self.assertRaises(tracking.TrackingDataError) as caught:
                            next(self.frames(1))
                        self.assertIn(str(self.meta), str(caught.exception))
                        self.assertIn("ball" if owner == "ball" else "Player slot",
                                      str(caught.exception))
                        self.assertIn("normalized x,y", str(caught.exception))

    def test_ambiguous_player_position_declarations_are_rejected(self):
        self.assert_ambiguous_positions_rejected("player")

    def test_ambiguous_ball_position_declarations_are_rejected(self):
        self.assert_ambiguous_positions_rejected("ball")

    def test_distinct_ball_position_channels_are_supported(self):
        ET.ElementTree(self.separate_ball_positions()).write(self.meta, encoding="utf-8")
        self.raw.write_text("1:" + OBSERVATIONS.split(":")[0] + ":0.2,0.8,36\n",
                            encoding="utf-8")
        frame, = self.frames(1)
        self.assertEqual(set(frame["ball"]), {"x_norm", "y_norm", "x_m", "y_m"})
        self.assertEqual((frame["ball"]["x_norm"], frame["ball"]["y_norm"]), (0.2, 0.8))
        self.assertAlmostEqual(frame["ball"]["x_m"], 21.06)
        self.assertAlmostEqual(frame["ball"]["y_m"], 54.4)
        self.assertAlmostEqual(frame["players"][0]["speed_mps"], 2)

    def test_reversed_register_slots_are_not_silently_mislabeled(self):
        root = ET.fromstring(METADATA)
        registers = root.find(".//DataFormatSpecification")[1]
        registers[:] = list(reversed(registers))
        ET.ElementTree(root).write(self.meta, encoding="utf-8")
        with self.assertRaisesRegex(tracking.TrackingDataError, "Player order"):
            next(self.frames(1))

    def test_slot_speed_declarations_must_agree(self):
        root = ET.fromstring(METADATA)
        channels = root.find(".//Channels")
        ET.SubElement(channels, "Channel", id="other-speed")
        other = channels[-1]
        ET.SubElement(other, "Name").text = "speed_mps"
        ET.SubElement(other, "Unit").text = "m/s"
        root.find(".//PlayerChannel[@id='a-speed']").set("channelId", "other-speed")
        ET.ElementTree(root).write(self.meta, encoding="utf-8")
        with self.assertRaisesRegex(tracking.TrackingDataError, "inconsistent speed"):
            next(self.frames(1))

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
        result = subprocess.run(
            [sys.executable, "-m", "starter.tactical_tracking", "--data-dir", self.temp.name],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stderr)
        self.assertIn("record 2", result.stderr)
        self.assertEqual(result.stdout, "")
        self.meta.write_text(METADATA.replace("<Unit>kph</Unit>", "<Unit>mph</Unit>"),
                             encoding="utf-8")
        error = io.StringIO()
        with redirect_stderr(error):
            self.assertEqual(tracking.main(["--data-dir", self.temp.name]), 1)
        self.assertIn("unsupported speed unit", error.getvalue())


if __name__ == "__main__":
    unittest.main()
