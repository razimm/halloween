import copy
import json
from pathlib import Path
import struct
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tools.show_controller import Show, STAGES, VOICES, FILES, BACKGROUND, GREEN, RED, BLACK, ZAP_UP, scaled
from tools.show_hardware import Audio, Korad, Lighting, Inputs, dmx_packet, validate_config
from tools.artnet import parse_reply
from tools.show import dispatch_events

CONFIG = json.loads((Path(__file__).resolve().parents[1] / 'config/show.json').read_text())


class ShowTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.config = copy.deepcopy(CONFIG)
        self.config['transition_s'] = 0
        self.config['zap_bell_pause_s'] = 0
        self.audio = Audio({name: dict(path=name, duration=2, gain=.3 if name == BACKGROUND else 1)
                            for name in FILES}, 'test', simulate=True,
                           clock=lambda: self.now, log=lambda *args: None)
        self.starts = []
        start = self.audio.start
        def record(name):
            self.starts.append(name)
            start(name)
        self.audio.start = record
        self.supply = Mock()
        self.lighting = Lighting(self.config['artnet'], simulate=True, log=lambda *args: None)
        self.zap = {'duration_s': 2, 'events': [{'time_s': 0, 'current_A': .1},
                               {'time_s': .08, 'current_A': .25},
                               {'time_s': .16, 'current_A': .4}]}
        self.show = Show(self.audio, self.supply, self.lighting, self.config, self.zap,
                         clock=lambda: self.now, choose=lambda choices: choices[1],
                         log=lambda *args: None, up_timeline=self.zap)
        self.show.start()

    def advance(self, seconds):
        self.now += seconds
        self.show.tick()

    def finish_show(self):
        self.show.buzzer()
        for _ in STAGES:
            self.advance(2)
        self.assertEqual(self.show.state, 'LOCKED')

    def test_complete_order_and_manual_lock_without_timer(self):
        self.assertEqual(self.starts, [BACKGROUND])
        self.assertEqual(self.lighting.value, scaled(GREEN, .05))
        self.finish_show()
        self.assertEqual(self.starts, [BACKGROUND, *STAGES])
        self.supply.off.assert_called_once_with()
        self.assertEqual(self.lighting.value, scaled(RED, .5))
        self.advance(36000)
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.show.release()
        self.assertEqual(self.show.state, 'IDLE')
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.assertEqual(self.supply.bright.call_count, 3)

    def test_finished_background_starts_after_five_seconds_and_loops_without_unlocking(self):
        self.finish_show()
        before = list(self.starts)
        bright_calls = self.supply.bright.call_count
        self.advance(4.99)
        self.assertEqual(self.starts, before)
        self.advance(.02)
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertEqual(self.lighting.value, scaled(RED, .5))
        self.assertEqual(self.supply.bright.call_count, bright_calls)
        count = self.starts.count(BACKGROUND)
        self.advance(2)
        self.assertEqual(self.starts.count(BACKGROUND), count + 1)
        self.assertEqual(self.show.state, 'LOCKED')

    def test_locked_background_yields_to_voice_and_resumes_after_full_response(self):
        self.finish_show()
        self.advance(5)
        self.show.buzzer()
        self.assertEqual(self.starts[-1], VOICES[1])
        self.advance(1)
        self.assertEqual(self.starts[-1], VOICES[1])
        self.advance(1)
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.assertEqual(self.show.state, 'LOCKED')

    def test_background_due_during_long_voice_waits_until_complete(self):
        self.finish_show()
        self.audio.tracks[VOICES[1]]['duration'] = 8
        self.advance(4)
        self.show.buzzer()
        self.advance(2)
        self.assertEqual(self.starts[-1], VOICES[1])
        self.advance(6)
        self.assertEqual(self.starts[-1], BACKGROUND)

    def test_locked_background_yields_to_power_up_and_release_keeps_loop_running(self):
        self.finish_show()
        self.advance(5)
        self.show.power()
        self.assertEqual(self.starts[-1], ZAP_UP)
        self.advance(2)
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.assertEqual(self.show.state, 'LOCKED')
        before = list(self.starts)
        self.show.release()
        self.assertEqual(self.show.state, 'IDLE')
        self.assertEqual(self.starts, before)

    def test_panic_cancels_pending_finished_background(self):
        self.finish_show()
        self.advance(4)
        self.show.panic()
        before = list(self.starts)
        self.advance(100)
        self.assertEqual(self.starts, before)
        self.assertEqual(self.show.state, 'PANIC')
        self.assertTrue(self.audio.done())

    def test_two_selects_finished_mode_from_idle_and_one_restores_idle(self):
        dispatch_events(self.show, None, [('finish', time.time())])
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertTrue(self.audio.done())
        self.assertEqual(self.lighting.value, scaled(RED, .5))
        self.supply.off.assert_called_with(fade_s=0)
        self.show.buzzer()
        self.assertEqual(self.starts[-1], VOICES[1])
        self.advance(2)
        self.show.release()
        self.assertEqual(self.show.state, 'IDLE')
        self.assertEqual(self.starts[-1], BACKGROUND)

    def test_two_aborts_main_show_sections_without_late_cues(self):
        for index in range(len(STAGES)):
            self.show.buzzer()
            self.audio.stop()
            self.show.stage = index
            self.show.begin_stage()
            self.show.finish()
            before = list(self.starts)
            self.advance(100)
            self.assertEqual(self.show.state, 'LOCKED')
            self.assertEqual(self.starts, before + [BACKGROUND])
            self.assertFalse(self.audio.done())
            self.assertIsNone(self.lighting.flashes)
            self.assertEqual(self.lighting.value, scaled(RED, .5))
            self.show.release()

    def test_two_keeps_voice_complete_and_cancels_pending_idle_release(self):
        self.finish_show()
        self.show.buzzer()
        self.show.release()
        self.assertEqual(self.show.state, 'RELEASING')
        self.show.finish()
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertTrue(self.show.voice)
        self.assertFalse(self.audio.done())
        self.advance(2)
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertEqual(self.starts[-1], VOICES[1])

    def test_two_stops_manual_power_up_and_does_not_override_panic(self):
        self.finish_show()
        self.show.power()
        self.show.finish()
        self.advance(10)
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertFalse(self.show.manual_powering)
        self.assertFalse(self.show.manual_light_on)
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.show.panic()
        self.show.finish()
        self.assertEqual(self.show.state, 'PANIC')
        self.show.release()
        self.assertEqual(self.show.state, 'IDLE')

    def test_panic_aborts_each_show_section_and_latches_until_one(self):
        self.show.buzzer()
        for name in STAGES:
            self.show.state = 'RUNNING'
            self.show.stage = STAGES.index(name)
            self.show.voice = True
            self.show.manual_powering = True
            self.show.blink_started = self.now
            self.lighting.flash_at((255, 255, 255, 0), [0], self.now, 10, 0)
            self.show.panic()
            self.assertEqual(self.show.state, 'PANIC')
            self.assertTrue(self.audio.done())
            self.assertEqual(self.lighting.frame(), bytes(512))
            self.supply.bright.assert_called_with(current_A=.3)
            self.assertFalse(self.show.voice)
            self.assertFalse(self.show.manual_powering)
            self.assertIsNone(self.lighting.flashes)
            before = list(self.starts)
            self.show.buzzer()
            self.show.power()
            self.advance(10)
            self.assertEqual(self.starts, before)
            self.assertEqual(self.show.state, 'PANIC')
            self.show.release()
            self.assertEqual(self.show.state, 'IDLE')
            self.assertEqual(self.starts[-1], BACKGROUND)
            self.assertEqual(self.lighting.value, scaled(GREEN, .05))

    def test_panic_attempts_all_outputs_even_after_audio_failure(self):
        self.show.panic_audio = Mock()
        self.audio.stop = Mock(side_effect=RuntimeError('audio failure'))
        self.show.panic()
        self.show.panic_audio.assert_called_once()
        self.assertEqual(self.show.state, 'PANIC')
        self.supply.bright.assert_called_with(current_A=.3)
        self.assertEqual(self.lighting.value, BLACK)

    def test_panic_release_waits_for_heos_stop_and_discards_old_release(self):
        self.show.resume_audio = Mock(return_value=False)
        self.show.panic()
        self.show.release(pressed_at=self.show.panic_at - .1)
        self.assertFalse(self.show.panic_release_requested)
        self.show.release(pressed_at=self.show.panic_at + .1)
        self.assertEqual(self.show.state, 'PANIC')
        self.assertTrue(self.show.panic_release_requested)
        self.show.resume_audio.return_value = True
        self.advance(.02)
        self.assertEqual(self.show.state, 'IDLE')

    def test_off_has_priority_over_buzzer_release_and_heos_in_same_batch(self):
        heos = Mock()
        before = list(self.starts)
        dispatch_events(self.show, heos, ['buzzer', ('release', time.time()),
                                         ('heos', time.time()), ('panic', time.time())])
        self.assertEqual(self.show.state, 'PANIC')
        self.assertEqual(self.starts, before)
        heos.trigger.assert_not_called()
        dispatch_events(self.show, heos, [('heos', time.time())])
        heos.trigger.assert_not_called()

    def test_play_toggles_locked_lamp_with_full_up_sound_without_unlocking(self):
        self.finish_show()
        self.show.power()
        self.supply.bright.assert_called_with(current_A=.001)
        self.assertEqual(self.starts[-1], ZAP_UP)
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertEqual(self.lighting.value, scaled(RED, .5))
        for _ in range(10):
            self.show.power()
            self.show.buzzer()
        self.assertEqual(self.starts.count(ZAP_UP), 1)
        self.advance(.2)
        self.supply.current.assert_called_with(.4)
        self.advance(1.81)
        self.assertFalse(self.show.manual_powering)
        self.assertTrue(self.show.manual_light_on)
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertEqual(self.starts[-1], ZAP_UP)
        self.supply.bright.assert_called_with(fade_s=0, current_A=.3)
        self.config['transition_s'] = 2
        self.show.power()
        self.supply.off.assert_called_with(fade_s=2)
        self.assertFalse(self.show.manual_light_on)
        self.assertEqual(self.show.state, 'LOCKED')
        self.assertEqual(self.starts.count(ZAP_UP), 1)

    def test_release_during_power_up_waits_for_audio_before_background_and_buzzer(self):
        self.finish_show()
        self.show.power()
        self.advance(.2)
        self.show.release()
        self.assertEqual(self.show.state, 'RELEASING')
        self.assertEqual(self.lighting.value, scaled(GREEN, .05))
        self.advance(1.7)
        self.show.buzzer()
        self.show.power()
        self.assertEqual(self.starts[-1], ZAP_UP)
        self.advance(.11)
        self.assertEqual(self.show.state, 'IDLE')
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.assertFalse(self.show.manual_powering)
        self.supply.bright.assert_called_with(fade_s=0, current_A=.3)

    def test_play_is_ignored_during_idle_show_and_voice(self):
        self.show.power()
        self.assertEqual(self.starts, [BACKGROUND])
        self.show.buzzer()
        self.show.power()
        self.assertEqual(self.starts[-1], STAGES[0])
        for _ in STAGES:
            self.advance(2)
        self.show.buzzer()
        self.show.power()
        self.assertEqual(self.starts[-1], VOICES[1])
        self.assertNotIn(ZAP_UP, self.starts)

    def test_buzzer_and_remote_during_running_do_not_restart_or_prearm(self):
        self.show.buzzer()
        for _ in range(20):
            self.show.buzzer()
            self.show.release()
        self.assertEqual(self.starts, [BACKGROUND, STAGES[0]])
        for _ in STAGES:
            self.advance(2)
        self.assertEqual(self.show.state, 'LOCKED')

    def test_zap_fade_ends_with_sound_then_bell_plays_with_led_off(self):
        self.show.buzzer()
        self.assertEqual(self.starts[-1], 'electric-zap_break_final.mp3')
        self.advance(.2)
        self.supply.current.assert_called_once_with(.4)
        self.advance(1.3)
        self.supply.off.assert_called_once_with(fade_s=.5, deadline=2)
        self.advance(.25)
        self.supply.current.assert_called_once_with(.4)
        self.advance(.25)
        self.assertEqual(self.starts[-1], 'church_bell_final.mp3')
        self.assertEqual(self.supply.off.call_count, 2)
        self.supply.off.assert_called_with()
        self.assertEqual(self.supply.bright.call_count, 2)
        self.advance(2)
        self.assertEqual(self.starts[-1], 'michael_myers_final.mp3')
        self.assertEqual(self.supply.bright.call_count, 2)

    def test_earlier_white_flash_fades_then_one_second_pause_before_bell(self):
        self.config['zap_bell_pause_s'] = 1
        self.show.buzzer()
        self.advance(.94)
        self.assertEqual(self.lighting.value, BLACK)
        self.advance(.02)
        self.assertEqual(self.lighting.value, (255, 255, 255, 0))
        self.advance(.29)
        self.assertTrue(all(125 <= v <= 130 for v in self.lighting.value[:3]))
        self.advance(.25)
        self.assertEqual(self.lighting.value, BLACK)
        self.advance(.5)
        self.assertEqual(self.starts[-1], STAGES[0])
        self.assertEqual(self.show.state, 'RUNNING')
        self.advance(.5)
        self.show.buzzer()
        self.show.release()
        self.assertEqual(self.starts[-1], STAGES[0])
        self.advance(.5)
        self.assertEqual(self.starts[-1], 'church_bell_final.mp3')
        self.assertEqual(self.show.stage_started, 3)

    def test_locked_buzzer_random_voice_three_blinks_and_no_queue(self):
        self.finish_show()
        self.show.buzzer()
        self.assertEqual(self.starts[-1], VOICES[1])
        self.assertEqual(self.lighting.value, BLACK)
        for _ in range(100):
            self.show.buzzer()
        colors = []
        for _ in range(6):
            self.advance(.301)
            colors.append(self.lighting.value)
            self.show.buzzer()
        self.assertEqual(colors, [scaled(RED, .5), BLACK, scaled(RED, .5), BLACK,
                                  scaled(RED, .5), scaled(RED, .5)])
        self.assertEqual(self.starts.count(VOICES[1]), 1)
        self.advance(.3)
        self.assertFalse(self.show.voice)
        self.advance(100)
        self.assertEqual(self.starts.count(VOICES[1]), 1)
        self.show.buzzer()
        self.assertEqual(self.starts.count(VOICES[1]), 2)

    def test_release_mid_voice_immediately_changes_lamps_but_finishes_audio(self):
        self.finish_show()
        self.show.buzzer()
        self.advance(.1)
        self.show.release()
        self.assertEqual(self.show.state, 'RELEASING')
        self.assertEqual(self.lighting.value, scaled(GREEN, .05))
        self.assertEqual(self.supply.bright.call_count, 3)
        self.assertEqual(self.starts[-1], VOICES[1])
        for _ in range(10):
            self.show.buzzer()
            self.show.release()
        self.advance(1.8)
        self.assertEqual(self.starts[-1], VOICES[1])
        self.advance(.11)
        self.assertEqual(self.show.state, 'IDLE')
        self.assertEqual(self.starts[-1], BACKGROUND)
        self.show.buzzer()
        self.assertEqual(self.starts[-1], STAGES[0])

    def test_short_voice_still_completes_three_blinks(self):
        self.finish_show()
        for name in VOICES:
            self.audio.tracks[name]['duration'] = .1
        self.show.buzzer()
        self.advance(.11)
        self.show.buzzer()
        self.assertEqual(self.starts.count(VOICES[1]), 1)
        self.advance(2)
        self.show.buzzer()
        self.assertEqual(self.starts.count(VOICES[1]), 2)

    def test_background_loops_and_no_release_during_idle_restarts_it(self):
        self.show.release()
        self.assertEqual(self.starts, [BACKGROUND])
        self.advance(2)
        self.assertEqual(self.starts, [BACKGROUND, BACKGROUND])
        self.assertEqual(self.audio.tracks[BACKGROUND]['gain'], .3)

    def test_no_cleanup_skipped_when_audio_or_supply_fails(self):
        self.audio.stop = Mock(side_effect=RuntimeError('audio failed'))
        self.supply.close.side_effect = RuntimeError('USB failed')
        self.lighting.close = Mock()
        with self.assertRaisesRegex(RuntimeError, 'USB failed'):
            self.show.stop()
        self.supply.close.assert_called_once()
        self.lighting.close.assert_called_once()
        self.assertEqual(self.show.state, 'STOPPED')

    def test_release_fades_red_to_green_without_delaying_buzzer_readiness(self):
        self.finish_show()
        self.config['transition_s'] = 2
        self.show.release()
        self.assertEqual(self.show.state, 'IDLE')
        self.assertEqual(self.lighting.value, scaled(RED, .5))
        self.supply.bright.assert_called_with(fade_s=2, current_A=.3)
        self.advance(1)
        self.assertEqual(self.lighting.value, (64, 6, 0, 0))
        self.advance(1)
        self.assertEqual(self.lighting.value, scaled(GREEN, .05))

    def test_myers_and_voice_blinks_bypass_two_second_fades(self):
        self.config['transition_s'] = 2
        self.show.buzzer()
        self.advance(2)
        self.advance(2)
        self.advance(.2)
        self.assertIsNone(self.lighting.fade)
        self.assertNotEqual(self.lighting.value, BLACK)
        self.advance(2)
        self.advance(2)
        self.show.buzzer()
        self.assertIsNone(self.lighting.fade)
        self.advance(.301)
        self.assertEqual(self.lighting.value, scaled(RED, .5))

    def test_myers_keeps_ten_percent_minimum_and_holds_full_brightness(self):
        self.audio.tracks[STAGES[2]]['duration'] = 100
        self.show.buzzer()
        self.advance(2)
        self.advance(2)
        myers_start = self.now
        self.show.tick()
        self.assertEqual(self.lighting.value, scaled(self.config['myers_lighting']['colors'][0], .1))
        start = self.config['artnet']['start_address'] - 1
        for n, color in enumerate(self.config['myers_lighting']['colors']):
            for peak_time in (.9, 1.0, 1.1):
                self.now = myers_start + n * 8 + peak_time
                self.show.tick()
                frame = self.lighting.frame()
                self.assertEqual(frame[start:start + 7], bytes([*color, 255, 0, 0]))
                self.assertEqual(max(frame[start:start + 4]), 255)
            self.now = myers_start + n * 8 + 2
            self.show.tick()
            self.assertEqual(self.lighting.value, scaled(color, .1))


