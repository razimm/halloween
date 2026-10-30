import argparse
import array
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    'sound_light', Path(__file__).resolve().parents[1] / 'tools/sound_light.py')
sound_light = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sound_light)


class SoundLightTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.audio = Path(self.directory.name) / 'sample.wav'

    def write_audio(self, samples):
        with wave.open(str(self.audio), 'wb') as output:
            output.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            output.writeframes(array.array('h', samples).tobytes())

    def test_silence_remains_steady_bright_without_dividing_by_zero(self):
        self.write_audio([0] * 16000)
        timeline = sound_light.analyze(self.audio)
        self.assertEqual(timeline['duration_s'], 1)
        self.assertTrue(all(not event['zap'] and event['current_A'] == .5
                            for event in timeline['events']))

    def test_full_scale_audio_cannot_exceed_current_limit(self):
        self.write_audio([0] * 1600 + [32767, -32768] * 4000 + [0] * 1600)
        events = sound_light.analyze(self.audio)['events']
        self.assertTrue(any(event['zap'] for event in events))
        self.assertTrue(all(.001 <= event['current_A'] <= .5 for event in events))
        self.assertTrue(all(a['time_s'] < b['time_s']
                            for a, b in zip(events, events[1:])))

    def test_simulation_does_not_open_supply_or_start_audio(self):
        self.write_audio([0] * 1600)
        with patch('sys.argv', ['sound_light.py', str(self.audio)]), \
                patch.object(sound_light, 'Supply') as supply, \
                patch.object(sound_light.subprocess, 'Popen') as playback:
            sound_light.main()
        supply.assert_not_called()
        playback.assert_not_called()

    def test_playback_failure_still_shuts_down_and_closes_supply(self):
        self.write_audio([0] * 1600)
        supply = Mock()
        args = argparse.Namespace(audio=self.audio, audio_device='test',
                                  gain=.2, port='test', light_lead_ms=0)
        with patch.object(sound_light, 'Supply', return_value=supply), \
                patch.object(sound_light.subprocess, 'Popen',
                             side_effect=OSError('audio unavailable')):
            with self.assertRaisesRegex(OSError, 'audio unavailable'):
                sound_light.play(args, sound_light.analyze(self.audio))
        supply.shutdown.assert_called_once()
        supply.serial.close.assert_called_once()

    def test_playback_file_preserves_source_and_reuses_scaled_audio(self):
        samples = [10000, -10000, 32767, -32768]
        self.write_audio(samples)
        original = self.audio.read_bytes()
        directory = Path(self.directory.name) / 'audio' / 'playback'
        with patch.object(sound_light, 'PLAYBACK_DIR', directory):
            quiet = sound_light.playback_audio(self.audio, .2)
            self.assertEqual(quiet.parent, directory)
            with wave.open(str(quiet)) as output:
                self.assertEqual(output.getframerate(), 16000)
                scaled = array.array('h', output.readframes(output.getnframes()))
            self.assertEqual(list(scaled), [2000, -2000, 6553, -6554])
            modified = quiet.stat().st_mtime_ns
            self.assertEqual(sound_light.playback_audio(self.audio, .2), quiet)
            self.assertEqual(quiet.stat().st_mtime_ns, modified)
        self.assertEqual(self.audio.read_bytes(), original)

    def test_invalid_current_does_not_send_a_command(self):
        supply = sound_light.Supply.__new__(sound_light.Supply)
        supply.max_current = .500
        supply.serial = Mock()
        for current in [0, -.1, .501, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                supply.current(current)
        supply.serial.write.assert_not_called()

    def test_boost_preserves_duration_and_rejects_clipping(self):
        self.write_audio([10000, -10000, 19000, -19000])
        original = self.audio.read_bytes()
        with patch.object(sound_light, 'PLAYBACK_DIR', Path(self.directory.name) / 'playback'):
            boosted = sound_light.playback_audio(self.audio, 1.5)
            with wave.open(str(boosted)) as output:
                self.assertEqual(output.getnframes(), 4)
                self.assertEqual(output.getframerate(), 16000)
                samples = array.array('h', output.readframes(4))
            self.assertEqual(list(samples), [15000, -15000, 28500, -28500])
            self.assertEqual(self.audio.read_bytes(), original)
            self.write_audio([32767, -32768])
            with self.assertRaisesRegex(ValueError, 'would clip'):
                sound_light.playback_audio(self.audio, 1.5)

    def test_zap_analysis_and_supply_respect_configured_700ma_ceiling(self):
        self.write_audio([0] * 1600 + [32767, -32768] * 4000 + [0] * 1600)
        timeline = sound_light.analyze(self.audio, max_current=.700)
        self.assertEqual(timeline['max_current_A'], .700)
        self.assertEqual(max(e['current_A'] for e in timeline['events']), .700)
        self.assertTrue(all(.001 <= e['current_A'] <= .700 for e in timeline['events']))
        supply = sound_light.Supply.__new__(sound_light.Supply)
        supply.max_current = .700
        supply.serial = Mock()
        supply.current(.700)
        supply.serial.write.assert_called_once_with(b'ISET1:0.700\n')
        for value in (.701, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                supply.current(value)
        with self.assertRaises(ValueError):
            sound_light.analyze(self.audio, max_current=.701)

    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg required for MP3 integration')
    def test_mp3_simulation_decodes_and_reuses_audio_without_hardware(self):
        self.write_audio([0] * 1600 + [12000, -12000] * 4000 + [0] * 1600)
        mp3 = self.audio.with_suffix('.mp3')
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(self.audio), str(mp3)],
                       check=True, capture_output=True)
        original = mp3.read_bytes()
        directory = Path(self.directory.name) / 'playback'
        timeline_path = Path(self.directory.name) / 'timeline.json'
        with patch.object(sound_light, 'PLAYBACK_DIR', directory), \
                patch('sys.argv', ['sound_light.py', str(mp3), '--timeline',
                                   str(timeline_path)]), \
                patch.object(sound_light, 'Supply') as supply, \
                patch.object(sound_light.subprocess, 'Popen',
                             wraps=subprocess.Popen) as processes:
            sound_light.main()
            supply.assert_not_called()
            self.assertEqual(processes.call_count, 1)
            self.assertEqual(processes.call_args.args[0][0], 'ffmpeg')
            decoded = sound_light.prepare_audio(mp3)
            modified = decoded.stat().st_mtime_ns
            self.assertEqual(sound_light.prepare_audio(mp3).stat().st_mtime_ns, modified)
            timeline = sound_light.json.loads(timeline_path.read_text())
            self.assertEqual(timeline['source'], mp3.name)
            self.assertAlmostEqual(timeline['duration_s'], .7, places=2)
            self.assertTrue(any(event['zap'] for event in timeline['events']))
            self.assertTrue(all(.001 <= event['current_A'] <= .5
                                for event in timeline['events']))
            quiet = sound_light.playback_audio(decoded, .2)
            with wave.open(str(quiet)) as audio:
                self.assertAlmostEqual(audio.getnframes() / audio.getframerate(),
                                       timeline['duration_s'])
            processes.reset_mock()
            sound_light.main()
            processes.assert_not_called()
        self.assertEqual(mp3.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
