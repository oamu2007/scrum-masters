"""Invented plays and invented EPTS files only; no public ground truth."""

import copy
from dataclasses import replace
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import games
from module4 import evidence as m4
from module4.stoppages import restart_windows, side_from_team_tag
from starter.tactical_tracking import iter_tracking_frames
from test_tactical_tracking import METADATA


def observation(frame, x=52.65, y=34.0, speeds=(0.0, 0.0, 0.0)):
    ball = None if x is None else dict(x_m=x, y_m=y, x_norm=x / 105.3, y_norm=y / 68)
    players = [dict(track_slot=i + 1, team="H" if i % 2 else "A", observed=True,
                    x_m=(x if x is not None else 50) + i, y_m=y,
                    speed_mps=speed) for i, speed in enumerate(speeds)]
    return dict(frame=frame, time_s=frame / 25, ball=ball, players=players)


def window(side="H", start=0, end=90):
    return dict(type="Throw-in", start_frame=start, end_frame=end, side=side)


class EvidenceTests(unittest.TestCase):
    def producer(self, windows=(), config=None, halves=((1, 0, 99), (2, 120, 199))):
        with patch.object(m4, "half_video_blocks", return_value=halves):
            return m4.StoppageEvidence(windows, config=config)

    def paused(self, producer, start=0):
        return [producer(i, observation(i, x=-0.3)) for i in range(start, start + 16)]

    def assert_contract(self, row):
        for prefix in ("dead", "restart"):
            score, available = row[prefix + "_score"], row[prefix + "_available"]
            self.assertIs(type(available), bool)
            self.assertTrue(math.isfinite(score))
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
            if not available:
                self.assertEqual(score, 0)
        self.assertIn(row["restart_side"], ("H", "A", None))

    def test_live_pass_with_brief_ball_occlusion(self):
        producer = self.producer([window()])
        rows = [producer(i, observation(i, x=None if 6 <= i <= 8 else 30 + i * .3,
                                        speeds=(3, 4, 3))) for i in range(25)]
        self.assertTrue(all(row["dead_score"] == row["restart_score"] == 0 for row in rows))
        for row in rows[6:9]:
            self.assertFalse(row["dead_available"])
            self.assertFalse(row["restart_available"])
        self.assertTrue(rows[-1]["dead_available"])

    def test_stationary_ball_alone_is_available_weak_evidence(self):
        producer = self.producer()
        rows = [producer(i, observation(i)) for i in range(25)]
        self.assertTrue(rows[-1]["dead_available"])
        self.assertFalse(rows[-1]["restart_available"])
        self.assertTrue(all(row["dead_score"] == 0 for row in rows))

    def test_tagged_interior_pause_is_only_weak_context(self):
        producer = self.producer([window()])
        rows = [producer(i, observation(i)) for i in range(25)]
        self.assertAlmostEqual(rows[-1]["dead_score"], .15)
        self.assertFalse(rows[-1]["restart_available"])

    def test_boundary_pause_then_supported_restart_inside_window(self):
        producer = self.producer([window("A")])
        rows = self.paused(producer)
        self.assertEqual(rows[0]["dead_score"], 0)
        self.assertAlmostEqual(rows[-1]["dead_score"], .8)
        row = producer(16, observation(16, x=2, speeds=(3, 3, 3)))
        self.assertEqual(row["dead_score"], 0)
        self.assertTrue(row["restart_available"])
        self.assertAlmostEqual(row["restart_score"], .9)
        self.assertEqual(row["restart_side"], "A")
        self.assertLess(16, 90)  # restart is detected before tag expiry

    def test_boundary_restart_without_tag_has_unknown_side(self):
        producer = self.producer()
        self.paused(producer)
        row = producer(16, observation(16, x=2, speeds=(3, 3, 3)))
        self.assertGreater(row["restart_score"], .7)
        self.assertIsNone(row["restart_side"])

    def test_known_unknown_and_conflicting_sides(self):
        for windows, expected in (([window("H")], "H"), ([window("A")], "A"),
                                  ([window(None)], None),
                                  ([window("H"), window("A")], None),
                                  ([window("H"), window(None)], None)):
            with self.subTest(windows=windows):
                producer = self.producer(windows)
                self.paused(producer)
                row = producer(16, observation(16, x=2, speeds=(3, 3, 3)))
                self.assertGreater(row["restart_score"], 0)
                self.assertEqual(row["restart_side"], expected)

    def test_half_open_tag_endpoints_and_side_alone(self):
        producer = self.producer([window(start=2, end=4), window("A", start=6, end=6)])
        rows = [producer(i, observation(i, x=None)) for i in range(7)]
        self.assertEqual([row["restart_side"] for row in rows], [None, None, "H", "H", None, None, None])
        self.assertTrue(all(not row["restart_available"] and row["restart_score"] == 0 for row in rows))

    def test_window_end_does_not_prove_a_restart(self):
        producer = self.producer([window(end=16)])
        self.paused(producer)
        row = producer(16, observation(16, x=-0.3))
        self.assertEqual(row["restart_score"], 0)
        self.assertIsNone(row["restart_side"])
        self.assertGreater(row["dead_score"], 0)

    def test_missing_players_positions_speeds_and_negative_speeds(self):
        for mutation in (lambda o: o.update(players=[]),
                         lambda o: o["players"][0].update(x_m=None, observed=False),
                         lambda o: o["players"][0].update(y_m=float("nan")),
                         lambda o: o["players"][0].update(speed_mps=None),
                         lambda o: o["players"][0].update(speed_mps=-1),
                         lambda o: o["players"][0].update(speed_mps=float("inf"))):
            producer = self.producer([window()])
            for i in range(20):
                obs = observation(i, x=-.3)
                mutation(obs)
                row = producer(i, obs)
                self.assertFalse(row["dead_available"])
                self.assertFalse(row["restart_available"])
                self.assertEqual(row["dead_score"], 0)

    def test_partial_ball_position_stays_missing(self):
        producer = self.producer([window()])
        for i in range(20):
            obs = observation(i, x=-.3)
            obs["ball"]["y_m"] = None
            row = producer(i, obs)
            self.assertFalse(row["dead_available"])
            self.assertEqual(row["dead_score"], 0)

    def test_missing_ball_after_pause_supplies_no_positive_evidence(self):
        producer = self.producer([window()])
        self.paused(producer)
        row = producer(16, observation(16, x=None))
        self.assertEqual(row["dead_score"], 0)
        self.assertFalse(row["dead_available"])
        self.assertEqual(row["restart_score"], 0)
        self.assertFalse(row["restart_available"])

    def test_conflicting_ball_and_player_clues(self):
        producer = self.producer([window()])
        rows = [producer(i, observation(i, x=-.3, speeds=(5, 5, 5))) for i in range(20)]
        self.assertTrue(rows[-1]["dead_available"])
        self.assertTrue(all(row["dead_score"] == 0 for row in rows))
        producer = self.producer([window()])
        self.paused(producer)
        row = producer(16, observation(16, x=2, speeds=(0, 0, 0)))
        self.assertTrue(row["restart_available"])
        self.assertEqual(row["restart_score"], 0)
        self.assertEqual(row["dead_score"], 0)

    def test_one_noisy_outside_point_does_not_prove_stoppage(self):
        producer = self.producer()
        rows = [producer(i, observation(i, x=-.3 if i == 10 else 30)) for i in range(25)]
        self.assertTrue(all(row["dead_score"] == 0 for row in rows))

    def test_restart_requires_in_pitch_displacement_and_recent_pause(self):
        for x in (-1.5, -.3, .1):
            producer = self.producer()
            self.paused(producer)
            row = producer(16, observation(16, x=x, speeds=(3, 3, 3)))
            self.assertEqual(row["restart_score"], 0)
        producer = self.producer()
        rows = [producer(i, observation(i, x=20 + i, speeds=(3, 3, 3))) for i in range(20)]
        self.assertTrue(all(not row["restart_available"] for row in rows))

    def test_ball_velocity_uses_elapsed_seconds_across_missing_samples(self):
        # A shorter invented displacement gate isolates velocity: the observed
        # .32 m path spans .20 s, including two missing frames. Assuming .04 s
        # between observations would falsely exceed the 2 m/s restart gate.
        config = replace(m4.EvidenceConfig(), restart_displacement_m=.1)
        producer = self.producer(config=config)
        self.paused(producer)
        producer(16, observation(16, x=None))
        producer(17, observation(17, x=None))
        row = producer(18, observation(18, x=.02, speeds=(3, 3, 3)))
        self.assertTrue(row["restart_available"])
        self.assertEqual(row["restart_score"], 0)

    def test_short_missing_gap_does_not_invent_an_interpolated_ball(self):
        producer = self.producer()
        self.paused(producer)
        missing = producer(16, observation(16, x=None))
        self.assertFalse(missing["restart_available"])
        resumed = producer(17, observation(17, x=2, speeds=(3, 3, 3)))
        self.assertGreater(resumed["restart_score"], 0)

    def test_long_ball_gap_does_not_bridge_motion_or_pause(self):
        producer = self.producer()
        self.paused(producer)
        for i in range(16, 25):
            producer(i, observation(i, x=None))
        row = producer(25, observation(25, x=5, speeds=(3, 3, 3)))
        self.assertFalse(row["dead_available"])
        self.assertFalse(row["restart_available"])

    def test_context_expiry_and_bounded_history(self):
        # The pause context now lives pause_context_s (30 s), not 3 s. See test_stoppage_resume.py.
        producer = self.producer(halves=((1, 0, 1999),))
        self.paused(producer)
        for i in range(16, 800):                      # ball missing for about 31 s
            producer(i, observation(i, x=None))
        self.assertIsNone(producer.context)
        row = producer(800, observation(800, x=5, speeds=(3, 3, 3)))
        self.assertEqual(row["restart_score"], 0)
        for i in range(801, 900):
            producer(i, observation(i, x=5, speeds=(3, 3, 3)))
            self.assertLessEqual(len(producer.history), math.ceil(.2 * 25) + 2)

    def test_fresh_state_at_half_boundary_including_no_gap(self):
        for halves in (((1, 0, 15), (2, 16, 80)), ((1, 0, 15), (2, 25, 80))):
            producer = self.producer([window()], halves=halves)
            self.paused(producer)
            start = halves[1][1]
            for i in range(16, start):
                self.assertEqual(producer(i, observation(i, x=-.3)), m4._empty())
            fresh = self.producer([window()], halves=halves)
            for i in range(start, start + 8):
                obs = observation(i, x=2 + (i - start) * .2, speeds=(3, 3, 3))
                self.assertEqual(producer(i, obs), fresh(i, obs))

    def test_order_time_and_frame_validation(self):
        for index, obs in ((1, observation(0)), (-1, observation(-1)), (True, observation(1)),
                           (0, dict(observation(0), time_s=float("nan"))),
                           (0, dict(observation(0), time_s=.04))):
            with self.assertRaises(ValueError):
                self.producer()(index, obs)
        for bad in (0, 2):
            producer = self.producer()
            producer(0, observation(0))
            with self.assertRaisesRegex(ValueError, "ordered"):
                producer(bad, observation(bad))

    def test_ranges_immutability_export_slots_and_independent_returns(self):
        windows = [window()]
        saved_windows = copy.deepcopy(windows)
        producer = self.producer(windows)
        frames = [observation(i, x=-.3 if i < 16 else 2, speeds=(0, 0, 0) if i < 16 else (3, 3, 3))
                  for i in range(30)]
        original = copy.deepcopy(frames)
        rows = [producer(i, obs) for i, obs in enumerate(frames)]
        self.assertEqual(frames, original)
        self.assertEqual(windows, saved_windows)
        for row in rows:
            self.assert_contract(row)
        expected = copy.deepcopy(rows)
        rows[0]["dead_score"] = 999
        self.assertNotEqual(rows[1]["dead_score"], 999)
        # Reassignment of slots/teams has no effect: only current collective speeds enter.
        swapped = self.producer(windows)
        for i, obs in enumerate(copy.deepcopy(frames)):
            for p in obs["players"]:
                p["track_slot"] = 100 - p["track_slot"]
                p["team"] = "H"
            self.assertEqual(swapped(i, obs), expected[i])

    def test_configuration_rejects_invalid_values(self):
        for values in ({"pause_s": 0}, {"nearby_radius_m": float("nan")},
                       {"min_nearby_players": 2.5}, {"collective_fraction": 1.1},
                       {"min_motion_s": .4}, {"player_slow_mps": 3},
                       {"ball_slow_mps": 4}, {"boundary_dead_weight": .95}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                m4.EvidenceConfig(**values)


class TagTests(unittest.TestCase):
    def test_preserved_extractor_mapping_and_filtering(self):
        self.assertEqual(side_from_team_tag(" Barcelona "), "H")
        self.assertEqual(side_from_team_tag("ATHLETIC CLUB"), "A")
        self.assertEqual(side_from_team_tag("Atletic Club"), "A")
        self.assertIsNone(side_from_team_tag("N/A"))
        self.assertIsNone(side_from_team_tag(None))
        events = [dict(code=" set PIECES ", start_frame=3, end_frame=5,
                       tags={"Team": "N/A", "Type": "Throw-in"}),
                  dict(code="BUILD UP", start_frame=6, end_frame=9, tags={})]
        before = copy.deepcopy(events)
        self.assertEqual(restart_windows(events), [window(None, 3, 5)])
        self.assertEqual(events, before)


class TrackingHandoffTests(unittest.TestCase):
    def test_actual_m3_dictionaries_stream_arrays_and_simple_consumer(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = games.asset_paths(data_dir=folder)
            Path(paths["atd_meta"]).parent.mkdir()
            Path(paths["atd_meta"]).write_text(METADATA, encoding="utf-8")
            records = []
            for i in range(20):
                x = -.3 if i < 16 else 2 + (i - 16) * .2
                speed = 0 if i < 16 else 10.8  # raw km/h -> 3 m/s exactly once
                records.append(f"{i+1}:{x/105.3},.5,{speed};.01,.5,{speed}:{x/105.3},.5,NaN\n")
            Path(paths["atd_raw"]).write_text("".join(records), encoding="utf-8")
            config = replace(m4.EvidenceConfig(), min_nearby_players=2)
            with patch.dict(games.SOURCES["tactical"], n_video_frames=20), \
                    patch.object(m4, "half_video_blocks", return_value=[(1, 0, 19)]):
                frames = list(iter_tracking_frames(data_dir=folder))
                before = copy.deepcopy(frames)
                producer = m4.StoppageEvidence([window("A")], config=config)
                direct = [dict(frame=i, **producer(i, obs)) for i, obs in enumerate(frames)]
                rows = list(m4.iter_stoppage_evidence(data_dir=folder, windows=[window("A")], config=config))
                arrays = m4.build_evidence(data_dir=folder, windows=[window("A")], config=config)
                self.assertEqual(frames, before)
                self.assertEqual(direct, rows)
                self.assertEqual([row["frame"] for row in rows], list(range(20)))
                self.assertEqual(frames[16]["players"][0]["speed_mps"], 3)
                self.assertAlmostEqual(rows[15]["dead_score"], .8)
                self.assertAlmostEqual(rows[16]["restart_score"], .9)
                for name, array in arrays.items():
                    self.assertEqual(array.shape, (20,))
                    np.testing.assert_array_equal(array, [row[name] for row in rows])
                self.assertEqual(arrays["dead_score"].dtype, np.float64)
                self.assertEqual(arrays["restart_available"].dtype, np.bool_)
                saved = copy.deepcopy(rows)
                # A consumer uses explicit returns, with no producer/global lookup.
                restarts = [row["frame"] for row in rows
                            if row["restart_available"] and row["restart_score"] >= .7]
                self.assertIn(16, restarts)
                self.assertEqual(rows, saved)

    def test_stream_laziness_close_truncation_overflow_and_order(self):
        consumed, closed = [], []

        def source(**kwargs):
            try:
                for i in range(3):
                    consumed.append(i)
                    yield observation(i)
            finally:
                closed.append(True)

        with patch.object(m4, "iter_tracking_frames", source):
            stream = m4.iter_stoppage_evidence(windows=())
            self.assertEqual(consumed, [])
            self.assertEqual(next(stream)["frame"], 0)
            stream.close()
            self.assertEqual(consumed, [0])
            self.assertEqual(closed, [True])
        for frames, count in (([observation(0)], 2),
                              ([observation(0), observation(1)], 1),
                              ([observation(1)], 1)):
            with patch.object(m4, "iter_tracking_frames", return_value=iter(frames)), \
                    patch.object(m4, "source_frames", return_value=count), self.assertRaises(ValueError):
                list(m4.iter_stoppage_evidence(windows=()))


if __name__ == "__main__":
    unittest.main()
