"""M2 contract regressions: invented evidence, actual M1 scores and games.py blocks."""

import copy
from dataclasses import replace
import unittest
from unittest.mock import patch

import numpy as np

from games import GAME, half_video_blocks, source_frames
from module1.control_scores import score_frame
from modulos import modulo2 as decoder


def evidence(n):
    return dict(score_home=np.zeros(n), score_away=np.zeros(n),
                ball_visible=np.ones(n, dtype=bool), home_available=np.ones(n, dtype=bool),
                away_available=np.ones(n, dtype=bool), dead_score=np.zeros(n),
                dead_available=np.zeros(n, dtype=bool), restart_score=np.zeros(n),
                restart_available=np.zeros(n, dtype=bool),
                restart_side=np.full(n, None, dtype=object),
                half_blocks=[(1, 0, n - 1)] if n else [])


def proximity(home_m, away_m):
    return score_frame(dict(ball=dict(x_m=0., y_m=0.), players=[
        dict(team=team, observed=True, x_m=distance, y_m=0., speed_mps=None)
        for team, distance in (("H", home_m), ("A", away_m))]))


class DefaultControlTests(unittest.TestCase):
    def test_shipped_defaults_have_positive_credibility_and_confirmation(self):
        self.assertEqual(decoder.CONFIG_M2.min_score, .10)
        self.assertEqual(decoder.CONFIG_M2.min_margin, .05)
        self.assertEqual(decoder.CONFIG_M2.confirm_frames, 12)

    def test_negligible_and_tiny_margin_evidence_never_force_turnover_or_acquisition(self):
        k = decoder.CONFIG_M2.confirm_frames
        for home, away in ((1e-9, 2e-9), (.8, .8000000001)):
            with self.subTest(home=home, away=away):
                data = evidence(k * 4)
                data["score_home"][:] = home
                data["score_away"][:] = away
                self.assertEqual(decoder.modulo2(**data), ["X"] * (k * 4))
                data["score_home"][:k] = .9
                data["score_away"][:k] = .1
                self.assertEqual(decoder.modulo2(**data), ["X"] * (k - 1) + ["H"] * (k * 3 + 1))

    def test_actual_m1_distant_players_cannot_force_turnover(self):
        k = decoder.CONFIG_M2.confirm_frames
        data = evidence(k * 5)
        for segment, scores in ((slice(0, k), proximity(1, 8)),
                                (slice(k, k * 4), proximity(60, 59)),
                                (slice(k * 4, None), proximity(8, 1))):
            for name in ("score_home", "score_away", "ball_visible", "home_available", "away_available"):
                data[name][segment] = scores[name]
        labels = decoder.modulo2(**data)
        self.assertEqual(labels[k - 1:-1], ["H"] * (len(labels) - k))
        self.assertEqual(labels[-1], "A")
        self.assertEqual(sum(a == "H" and b == "A" for a, b in zip(labels, labels[1:])), 1)

    def test_initial_acquisition_requires_same_gates_and_confirmation_frame(self):
        k = decoder.CONFIG_M2.confirm_frames
        data = evidence(k * 2)
        data["score_home"][:k] = .099
        data["score_home"][k:] = .9
        data["score_away"][k:] = .1
        self.assertEqual(decoder.modulo2(**data), ["X"] * (k * 2 - 1) + ["H"])

    def test_interruptions_clear_pending_confirmation_but_keep_established_side(self):
        k = decoder.CONFIG_M2.confirm_frames
        for interruption in ("tie", "occlusion", "unavailable", "weak", "current"):
            with self.subTest(interruption=interruption):
                data = evidence(k * 3)
                data["score_home"][:] = .1
                data["score_away"][:] = .9
                data["score_home"][:k], data["score_away"][:k] = .9, .1
                index = k * 2 - 1
                if interruption == "tie":
                    data["score_home"][index] = data["score_away"][index] = .8
                elif interruption == "occlusion":
                    for name in ("ball_visible", "home_available", "away_available"):
                        data[name][index] = False
                    data["score_home"][index] = data["score_away"][index] = 0
                elif interruption == "unavailable":
                    data["home_available"][index] = False
                    data["score_home"][index] = 0
                elif interruption == "weak":
                    data["score_home"][index], data["score_away"][index] = 1e-9, 2e-9
                else:
                    data["score_home"][index], data["score_away"][index] = .9, .1
                labels = decoder.modulo2(**data)
                self.assertEqual(labels[k - 1:-1], ["H"] * (len(labels) - k))
                self.assertEqual(labels[-1], "A")


