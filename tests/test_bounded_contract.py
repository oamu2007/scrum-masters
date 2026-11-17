"""Bounded contract audit: invented EPTS and tags through the real pipeline.

No match labels/data, substitute decoder, parameter search or kickoff experiment.
Only fixture length/half boundaries are rebased. Production defaults are retained.
Carried forward from the previous audit; tagged interior dwell expectations are
explicitly superseded by the quality proposal (see POSSESSION_QUALITY_RESULT.md).
"""
from contextlib import ExitStack
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np

import games
from module4 import evidence as m4
from modulos import modulo2 as m2
import run_possession as rp
from starter import tactical_tracking as tracking
from test_tactical_tracking import METADATA


def hold(n, **values):
    return [dict(values) for _ in range(n)]


def move(n, *, x=2., **values):
    return [dict(values, x=x + .5 * i) for i in range(n)]


def metadata():
    root = ET.fromstring(METADATA)
    ET.SubElement(root.find('.//Players'), 'Player', id='extra-home', teamId='blue')
    group = ET.SubElement(root.find('.//DataFormatSpecification')[1],
                          'SplitRegister', separator=',')
    for channel in ('horizontal', 'vertical', 'pace'):
        identity = 'extra-' + channel
        ET.SubElement(root.find('.//PlayerChannels'), 'PlayerChannel',
                      id=identity, playerId='extra-home', channelId=channel)
        ET.SubElement(group, 'PlayerChannelRef', playerChannelId=identity)
    return ET.tostring(root, encoding='unicode')


def raw_record(index, frame):
    x = frame.get('x', 40.)
    home, away = frame.get('home', 0.), frame.get('away', 10.)
    # Metadata order is away, home, extra home. Speeds are raw km/h.
    speeds = frame.get('speeds', (0., 0., 0.))
    players = []
    for distance, speed in zip((away, home, home), speeds):
        position = 'NaN,NaN' if distance is None else f'{((40. if x is None else x) + distance) / 105.3},0.5'
        players.append(position + ',' + ('NaN' if speed is None else str(speed * 3.6)))
    ball = 'NaN,NaN,NaN' if x is None else f'{x / 105.3},0.5,NaN'
    return f'{index + 1}:{";".join(players)}:{ball}\n'