class AdapterTests(unittest.TestCase):
    def test_hama_discovery_keeps_keypad_and_consumer_control_interfaces(self):
        keyboard, mouse, consumer = Mock(), Mock(), Mock()
        for device in (keyboard, mouse, consumer):
            device.info = SimpleNamespace(vendor=1444, product=39041)
            device.read.return_value = []
        keyboard.capabilities.return_value = {1: [79, 80, 69, 28, 142]}
        mouse.capabilities.return_value = {}
        consumer.capabilities.return_value = {1: [164]}
        fake_evdev = SimpleNamespace(
            InputDevice=Mock(side_effect=[keyboard, mouse, consumer]),
            list_devices=lambda: ['keyboard', 'mouse', 'consumer'],
            ecodes=SimpleNamespace(EV_KEY=1))
        button = Mock(is_pressed=False)
        with patch.dict('sys.modules', {'evdev': fake_evdev,
                                       'gpiozero': SimpleNamespace(Button=Mock(return_value=button))}):
            inputs = Inputs(CONFIG)
            self.assertEqual(inputs.remotes, [keyboard, consumer])
            self.assertIs(inputs.remote, keyboard)
            inputs.close()
        for device in (keyboard, mouse, consumer):
            device.close.assert_called_once()
        button.close.assert_called_once()

    def test_white_zap_flash_preserves_initial_fade_and_ends_without_tail(self):
        light = Lighting(CONFIG['artnet'], simulate=True)
        light.color(GREEN)
        light.fade_to(BLACK, 2, 0)
        light.flash_at((255, 255, 255, 0), [9.2], 0, .1, 0,
                       preserve_fade=True)
        light.tick(1)
        self.assertEqual(light.value, (0, 128, 0, 0))
        light.tick(9.19)
        self.assertEqual(light.frame(), bytes(512))
        start = CONFIG['artnet']['start_address'] - 1
        light.tick(9.21)
        self.assertEqual(light.frame()[start:start + 7],
                         bytes([255, 255, 255, 0, 255, 0, 0]))
        light.tick(9.31)
        self.assertEqual(light.frame(), bytes(512))

    def test_three_bell_flashes_have_full_orange_peaks_and_no_extra_flashes(self):
        light = Lighting(CONFIG['artnet'], simulate=True)
        cfg = CONFIG['bell_lighting']
        light.flash_at(cfg['color'], cfg['gong_times_s'], 0,
                       cfg['hold_s'], cfg['fade_out_s'])
        start = CONFIG['artnet']['start_address'] - 1
        light.tick(0)
        self.assertEqual(light.frame(), bytes(512))
        for gong in cfg['gong_times_s']:
            light.tick(gong)
            self.assertEqual(light.frame()[start:start + 7],
                             bytes([255, 0, 0, 255, 255, 0, 0]))
            light.tick(gong + cfg['hold_s'] / 2)
            self.assertEqual(light.value, tuple(cfg['color']))
            light.tick(gong + cfg['hold_s'] + cfg['fade_out_s'] / 2)
            self.assertTrue(0 < light.value[0] < 255)
            light.tick(gong + cfg['hold_s'] + cfg['fade_out_s'] + .01)
            self.assertEqual(light.frame(), bytes(512))
        light.color(GREEN)
        light.tick(100)
        self.assertEqual(light.value, GREEN)

    def test_artnet_manual_clock_sends_40_frames_per_second(self):
        with patch('tools.show_hardware.socket.socket') as factory:
            light = Lighting(CONFIG['artnet'])
            for n in range(41):
                light.tick(n / 40)
            self.assertEqual(factory.return_value.sendto.call_count, 41)
            factory.return_value.close()

    def test_artnet_fade_finishes_while_controller_is_blocked(self):
        reached_target = threading.Event()
        target = (0, 26, 0, 0)
        start = CONFIG['artnet']['start_address'] - 1
        frames = []

        def receive(packet, peer):
            frames.append(packet)
            if packet[18 + start:22 + start] == bytes(target):
                reached_target.set()

        with patch('tools.show_hardware.socket.socket') as factory:
            factory.return_value.sendto.side_effect = receive
            light = Lighting(CONFIG['artnet'], threaded=True)
            try:
                light.fade_to(target, .15, time.monotonic())
                # Deliberately do not call tick(), as when serial I/O blocks.
                self.assertTrue(reached_target.wait(1), 'Independent fade did not finish')
                self.assertGreaterEqual(len(frames), 4)
            finally:
                with patch('tools.show_hardware.time.sleep'):
                    light.close()
            self.assertFalse(light.worker.is_alive())
            self.assertEqual(frames[-1][18:], bytes(512))
            factory.return_value.close.assert_called_once()

    def test_zap_fade_starts_at_last_current_and_disables_output_at_half_second(self):
        now = [0]
        with patch('tools.show_hardware.sound_light.Supply') as factory:
            supply = factory.return_value
            korad = Korad('test', clock=lambda: now[0], log=lambda *args: None)
            korad.bright()
            korad.current(.120)
            supply.send.reset_mock()
            now[0] = .1
            korad.off(fade_s=.5, deadline=.5)
            supply.send.assert_not_called()
            korad.tick(now[0])
            self.assertEqual(korad.level, .120)
            now[0] = .25
            korad.tick(now[0])
            self.assertTrue(.001 < korad.level < .120)
            supply.enabled.return_value = False
            now[0] = .5
            korad.tick(now[0])
            supply.send.assert_called_once_with('OUT0')
            self.assertFalse(korad.output_on)
            self.assertIsNone(korad.ramp)
            supply.enabled.return_value = True
            korad.bright(brightness=.3)
            self.assertEqual(korad.level, .150)

    def test_fade_retargets_from_current_color_and_can_be_cancelled(self):
        light = Lighting(CONFIG['artnet'], simulate=True)
        light.fade_to(RED, 2, 0)
        light.tick(1)
        self.assertEqual(light.value, (128, 0, 0, 0))
        light.fade_to(GREEN, 2, 1)
        light.tick(2)
        self.assertEqual(light.value, (64, 128, 0, 0))
        light.color(BLACK)
        light.tick(3)
        self.assertEqual(light.frame(), bytes(512))

    def test_korad_fade_starts_low_reaches_limit_and_zap_cancels_it(self):
        with patch('tools.show_hardware.sound_light.Supply') as factory:
            supply = factory.return_value
            korad = Korad('test', clock=lambda: 0, log=lambda *args: None)
            korad.bright(fade_s=2)
            supply.prepare.assert_called_once_with(bright_current=.001)
            korad.tick(0)
            korad.tick(1)
            korad.tick(2)
            values = [call.args[0] for call in supply.current.call_args_list]
            self.assertEqual(values, [.001, .251, .5])
            self.assertIsNone(korad.ramp)
            supply.enabled.return_value = True
            korad.bright(fade_s=2)
            korad.current(.1)
            korad.tick(1)
            supply.current.assert_called_with(.1)
            supply.enabled.return_value = False
            korad.off()
            self.assertIsNone(korad.ramp)

    def test_korad_idle_to_show_ramps_from_300_to_700_ma_without_dipping(self):
        now = [0]
        with patch('tools.show_hardware.sound_light.Supply') as factory:
            supply = factory.return_value
            supply.enabled.return_value = True
            korad = Korad('test', clock=lambda: now[0], log=lambda *args: None, max_current=.700)
            korad.bright(fade_s=2, current_A=.300)
            now[0] = 2
            korad.tick(now[0])
            self.assertEqual(korad.level, .300)
            korad.bright(fade_s=2)
            supply.current.assert_called_with(.300)
            now[0] = 3
            korad.tick(now[0])
            self.assertEqual(korad.level, .500)
            now[0] = 4
            korad.tick(now[0])
            self.assertEqual(korad.level, .700)

    def test_qa5x_7ch_uses_dimmer_without_strobe_or_macros_and_blacks_out(self):
        config = dict(CONFIG['artnet'], channel_mode=7, start_address=20)
        validate_config(dict(CONFIG, artnet=config))
        light = Lighting(config, simulate=True)
        light.color((100, 50, 20, 10))
        self.assertEqual(light.frame()[19:26], bytes([100, 50, 20, 10, 255, 0, 0]))
        light.color(BLACK)
        self.assertEqual(light.frame(), bytes(512))

    def test_artnet_packet_and_qa5x_5ch_master_dimmer(self):
        light = Lighting(dict(CONFIG['artnet'], channel_mode=5, start_address=10), simulate=True)
        light.color((100, 0, 20, 0))
        packet = dmx_packet(0x1234, 255, light.frame())
        self.assertEqual(packet[:18], b'Art-Net\0\0\x50\0\x0e\xff\0\x34\x12\x02\0')
        self.assertEqual(packet[18 + 9:18 + 14], bytes([100, 0, 20, 0, 255]))
        self.assertEqual(len(packet), 530)
        light.color(BLACK)
        self.assertEqual(light.frame(), bytes(512))

    def test_blackout_repeats_full_zero_frames_and_closes_socket(self):
        config = dict(CONFIG['artnet'], channel_mode=5)
        with patch('tools.show_hardware.socket.socket') as factory, \
                patch('tools.show_hardware.time.sleep'):
            light = Lighting(config)
            light.color((100, 0, 0, 0))
            light.tick(0)
            factory.return_value.sendto.reset_mock()
            light.close()
        factory.return_value.bind.assert_called_once_with(('', 6454))
        frames = factory.return_value.sendto.call_args_list
        self.assertEqual(len(frames), 40)
        self.assertTrue(all(call.args[0][12] == 0 and call.args[0][18:] == bytes(512)
                            for call in frames))
        factory.return_value.close.assert_called_once()

    def test_configuration_rejects_unverified_hardware_and_bad_gain(self):
        validate_config(CONFIG)
        with self.assertRaisesRegex(ValueError, 'verified'):
            validate_config(dict(CONFIG, artnet=dict(CONFIG['artnet'], confirmed=False)), True)
        for value in (0, -1, 1.01, float('nan')):
            with self.assertRaises(ValueError):
                validate_config(dict(CONFIG, background_gain=value))

    def test_audio_failure_and_overlap_are_errors(self):
        audio = Audio({}, 'test')
        audio.process = Mock()
        audio.process.poll.return_value = 1
        with self.assertRaisesRegex(RuntimeError, 'playback failed'):
            audio.done()
        audio.process.poll.return_value = None
        with self.assertRaisesRegex(RuntimeError, 'overlapping'):
            audio.start(BACKGROUND)

    def test_hama_keypad_and_play_on_separate_devices_ignore_repeats_and_numlock(self):
        inputs = Inputs.__new__(Inputs)
        inputs.button = Mock(is_pressed=False)
        inputs.remote = Mock()
        consumer = Mock()
        inputs.remotes = [inputs.remote, consumer]
        inputs.key = 79
        inputs.finish_key = 80
        inputs.power_key = 164
        inputs.panic_key = 142
        inputs.heos_key = 28
        inputs.ecodes = SimpleNamespace(EV_KEY=1)
        inputs.debounce = .05
        inputs.last_buzzer = float('-inf')
        inputs.was_pressed = False
        inputs.remote.read.return_value = [SimpleNamespace(type=1, code=code, value=value, timestamp=lambda: 123.0)
                                          for code, value in ((69, 1), (79, 0), (79, 2),
                                                              (80, 1), (79, 1), (28, 2), (28, 0), (28, 1))]
        consumer.read.return_value = [SimpleNamespace(type=1, code=164, value=value)
                                      for value in (2, 0, 1)]
        with patch('tools.show_hardware.select.select', return_value=(inputs.remotes, [], [])):
            self.assertEqual(inputs.poll(), [('finish', 123.0), ('release', 123.0), ('heos', 123.0), 'power'])

    def test_artpoll_reply_preserves_zero_based_port_address(self):
        packet = bytearray(239)
        packet[:10] = b'Art-Net\0\0\x21'
        packet[18:20] = bytes([1, 2])
        packet[26:32] = b'Port 1'
        packet[172:174] = struct.pack('>H', 1)
        packet[174] = 128
        packet[190] = 3
        reply = parse_reply(packet)
        self.assertEqual(reply['ports'][0]['output_universe'], 0x123)
        self.assertIsNone(parse_reply(b''))


if __name__ == '__main__':
    unittest.main()