class HalfContractTests(unittest.TestCase):
    def test_native_games_blocks_both_and_either_half_with_exact_mask(self):
        blocks = half_video_blocks(GAME)
        self.assertEqual(blocks, [(1, 11185, 90651), (2, 110808, 190197)])
        n = source_frames("tactical", GAME)
        data = evidence(n)
        data["score_home"][:] = .9
        data["score_away"][:] = .1
        data["half_blocks"] = blocks
        full = decoder.modulo2(**data)
        mask = np.zeros(n, dtype=bool)
        for half, first, last in blocks:
            mask[first:last + 1] = True
            self.assertEqual(full[first:first + decoder.CONFIG_M2.confirm_frames - 1], ["X"] * 11)
            self.assertEqual(full[last], "H")
            alone = decoder.modulo2(**dict(data, half_blocks=[(half, first, last)]))
            self.assertEqual(full[first:last + 1], alone[first:last + 1])
            self.assertTrue(all(label == "X" for label in alone[:first] + alone[last + 1:]))
        self.assertTrue(all(label == "X" for label, valid in zip(full, mask) if not valid))
        self.assertEqual(int((~mask).sum()), 40462)
        # Fresh decode using only second-half arrays, rebased onto a local frame axis.
        half, first, last = blocks[1]
        sliced = {name: value[first:last + 1] for name, value in data.items() if name != "half_blocks"}
        fresh = decoder.modulo2(**sliced, half_blocks=[(half, 0, last - first)])
        self.assertEqual(full[first:last + 1], fresh)

    def test_adjacent_blocks_reset_dead_state_and_all_pending_counters(self):
        data = evidence(20)
        data["half_blocks"] = [(1, 0, 9), (2, 10, 19)]
        data["dead_score"][[0, 1, 2, 10, 11, 12]] = .8
        data["dead_available"][[0, 1, 2, 10, 11, 12]] = True
        data["restart_score"][[8, 9, 13, 14, 15]] = .8
        data["restart_available"][[8, 9, 13, 14, 15]] = True
        data["restart_side"][[8, 9]] = "H"  # interrupted side history must not leak
        full = decoder.modulo2(**data)
        fresh = decoder.modulo2(**dict(data, half_blocks=[(2, 10, 19)]))
        self.assertEqual(full[2:10], ["D"] * 8)
        self.assertEqual(full[10:20], fresh[10:20])
        self.assertEqual(full[10:16], ["X", "X", "D", "D", "D", "X"])

    def test_adjacent_blocks_reset_control_and_dead_candidates(self):
        for kind in ("control", "dead"):
            data = evidence(24)
            data["half_blocks"] = [(1, 0, 10), (2, 11, 23)]
            if kind == "control":
                data["score_away"][:] = .9
                labels = decoder.modulo2(**data)
                self.assertEqual(labels[:22], ["X"] * 22)
                self.assertEqual(labels[22:], ["A", "A"])
            else:
                data["dead_score"][9:12] = .8
                data["dead_available"][9:12] = True
                self.assertEqual(decoder.modulo2(**data), ["X"] * 24)

    def test_invalid_blocks_have_clear_errors(self):
        cases = [None, 1, "123", [(1,)], [(0, 2)], [(1, 0, 2, 3)], [1], [None], ["123"],
                 [(True, 0, 2)], [(0, 0, 2)], [(-1, 0, 2)], [(1.0, 0, 2)],
                 [(1, False, 2)], [(1, 0., 2)], [(1, float("nan"), 2)], [(1, 0, "2")],
                 [(1, -1, 2)], [(1, 2, 1)], [(1, 0, 3)],
                 [(1, 0, 1), (2, 1, 2)], [(2, 0, 0), (1, 1, 2)],
                 [(1, 0, 0), (1, 1, 2)], [(1, 1, 2), (2, 0, 0)]]
        for blocks in cases:
            with self.subTest(blocks=blocks), self.assertRaisesRegex(ValueError, "half_blocks"):
                decoder.modulo2(**dict(evidence(3), half_blocks=blocks))

    def test_empty_inputs_and_blocks_are_explicit(self):
        self.assertEqual(decoder.modulo2(**evidence(0)), [])
        self.assertEqual(decoder.modulo2(**dict(evidence(3), half_blocks=[])), ["X"] * 3)
        with self.assertRaisesRegex(ValueError, "half_blocks"):
            decoder.modulo2(**dict(evidence(0), half_blocks=[(1, 0, 0)]))