class BoundedContractTests(unittest.TestCase):
    def run_pipeline(self, frames, windows=(), blocks=None):
        n = len(frames)
        blocks = [(1, 0, n - 1)] if blocks is None else blocks
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
            paths = games.asset_paths(data_dir=folder)
            Path(paths['atd_meta']).parent.mkdir()
            Path(paths['atd_meta']).write_text(metadata(), encoding='utf-8')
            Path(paths['atd_raw']).write_text(''.join(raw_record(i, f) for i, f in enumerate(frames)), encoding='utf-8')
            tags = ET.Element('file')
            for start, end, side in windows:
                event = ET.SubElement(tags, 'instance')
                for key, value in [('code', 'SET PIECES'), ('start', start / 25), ('end', end / 25)]:
                    ET.SubElement(event, key).text = str(value)
                for key, value in [('Type', 'Free Kick'), ('Team', {'H': 'Barcelona', 'A': 'Atletic Club', None: 'N/A'}[side])]:
                    label = ET.SubElement(event, 'label')
                    ET.SubElement(label, 'group').text = key
                    ET.SubElement(label, 'text').text = value
            Path(paths['smart_tagging']).write_text(ET.tostring(tags, encoding='unicode'), encoding='utf-8')
            for module in (rp, tracking, m4):
                stack.enter_context(patch.object(module, 'source_frames', return_value=n))
            for module in (rp, m4):
                stack.enter_context(patch.object(module, 'half_video_blocks', return_value=blocks))

            # Observe the real producers/decoder without changing their evidence.
            original_score, original_stop, original_decode = rp.score_frame, m4.StoppageEvidence.__call__, m2.modulo2
            produced, passed = [], {}
            def score(observation, tau):
                result = original_score(observation, tau)
                produced.append((observation, dict(result)))
                return result
            def stop(instance, index, observation):
                self.assertIs(observation, produced[-1][0])
                result = original_stop(instance, index, observation)
                produced[-1][1].update(result)
                return result
            def decode(**fields):
                passed.update(fields)
                return original_decode(**fields)
            reader = stack.enter_context(patch.object(rp, 'iter_tracking_frames', wraps=rp.iter_tracking_frames))
            stack.enter_context(patch.object(rp, 'score_frame', side_effect=score))
            stack.enter_context(patch.object(m4.StoppageEvidence, '__call__', stop))
            stack.enter_context(patch.object(m2, 'modulo2', side_effect=decode))
            evidence = rp.collect_evidence(3., games.GAME, folder)
            labels = rp.decode_match(evidence, n, games.GAME)
            reader.assert_called_once_with(game=games.GAME, data_dir=folder)
            self.assertEqual(len(produced), n)
            for name in rp.FLOAT_FIELDS + rp.BOOL_FIELDS + rp.M4_FIELDS:
                np.testing.assert_equal(evidence[name], np.array([row[name] for _, row in produced]))
            for name in rp.M1_FIELDS + rp.M4_FIELDS + ('initial_dead',):
                self.assertIs(passed[name], evidence[name])
            self.assertEqual(passed['half_blocks'], blocks)
            self.assertFalse(evidence['initial_dead'].any())
            destination = Path(folder) / 'invented.csv'
            rp.write_submission(destination, labels)
            content = destination.read_bytes()
            expected = ('frame,label\n' + ''.join(f'{i},{label}\n' for i, label in enumerate(labels))).encode()
            self.assertEqual(content, expected)
            return evidence, labels, hashlib.sha256(content).hexdigest()

    def test_all_producer_fields_reach_decoder_and_repeatable_csv(self):
        frames = hold(20) + hold(25, x=-.3) + hold(8, x=None) + move(35, speeds=(3.,) * 3)
        first = self.run_pipeline(frames, [(0, 80, 'A')], [(1, 2, len(frames) - 3)])
        second = self.run_pipeline(frames, [(0, 80, 'A')], [(1, 2, len(frames) - 3)])
        self.assertEqual(first[1:], second[1:])
        self.assertIn('D', first[1])
        self.assertIn('A', first[1])
        self.assertEqual(first[1][:2] + first[1][-2:], ['X'] * 4)

    def test_unavailable_weak_tied_and_same_team_interrupt_turnover(self):
        away = dict(home=10., away=0.)
        interruptions = [dict(x=None), dict(home=None, away=0.), dict(home=10., away=None),
                         dict(home=60., away=59.), dict(home=0., away=0.), dict()]
        for interruption in interruptions:
            with self.subTest(interruption=interruption):
                frames = hold(20) + hold(11, **away) + [interruption] + hold(11, **away) + hold(1) + hold(12, **away)
                _, labels, _ = self.run_pipeline(frames)
                self.assertEqual(labels[:11], ['X'] * 11)
                self.assertEqual(labels[11:-1], ['H'] * (len(frames) - 12))
                self.assertEqual(labels[-1], 'A')

    def test_two_dead_reports_then_missing_ball_or_speed_do_not_confirm(self):
        for interruption in (dict(x=None), dict(x=-.3, speeds=(None, 0., 0.))):
            with self.subTest(interruption=interruption):
                evidence, labels, _ = self.run_pipeline(hold(14, x=-.3) + [interruption] + hold(25, x=-.3))
                self.assertTrue(np.all(evidence['dead_score'][12:14] >= .5))
                self.assertFalse(evidence['dead_available'][14])
                self.assertNotIn('D', labels[:27])
                self.assertEqual(labels[27:], ['D'] * 13)

    def test_short_restart_keeps_eligibility_but_clears_pending_side(self):
        second = 25 + 2 + 60 * 25
        frames = hold(25, x=-.3) + move(2, speeds=(3.,) * 3) + hold(60 * 25, x=None) + move(35, speeds=(3.,) * 3)
        evidence, labels, _ = self.run_pipeline(frames, [(0, 27, 'H'), (second, len(frames), 'A')])
        self.assertTrue(np.all(evidence['restart_score'][25:27] >= .5))
        self.assertEqual(labels[14:second], ['D'] * (second - 14))
        report = second + int(np.flatnonzero(evidence['restart_score'][second:] >= .5)[0])
        self.assertEqual(labels[report:report + 2], ['D', 'D'])
        self.assertEqual(labels[report + 2], 'A')

    def test_consumption_blocks_old_pause_reuse_and_new_stop_rearms(self):
        frames = hold(25, x=-.3) + move(5, speeds=(3.,) * 3) + hold(60 * 25, x=None)
        stale_start = len(frames)
        frames += move(35, speeds=(3.,) * 3)
        new_stop = len(frames)
        frames += hold(25, x=-.3) + move(35, speeds=(3.,) * 3)
        evidence, labels, _ = self.run_pipeline(frames)
        self.assertNotEqual(labels[27], 'D')
        self.assertFalse(np.any(evidence['restart_score'][30:new_stop + 25]))
        self.assertNotIn('D', labels[stale_start:new_stop])
        self.assertIn('D', labels[new_stop:new_stop + 25])
        self.assertTrue(np.any(evidence['restart_score'][new_stop + 25:] >= .5))
        self.assertEqual(labels[-1], 'H')

    def test_ball_only_restart_is_not_masked_by_missing_player_evidence(self):
        frames = hold(25, x=-.3) + hold(32 * 25, x=None) + move(35, home=None, away=None)
        evidence, labels, _ = self.run_pipeline(frames)
        strong = evidence['restart_score'] >= .5
        self.assertGreaterEqual(int(strong.sum()), 3)
        self.assertTrue(np.all(evidence['restart_available'][strong]))
        for name in ('dead_available', 'home_available', 'away_available'):
            self.assertFalse(np.any(evidence[name][strong]))
        report = int(np.flatnonzero(strong)[0])
        self.assertEqual(labels[report + 2:], ['X'] * (len(frames) - report - 2))

    def test_available_weak_dead_evidence_and_known_side_are_not_events(self):
        # A brief tagged pause is still weak; prolonged corroborated dwell now
        # has its own positive case below instead of the old all-duration cap.
        for frames, windows, maximum in ((hold(25), [(0, 125, 'A')], .15),
                                         (hold(125, x=.2), [], .30)):
            with self.subTest(maximum=maximum):
                evidence, labels, _ = self.run_pipeline(frames, windows)
                self.assertTrue(np.any(evidence['dead_available']))
                self.assertAlmostEqual(float(max(evidence['dead_score'])), maximum)
                self.assertNotIn('D', labels)
                self.assertFalse(np.any(evidence['restart_score']))
                self.assertEqual(labels[11:], ['H'] * (len(frames) - 11))

    def test_tagged_collective_interior_dwell_is_strong_after_one_second(self):
        evidence, labels, _ = self.run_pipeline(hold(125), [(0,125,'A')])
        self.assertTrue(np.all(evidence['dead_score'][:25] <= .15))
        self.assertTrue(np.all(evidence['dead_score'][25:] >= .5))
        self.assertEqual(labels[11:27], ['H']*16)
        self.assertEqual(labels[27:], ['D']*98)
        self.assertFalse(np.any(evidence['restart_score']))

    def test_adjacent_or_separated_half_starts_clear_dead_and_eligibility(self):
        for gap in (0, 20):
            with self.subTest(gap=gap):
                second = 25 + gap
                frames = hold(25, x=-.3) + hold(gap) + move(40, speeds=(3.,) * 3)
                evidence, labels, _ = self.run_pipeline(frames, blocks=[(1, 0, 24), (2, second, len(frames) - 1)])
                fresh, fresh_labels, _ = self.run_pipeline(move(40, speeds=(3.,) * 3))
                self.assertEqual(labels[24], 'D')
                self.assertEqual(labels[25:second], ['X'] * gap)
                self.assertEqual(labels[second:], fresh_labels)
                for name in evidence:
                    np.testing.assert_equal(evidence[name][second:], fresh[name])
                self.assertFalse(np.any(evidence['restart_score'][second:]))

    def test_default_restart_paths_produce_consumer_strength_and_three_reports(self):
        for speeds in ((3.,) * 3, (0.,) * 3, (None,) * 3):
            with self.subTest(speeds=speeds):
                evidence, labels, _ = self.run_pipeline(hold(25, x=-.3) + move(35, speeds=speeds))
                positive = evidence['restart_score'] > 0
                self.assertGreaterEqual(int(positive.sum()), 3)
                self.assertTrue(np.all(evidence['restart_score'][positive] >= m2.CONFIG_M2.restart_min_score))
                report = int(np.flatnonzero(positive)[0])
                # Raw 10.8 km/h must reach M4 as 3 m/s: path A fires on
                # departure. Stationary/missing speeds require five sustain frames.
                self.assertEqual(report, 25 if speeds[0] == 3. else 30)
                self.assertEqual(labels[report:report + 2], ['D', 'D'])
                self.assertNotEqual(labels[report + 2], 'D')


if __name__ == '__main__':
    unittest.main()
