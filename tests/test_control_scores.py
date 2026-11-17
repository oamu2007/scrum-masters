"""Invented observations and XML only; no restricted data or labels required."""

import copy
import csv
import io
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import numpy as np

import games
from module1 import control_scores as control
from starter import tactical_tracking as tracking


def player(team, x, y, observed=True, speed=None, slot=1):
    return dict(team=team, x_m=x, y_m=y, observed=observed, speed_mps=speed,
                track_slot=slot, x_norm=0.0, y_norm=0.0)


def observation():
    return dict(frame=0, time_s=0.0, ball=dict(x_m=10.0, y_m=10.0), players=[
        player("H", 13.0, 14.0), player("A", 10.0, 11.0, slot=2),
        player("H", 20.0, 10.0, slot=3)])


class FrameScoreTests(unittest.TestCase):
    def test_known_distances_and_scores_in_metres(self):
        result = control.score_frame(observation())
        self.assertEqual(set(result), {"ball_visible", "d_home", "d_away", "score_home",
                                       "score_away", "home_available", "away_available"})
        self.assertEqual((result["d_home"], result["d_away"]), (5.0, 1.0))
        self.assertAlmostEqual(result["score_home"], math.exp(-5.0 / 3.0))
        self.assertAlmostEqual(result["score_away"], math.exp(-1.0 / 3.0))
        self.assertTrue(result["ball_visible"])
        self.assertTrue(result["home_available"] and result["away_available"])
        for side in ("home", "away"):
            self.assertTrue(math.isfinite(result["score_" + side]))
            self.assertTrue(0 <= result["score_" + side] <= 1)
        self.assertAlmostEqual(control.score_frame(observation(), tau=5)["score_home"],
                               math.exp(-1))

    def test_team_swap_swaps_distances_scores_and_availability(self):
        for players in (observation()["players"], [player("H", 13, 14)]):
            with self.subTest(players=len(players)):
                original = dict(observation(), players=players)
                swapped = copy.deepcopy(original)
                for p in swapped["players"]:
                    p["team"] = "A" if p["team"] == "H" else "H"
                a, b = control.score_frame(original), control.score_frame(swapped)
                self.assertEqual(a["ball_visible"], b["ball_visible"])
                for home, away in (("d_home", "d_away"), ("score_home", "score_away"),
                                   ("home_available", "away_available")):
                    np.testing.assert_equal(a[home], b[away])
                    np.testing.assert_equal(a[away], b[home])

    def assert_unavailable(self, evidence, side):
        self.assertFalse(evidence[side + "_available"])
        self.assertTrue(math.isnan(evidence["d_" + side]))
        self.assertEqual(evidence["score_" + side], 0.0)

    def test_missing_ball_makes_both_sides_unavailable(self):
        result = control.score_frame(dict(observation(), ball=None))
        self.assertFalse(result["ball_visible"])
        for side in ("home", "away"):
            self.assert_unavailable(result, side)

    def test_one_or_both_teams_missing(self):
        for teams in ([], ["H"], ["A"]):
            with self.subTest(teams=teams):
                obs = dict(observation(), players=[player(t, 10, 10) for t in teams])
                result = control.score_frame(obs)
                self.assertTrue(result["ball_visible"])
                for team, side in (("H", "home"), ("A", "away")):
                    if team in teams:
                        self.assertTrue(result[side + "_available"])
                        self.assertEqual(result["d_" + side], 0)
                        self.assertEqual(result["score_" + side], 1)
                    else:
                        self.assert_unavailable(result, side)

    def test_partial_or_nonfinite_player_coordinates_are_not_observations(self):
        for coordinate in ("x_m", "y_m"):
            for value in (None, math.nan, math.inf, -math.inf):
                with self.subTest(coordinate=coordinate, value=value):
                    obs = observation()
                    obs["players"] = obs["players"][:2]
                    obs["players"][0][coordinate] = value
                    result = control.score_frame(obs)
                    self.assert_unavailable(result, "home")
                    self.assertTrue(result["away_available"])

    def test_partial_or_nonfinite_ball_coordinates_are_not_visible(self):
        for coordinate in ("x_m", "y_m"):
            for value in (None, math.nan, math.inf, -math.inf):
                with self.subTest(coordinate=coordinate, value=value):
                    obs = observation()
                    obs["ball"][coordinate] = value
                    result = control.score_frame(obs)
                    self.assertFalse(result["ball_visible"])
                    self.assert_unavailable(result, "home")
                    self.assert_unavailable(result, "away")

    def test_missing_speed_does_not_hide_valid_position(self):
        obs = observation()
        result = control.score_frame(obs)
        self.assertTrue(all(p["speed_mps"] is None for p in obs["players"]))
        self.assertEqual((result["d_home"], result["d_away"]), (5, 1))

    def test_unobserved_position_is_not_made_available_by_speed(self):
        obs = dict(observation(), players=[player("H", 10, 10, observed=False, speed=10),
                                           player("A", None, None, observed=False, speed=10)])
        result = control.score_frame(obs)
        self.assertTrue(result["ball_visible"])
        self.assert_unavailable(result, "home")
        self.assert_unavailable(result, "away")

    def test_available_zero_score_is_distinct_from_unavailable(self):
        obs = dict(observation(), players=[player("H", 3010, 10)])
        result = control.score_frame(obs)
        self.assertTrue(result["home_available"])
        self.assertEqual(result["d_home"], 3000)
        self.assertEqual(result["score_home"], 0.0)  # floating-point underflow
        self.assert_unavailable(result, "away")

    def test_invalid_tau_is_rejected_even_without_observations(self):
        for tau in (0, -1, math.nan, math.inf, -math.inf, None, "3"):
            with self.subTest(tau=tau), patch.object(control, "iter_tracking_frames") as read:
                calls = [lambda: control.score_frame(dict(observation(), ball=None), tau),
                         lambda: control.distance_to_score(math.inf, tau),
                         lambda: next(control.iter_control_scores(tau)),
                         lambda: control.build_evidence(tau), lambda: control.build(tau)]
                for call in calls:
                    with self.assertRaisesRegex(ValueError, "tau.*finite.*positive"):
                        call()
                read.assert_not_called()

    def test_input_is_unchanged_and_calls_have_no_memory(self):
        obs = observation()
        before = copy.deepcopy(obs)
        first = control.score_frame(obs)
        control.score_frame(dict(obs, ball=None))
        self.assertEqual(control.score_frame(obs), first)
        self.assertEqual(obs, before)
        first["score_home"] = -1
        self.assertAlmostEqual(control.score_frame(obs)["score_home"], math.exp(-5 / 3))

    def test_iterator_is_lazy_and_closes_its_m3_source(self):
        seen = []
        closed = []

        def source(**kwargs):
            try:
                for index in range(3):
                    seen.append(index)
                    yield dict(observation(), frame=index)
            finally:
                closed.append(True)

        with patch.object(control, "iter_tracking_frames", source):
            stream = control.iter_control_scores()
            self.assertEqual(seen, [])
            first = next(stream)
            self.assertEqual(seen, [0])
            second = next(stream)
            second["score_home"] = -1
            self.assertEqual(first["frame"], 0)
            self.assertEqual(second["frame"], 1)
            self.assertGreater(first["score_home"], 0)
            stream.close()
            self.assertEqual(seen, [0, 1])
            self.assertEqual(closed, [True])


class TrackingHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.paths = games.asset_paths(data_dir=self.temp.name)
        Path(self.paths["atd_meta"]).parent.mkdir()
        # Invented export structure with away first in Player order and home first in Teams.
        root = ET.Element("EPTS")
        metadata = ET.SubElement(root, "Metadata")
        teams = ET.SubElement(metadata, "Teams")
        for team in ("home-example", "away-example"):
            ET.SubElement(teams, "Team", id=team)
        players = ET.SubElement(metadata, "Players")
        for name, team in (("z", "away-example"), ("a", "home-example")):
            ET.SubElement(players, "Player", id=name, teamId=team)
        channels = ET.SubElement(metadata, "Channels")
        for channel, name, unit in (("x", "position_x", "normalized"),
                                     ("y", "position_y", "normalized"),
                                     ("s", "speed_kph", "kph")):
            definition = ET.SubElement(channels, "Channel", id=channel)
            ET.SubElement(definition, "Name").text = name
            ET.SubElement(definition, "Unit").text = unit
        links = ET.SubElement(metadata, "PlayerChannels")
        spec = ET.SubElement(ET.SubElement(root, "DataFormatSpecifications"),
                             "DataFormatSpecification", separator=":")
        ET.SubElement(spec, "StringRegister", name="frameCount")
        registers = ET.SubElement(spec, "SplitRegister", separator=";")
        for name in ("z", "a"):
            group = ET.SubElement(registers, "SplitRegister", separator=",")
            for channel in ("x", "y", "s"):
                link = name + "-" + channel
                ET.SubElement(links, "PlayerChannel", id=link, playerId=name, channelId=channel)
                ET.SubElement(group, "PlayerChannelRef", playerChannelId=link)
        ball = ET.SubElement(spec, "SplitRegister", separator=",")
        for channel in ("x", "y", "s"):
            ET.SubElement(ball, "BallChannelRef", channelId=channel)
        ET.ElementTree(root).write(self.paths["atd_meta"], encoding="utf-8")
        Path(self.paths["atd_raw"]).write_text(
            "1:0.5,0.6,36;0.6,0.5,NaN:0.5,0.5,0\n"
            "2:NaN,0.6,36;0.5,0.5,NaN:0.5,0.5,0\n"
            "3:0.5,0.5,36;0.6,0.5,0:0.5,NaN,0\n", encoding="utf-8")
        self.config = patch.dict(games.SOURCES["tactical"], n_video_frames=3)
        self.config.start()
        self.addCleanup(self.config.stop)

    def test_actual_corrected_m3_to_m1_handoff(self):
        observations = list(tracking.iter_tracking_frames(data_dir=self.temp.name))
        before = copy.deepcopy(observations)
        self.assertAlmostEqual(observations[0]["players"][0]["speed_mps"], 10)
        self.assertIsNone(observations[0]["players"][1]["speed_mps"])
        evidence = list(control.iter_control_scores(data_dir=self.temp.name))
        self.assertEqual([e["frame"] for e in evidence], [0, 1, 2])
        self.assertAlmostEqual(evidence[0]["d_home"], 10.53)
        self.assertAlmostEqual(evidence[0]["d_away"], 6.8)
        self.assertAlmostEqual(evidence[0]["score_home"], math.exp(-10.53 / 3))
        self.assertAlmostEqual(evidence[0]["score_away"], math.exp(-6.8 / 3))
        self.assertTrue(evidence[1]["home_available"])
        self.assertFalse(evidence[1]["away_available"])
        self.assertEqual(evidence[1]["score_home"], 1)
        self.assertIsNone(observations[2]["ball"])
        self.assertFalse(evidence[2]["ball_visible"])
        for obs in observations:
            control.score_frame(obs)
        self.assertEqual(observations, before)

    def test_named_arrays_and_legacy_build_are_consistent(self):
        evidence = control.build_evidence(data_dir=self.temp.name)
        legacy = control.build(data_dir=self.temp.name)
        for actual, name in zip(legacy, ("ball_visible", "d_home", "d_away",
                                        "score_home", "score_away")):
            np.testing.assert_equal(actual, evidence[name])
        self.assertEqual(legacy[0].dtype, np.dtype("int8"))
        self.assertEqual(evidence["home_available"].dtype, np.dtype(bool))
        self.assertEqual(evidence["score_home"].dtype, np.dtype("float64"))
        np.testing.assert_equal(evidence["home_available"], [True, True, False])
        np.testing.assert_equal(evidence["away_available"], [True, False, False])
        self.assertTrue(math.isnan(evidence["d_away"][1]))
        self.assertEqual(evidence["score_away"][1], 0)

    def test_malformed_tracking_is_not_silently_accepted(self):
        for content in ("1:0,0,0;0,0,0:0,0,0\n",  # truncated
                        "1:0,0,0;0,0,0:0,0,0\n1:0,0,0;0,0,0:0,0,0\n"):
            with self.subTest(content=content):
                Path(self.paths["atd_raw"]).write_text(content, encoding="utf-8")
                with self.assertRaises(tracking.TrackingDataError):
                    control.build_evidence(data_dir=self.temp.name)

    def test_cli_and_rounded_diagnostics_keep_availability(self):
        out = Path(self.temp.name) / "diagnostic.csv"
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(control.main(["--data-dir", self.temp.name, "--out", str(out)]), 0)
        self.assertIn("diagnostic", stdout.getvalue())
        with out.open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]["home_available"], "1")
        self.assertEqual(rows[1]["away_available"], "0")
        self.assertEqual(rows[1]["d_away"], "")
        self.assertEqual(rows[1]["score_away"], "0.0000")
        exact = control.build_evidence(data_dir=self.temp.name)
        self.assertNotEqual(float(rows[0]["score_home"]), exact["score_home"][0])
        legacy_out = Path(self.temp.name) / "legacy.csv"
        control.write_csv(str(legacy_out), *control.build(data_dir=self.temp.name))
        self.assertEqual(len(legacy_out.read_text().splitlines()[0].split(",")), 6)

    def test_invalid_tau_and_tracking_produce_nonzero_cli_status(self):
        out = Path(self.temp.name) / "invalid.csv"
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(control.main(["--tau", "0", "--out", str(out)]), 1)
        self.assertIn("tau", stderr.getvalue())
        self.assertFalse(out.exists())
        Path(self.paths["atd_raw"]).write_text(
            "1:0,0,0;0,0,0:0,0,0\n1:0,0,0;0,0,0:0,0,0\n", encoding="utf-8")
        result = subprocess.run([sys.executable, "-m", "module1.control_scores", "--data-dir",
                                 self.temp.name, "--out", str(out)],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("record 2", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