class ValidationTests(unittest.TestCase):
    def test_integer_scores_and_numpy_integer_blocks_and_counts_are_legal(self):
        data = evidence(15)
        data["score_away"] = np.ones(15, dtype=np.uint8)
        data["score_home"] = np.zeros(15, dtype=np.uint8)
        data["half_blocks"] = np.array([[1, 0, 14]], dtype=np.int64)
        config = replace(decoder.CONFIG_M2, confirm_frames=np.int64(12))
        self.assertEqual(decoder.modulo2(**data, config=config), ["X"] * 11 + ["A"] * 4)
        # abs(uint8(0)-uint8(1)) must be 1, not 255, at a strict margin gate of 1.
        self.assertEqual(decoder.modulo2(**data, config=replace(config, min_margin=1)), ["X"] * 15)

    def test_scalar_ragged_2d_and_mismatched_inputs_are_field_specific(self):
        for name in evidence(3):
            if name == "half_blocks":
                continue
            for value in (None, 1, [[0, 0, 0]], [0, 0], [[0], [0, 1]]):
                with self.subTest(name=name, value=value), self.assertRaisesRegex(ValueError, name):
                    decoder.modulo2(**dict(evidence(3), **{name: value}))

    def test_scores_reject_strings_complex_boolean_nonfinite_and_out_of_range(self):
        for name in ("score_home", "score_away", "dead_score", "restart_score"):
            for values in (["0.8"] * 3, [.1, "0.8", .1], [True] * 3, [.1, True, .1], [.1 + 0j] * 3,
                           [float("nan")] * 3, [float("inf")] * 3, [-.01] * 3, [1.01] * 3):
                with self.subTest(name=name, values=values), self.assertRaisesRegex(ValueError, name):
                    decoder.modulo2(**dict(evidence(3), **{name: values}))

    def test_flags_only_accept_booleans_or_numeric_zero_one(self):
        for name in ("ball_visible", "home_available", "away_available", "dead_available", "restart_available"):
            for values in (["False"] * 3, [float("nan")] * 3, [2] * 3,
                           [-1] * 3, [.5] * 3, [1j] * 3, [None] * 3):
                with self.subTest(name=name, values=values), self.assertRaisesRegex(ValueError, name):
                    decoder.modulo2(**dict(evidence(3), **{name: values}))
        data = evidence(3)
        for name in ("ball_visible", "home_available", "away_available", "dead_available", "restart_available"):
            data[name] = [0, 1., True]
        self.assertEqual(decoder.modulo2(**data), ["X"] * 3)

    def test_contradictory_availability_is_rejected_before_decoder(self):
        for name, flag in (("score_home", "home_available"), ("score_away", "away_available"),
                           ("dead_score", "dead_available"), ("restart_score", "restart_available")):
            data = evidence(3)
            data[name][:] = .8
            data[flag][:] = False
            with self.subTest(name=name), patch.object(decoder, "_decodificar_half") as decode:
                with self.assertRaisesRegex(ValueError, name):
                    decoder.modulo2(**data)
                decode.assert_not_called()
        for side in ("home_available", "away_available"):
            data = evidence(3)
            data["ball_visible"][:] = False
            data["home_available"][:] = data["away_available"][:] = False
            data[side][:] = True
            with self.subTest(side=side), self.assertRaisesRegex(ValueError, side):
                decoder.modulo2(**data)

    def test_available_zero_and_independent_restart_availability_are_legal(self):
        data = evidence(6)
        data["ball_visible"][:] = data["home_available"][:] = data["away_available"][:] = False
        data["dead_score"][:3], data["dead_available"][:3] = .8, True
        data["restart_score"][3:], data["restart_available"][3:] = .8, True
        data["restart_side"][3:] = "H"
        self.assertEqual(decoder.modulo2(**data), ["X", "X", "D", "D", "D", "H"])
        zeros = evidence(20)
        zeros["dead_available"][:] = zeros["restart_available"][:] = True
        self.assertEqual(decoder.modulo2(**zeros), ["X"] * 20)

    def test_known_side_without_restart_evidence_is_non_decisive(self):
        data = evidence(20)
        data["dead_score"][:3], data["dead_available"][:3] = .8, True
        data["restart_side"][:] = "A"
        self.assertEqual(decoder.modulo2(**data), ["X", "X"] + ["D"] * 18)
        for value in ("X", "h", "", 1, False, float("nan"), ["H"]):
            bad = np.empty(3, dtype=object)
            bad[:] = [None, value, None]
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "restart_side"):
                decoder.modulo2(**dict(evidence(3), restart_side=bad))

    def test_invalid_configuration_is_field_specific(self):
        for name in ("min_score", "min_margin", "dead_min_score", "restart_min_score"):
            for value in (float("nan"), float("inf"), -float("inf"), -.1, 1.1,
                          "0.5", None, True, 0j, [.5]):
                with self.subTest(name=name, value=value), self.assertRaisesRegex(ValueError, name):
                    decoder.modulo2(**evidence(3), config=replace(decoder.CONFIG_M2, **{name: value}))
        for name in ("confirm_frames", "dead_confirm_frames", "restart_confirm_frames"):
            for value in (0, -1, 3.0, True, np.bool_(True), "3", None, float("nan"), float("inf"), [3]):
                with self.subTest(name=name, value=value), self.assertRaisesRegex(ValueError, name):
                    decoder.modulo2(**evidence(3), config=replace(decoder.CONFIG_M2, **{name: value}))
        for value in (None, {}, 1):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "config"):
                decoder.modulo2(**evidence(3), config=value)
        with self.assertRaisesRegex(ValueError, "same_frame_priority"):
            decoder.modulo2(**evidence(3), config=replace(decoder.CONFIG_M2, same_frame_priority="unknown"))
        for name in ("dead_min_score", "restart_min_score"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, name):
                decoder.modulo2(**evidence(3), config=replace(decoder.CONFIG_M2, **{name: 0}))

    def test_decoder_does_not_mutate_input_arrays_or_blocks(self):
        data = evidence(30)
        data["score_home"][:] = .9
        data["dead_score"][15:18], data["dead_available"][15:18] = .8, True
        before = copy.deepcopy(data)
        first = decoder.modulo2(**data)
        self.assertEqual(first, decoder.modulo2(**data))
        for name in data:
            np.testing.assert_equal(data[name], before[name])


