"""Invented tagged pauses through actual M1/M4, transport, M2 and CSV.

No supplied-match labels or assets. Expectations describe the proposed mechanism,
not accuracy measurements. The EPTS case also exercises the actual M3 parser.
"""
from contextlib import ExitStack
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np

import games
from module4 import evidence as m4
import run_possession as rp
from starter import tactical_tracking as m3
from test_integrated_pipeline import pipeline
from test_stoppage_m2_gate import observation
from test_tactical_tracking import METADATA


def tag(start=0, end=500, side='A'):
    return dict(type='Free Kick', start_frame=start, end_frame=end, side=side)


def quiet(n=50, x=40., jitter=0., **values):
    return [dict(x=None if x is None else x + (jitter if i % 2 else -jitter), **values) for i in range(n)]


def travel(n=35, x=40., **values):
    return [dict(x=x + .5*(i+1), **values) for i in range(n)]


class TaggedPauseQualityTests(unittest.TestCase):
    def test_interior_set_piece_enters_dead_after_dwell_and_confirmation(self):
        evidence, labels = pipeline(quiet(), [tag()])
        self.assertTrue(np.all(evidence['dead_score'][:25] < .5))
        self.assertEqual(labels[:11], ['X']*11)
        self.assertEqual(labels[11:27], ['H']*16)
        self.assertEqual(labels[27:], ['D']*23)

    def test_local_jitter_does_not_hide_supported_pause_or_resume_it(self):
        evidence, labels = pipeline(quiet(80, jitter=.2), [tag()])
        self.assertTrue(np.all(evidence['dead_score'][25:] >= .5))
        self.assertTrue(np.all(evidence['restart_score'] == 0))
        self.assertEqual(labels[27:], ['D']*53)

    def test_short_quiet_pause_is_not_enough(self):
        frames = quiet(20, jitter=.2) + travel()
        evidence, labels = pipeline(frames, [tag()])
        self.assertNotIn('D', labels)
        self.assertTrue(np.all(evidence['restart_score'] == 0))

    def test_near_threshold_dwell_pulse_does_not_confirm_dead(self):
        # The first departing point still fits the one-metre spatial envelope.
        # A sub-confirmation evidence pulse is legal, but must not label D.
        evidence, labels = pipeline(quiet(25, jitter=.2) + travel(), [tag()])
        self.assertLess(int(np.count_nonzero(evidence['dead_score'] >= .5)), 3)
        self.assertNotIn('D', labels)

    def test_tag_alone_or_quiet_alone_does_not_create_dead(self):
        for frames, windows in ((quiet(200), []), (quiet(200, x=None), [tag()]),
                                (travel(80, speeds=(0.,)*3), [tag()]),
                                (quiet(80, speeds=(3.,)*3), [tag()]),
                                (quiet(80, speeds=()), [tag()]),
                                (quiet(80, speeds=(None,)*3), [tag()])):
            with self.subTest(frames=frames[:1], windows=windows):
                evidence, labels = pipeline(frames, windows)
                self.assertNotIn('D', labels)
                self.assertTrue(np.all(evidence['restart_score'] == 0))

    def test_tag_entry_is_not_an_event_and_dwell_cannot_cross_tag_windows(self):
        _, labels = pipeline(quiet(80), [tag(start=30)])
        self.assertNotIn('D', labels[:57])
        self.assertEqual(labels[57:], ['D']*23)
        # Adjacent phases each shorter than one second cannot pool observations.
        _, labels = pipeline(quiet(48), [tag(0,24), tag(24,48)])
        self.assertNotIn('D', labels)

    def test_interruptions_require_fresh_supported_dwell(self):
        for interruption in (dict(x=None), dict(x=40., speeds=()),
                             dict(x=40., speeds=(3.,)*3), dict(x=60.)):
            frames = quiet(20) + [interruption] + quiet(35)
            evidence, labels = pipeline(frames, [tag()])
            self.assertNotIn('D', labels[:48])
            self.assertEqual(labels[48:], ['D']*8)

    def test_supported_pause_persists_after_phase_end_and_long_gap(self):
        for seconds in (32,60,120):
            frames = quiet(40, jitter=.2) + [dict(x=None)]*(25*seconds) + quiet(30, x=45., jitter=.1)
            evidence, labels = pipeline(frames, [tag(end=40)])
            self.assertTrue(all(label == 'D' for label in labels[27:]))
            self.assertFalse(np.any(evidence['restart_score']))

    def test_supported_restarts_keep_known_unknown_and_conflicting_sides(self):
        for sides, expected in ((['A'],'A'), ([None],'X'), (['A','H'],'X')):
            frames = quiet(40, jitter=.2) + travel(speeds=())
            evidence, labels = pipeline(frames, [tag(side=side) for side in sides])
            reports = np.flatnonzero(evidence['restart_score'] >= .5)
            self.assertGreaterEqual(len(reports), 3)
            first = int(reports[0])
            self.assertEqual(labels[27:first+2], ['D']*(first+2-27))
            self.assertEqual(labels[first+2:], [expected]*(len(frames)-first-2))

    def test_completed_restart_spends_phase_for_new_pause_admission(self):
        frames = quiet(40, jitter=.2) + travel(35, speeds=()) + quiet(80, x=57.5)
        evidence, labels = pipeline(frames, [tag(end=len(frames))])
        self.assertIn('D', labels[:40])
        self.assertNotIn('D', labels[75:])
        self.assertTrue(np.all(evidence['dead_score'][100:] < .5))

    def test_new_phase_can_support_a_new_stop(self):
        frames = quiet(40, jitter=.2) + travel(35, speeds=()) + quiet(80, x=57.5, jitter=.2)
        evidence, labels = pipeline(frames, [tag(0,75), tag(75,len(frames))])
        self.assertNotIn('D', labels[75:102])
        self.assertEqual(labels[102:], ['D']*(len(frames)-102))

    def test_live_boundary_drift_without_tag_remains_live(self):
        for drift in (0., .02):
            frames = [dict(x=.2, y=20+drift*i, speeds=(1.,)*3) for i in range(750)]
            evidence, labels = pipeline(frames)
            self.assertNotIn('D', labels)
            self.assertLessEqual(float(max(evidence['dead_score'])), .3)

    def test_half_reset_clears_dwell_and_consumed_phase_state(self):
        frames = quiet(20, jitter=.2) + quiet(40, jitter=.2)
        evidence, labels = pipeline(frames, [tag()], [(1,0,19),(2,20,59)])
        fresh, fresh_labels = pipeline(quiet(40, jitter=.2), [tag()])
        self.assertEqual(labels[20:], fresh_labels)
        self.assertEqual(labels[47:], ['D']*13)
        for key in evidence:
            np.testing.assert_equal(evidence[key][20:], fresh[key])

        frames = quiet(40,jitter=.2) + travel(35,speeds=()) + quiet(40,jitter=.2)
        _, labels = pipeline(frames,[tag()],[(1,0,74),(2,75,114)])
        self.assertEqual(labels[102:], ['D']*13)

    def test_kickoff_type_keeps_separate_startup_policy(self):
        windows = [dict(tag(), type='Kick Off (Start)')]*2
        evidence, labels = pipeline(quiet(80,jitter=.2), windows)
        self.assertFalse(np.any(evidence['initial_dead']))
        self.assertNotIn('D',labels)

    def test_fractional_duration_rounds_up_and_state_stays_bounded(self):
        config = replace(m4.EvidenceConfig(), tagged_pause_s=1.01)
        with patch.object(m4,'half_video_blocks',return_value=[(1,0,199)]):
            producer = m4.StoppageEvidence([tag()],config=config)
        rows = []
        for i in range(150):
            rows.append(producer(i,observation(i,x=40.+(.2 if i%2 else -.2))))
            self.assertLessEqual(len(producer.tagged_history),28)
        self.assertTrue(all(row['dead_score'] < .5 for row in rows[:26]))
        self.assertTrue(all(row['dead_score'] >= .5 for row in rows[26:]))

    def test_confinement_is_two_dimensional_and_not_cumulative_path_length(self):
        inside = [dict(x=40.+(.3 if i%2 else -.3),y=34.+(.3 if i%2 else -.3)) for i in range(60)]
        outside = [dict(x=40.+(.4 if i%2 else -.4),y=34.+(.4 if i%2 else -.4)) for i in range(60)]
        _, accepted = pipeline(inside,[tag()])
        _, rejected = pipeline(outside,[tag()])
        self.assertEqual(accepted[27:],['D']*33)
        self.assertNotIn('D',rejected)

    def test_minimum_collective_fraction_supports_default_consumer(self):
        evidence, labels = pipeline(quiet(50,jitter=.2,speeds=(0.,0.,3.)),[tag()])
        self.assertAlmostEqual(evidence['dead_score'][25], .8*2/3)
        self.assertEqual(labels[27:],['D']*23)

    def test_new_configuration_rejects_invalid_or_overlapping_scales(self):
        for values in ({'tagged_pause_s':0.}, {'tagged_pause_s':.2},
                       {'tagged_pause_span_m':float('nan')}, {'tagged_pause_span_m':2.},
                       {'tagged_pause_weight':1.1}, {'tagged_pause_weight':False}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                m4.EvidenceConfig(**values)

    def test_sparse_or_missing_player_speed_never_counts_as_collective_quiet(self):
        for speeds in ((0.,0.), (0.,0.,None), (0.,0.,-1.)):
            evidence, labels = pipeline(quiet(80, speeds=speeds), [tag()])
            self.assertNotIn('D', labels)
            self.assertFalse(np.any(evidence['dead_available']))

    def test_actual_epts_tags_transport_and_deterministic_csv(self):
        frames = quiet(40, jitter=.2) + [dict(x=None)]*12 + travel(35, speeds=(3.,)*3)
        n = len(frames)
        root = ET.fromstring(METADATA)
        ET.SubElement(root.find('.//Players'),'Player',id='extra-home',teamId='blue')
        group = ET.SubElement(root.find('.//DataFormatSpecification')[1],'SplitRegister',separator=',')
        for channel in ('horizontal','vertical','pace'):
            identity = 'extra-'+channel
            ET.SubElement(root.find('.//PlayerChannels'),'PlayerChannel',id=identity,playerId='extra-home',channelId=channel)
            ET.SubElement(group,'PlayerChannelRef',playerChannelId=identity)
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
            paths = games.asset_paths(data_dir=folder)
            Path(paths['atd_meta']).parent.mkdir()
            Path(paths['atd_meta']).write_text(ET.tostring(root,encoding='unicode'),encoding='utf-8')
            records = []
            for i, frame in enumerate(frames):
                x = frame['x']
                ball = 'NaN,NaN,NaN' if x is None else f'{x/105.3},.5,NaN'
                px = 40. if x is None else x
                speed = frame.get('speeds',(0.,)*3)[0]*3.6
                records.append(f'{i+1}:{(px+10)/105.3},.5,{speed};{px/105.3},.5,{speed};{px/105.3},.5,{speed}:{ball}\n')
            Path(paths['atd_raw']).write_text(''.join(records),encoding='utf-8')
            Path(paths['smart_tagging']).write_text(
                '<file><instance><code>SET PIECES</code><start>0</start><end>4</end>'
                '<label><group>Type</group><text>Free Kick</text></label>'
                '<label><group>Team</group><text>Atletic Club</text></label></instance></file>',encoding='utf-8')
            for module in (rp,m3,m4):
                stack.enter_context(patch.object(module,'source_frames',return_value=n))
            for module in (rp,m4):
                stack.enter_context(patch.object(module,'half_video_blocks',return_value=[(1,0,n-1)]))
            hashes = []
            for _ in range(2):
                evidence = rp.collect_evidence(3.,games.GAME,folder)
                labels = rp.decode_match(evidence,n,games.GAME)
                self.assertEqual(labels[27:52], ['D']*25)
                self.assertIn('A', labels[52:])
                output = Path(folder)/'invented.csv'
                rp.write_submission(output,labels)
                content = output.read_bytes()
                self.assertEqual(content,('frame,label\n'+''.join(f'{i},{v}\n' for i,v in enumerate(labels))).encode())
                hashes.append(hashlib.sha256(content).hexdigest())
            self.assertEqual(hashes[0],hashes[1])


class KnownTaggedPauseLimitations(unittest.TestCase):
    """Failure characterizations, not successful live-play negative controls."""

    def test_false_tag_during_live_hold_is_observationally_ambiguous(self):
        # Invented live goalkeeper/field-player hold under a false automatic
        # set-piece tag has the same available inputs as a real restart setup.
        _, labels = pipeline(quiet(60,jitter=.2),[tag()])
        self.assertEqual(labels[27:],['D']*33)  # false D under this invented interpretation

    def test_tagged_slow_drift_can_fit_the_spatial_pause_envelope(self):
        # A false/overlong phase plus 0.5 m/s live motion can also resemble setup.
        frames = [dict(x=40.+.02*i,speeds=(1.,)*3) for i in range(60)]
        _, labels = pipeline(frames,[tag()])
        self.assertEqual(labels[27:],['D']*33)


if __name__ == '__main__':
    unittest.main()
