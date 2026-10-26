import argparse
import array
import importlib.util
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

    def test_invalid_current_does_not_send_a_command(self):
        supply = sound_light.Supply.__new__(sound_light.Supply)
        supply.serial = Mock()
        for current in [0, -.1, .501, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                supply.current(current)
        supply.serial.write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