class PersistentStateTests(unittest.TestCase):
    def test_dead_state_never_expires_or_restores_a_team_from_proximity(self):
        k = decoder.CONFIG_M2.confirm_frames
        data = evidence(k + 3 + 800 + k)
        data["score_home"][:k], data["score_away"][:k] = .9, .1
        data["dead_score"][k:k + 3], data["dead_available"][k:k + 3] = .8, True
        for name in ("ball_visible", "home_available", "away_available"):
            data[name][k + 3:-k] = False
        data["score_away"][-k:] = .9
        data["restart_side"][-k:] = "A"  # side alone is still not resumption
        labels = decoder.modulo2(**data)
        self.assertEqual(labels[:k - 1], ["X"] * (k - 1))
        self.assertEqual(labels[k - 1:k + 2], ["H"] * 3)
        self.assertEqual(labels[k + 2:], ["D"] * (len(labels) - k - 2))

    def test_unknown_restart_confirmation_frame_can_begin_control_confirmation(self):
        k = decoder.CONFIG_M2.confirm_frames
        data = evidence(6 + k - 1)
        data["dead_score"][:3], data["dead_available"][:3] = .8, True
        data["restart_score"][3:6], data["restart_available"][3:6] = .8, True
        data["score_away"][5:] = .9
        labels = decoder.modulo2(**data)
        self.assertEqual(labels[:6], ["X", "X", "D", "D", "D", "X"])
        self.assertEqual(labels[-1], "A")
        self.assertTrue(all(label == "X" for label in labels[5:-1]))


if __name__ == "__main__":
    unittest.main()
