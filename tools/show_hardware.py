"""Audio, KORAD, Art-Net and physical inputs for the show controller."""
import ipaddress
import bisect
import math
import select
import socket
import struct
import subprocess
import threading
import time
import wave
from pathlib import Path

from tools import sound_light
from tools.show_controller import BACKGROUND, FILES, VOICES, BLACK

ROOT = Path(__file__).resolve().parents[1]


def validate_config(config, hardware=False):
    keys = [config['remote_release_key'], config['remote_finish_key'],
            config['remote_power_key'], config['remote_panic_key']]
    if config.get('heos', {}).get('enabled'):
        keys.append(config['remote_heos_key'])
    if len(keys) != len(set(keys)):
        raise ValueError('Hama functions must use distinct keys')
    heos = config.get('heos', {})
    if heos.get('enabled'):
        if type(heos['volume']) is not int or not 0 <= heos['volume'] <= 100:
            raise ValueError('HEOS volume must be an integer in [0, 100]')
        if not 1 <= heos['http_port'] <= 65535:
            raise ValueError('Invalid HEOS audio HTTP port')
        for name in ('host', 'advertise_host'):
            address = ipaddress.IPv4Address(heos[name])
            if address.is_unspecified or address.is_multicast:
                raise ValueError('HEOS requires unicast LAN addresses')
        if config['remote_heos_key'] in (config['remote_release_key'], config['remote_power_key']):
            raise ValueError('HEOS key must differ from release and KORAD keys')
    if not 0 < config['myers_gain'] <= 4:
        raise ValueError('myers_gain must be in (0, 4]')
    for name in ('transition_s', 'zap_fade_out_s'):
        if not math.isfinite(config[name]) or not 0 <= config[name] <= 10:
            raise ValueError(f'{name} must be in [0, 10]')
    if not math.isfinite(config['locked_background_delay_s']) or config['locked_background_delay_s'] < 0:
        raise ValueError('locked_background_delay_s must be nonnegative')
    if not 0 < config['zap_par_flash_s'] <= 1:
        raise ValueError('zap_par_flash_s must be in (0, 1]')
    for name in ('zap_par_flash_fade_s', 'zap_par_flash_advance_s', 'zap_bell_pause_s'):
        if not math.isfinite(config[name]) or not 0 <= config[name] <= 10:
            raise ValueError(f'{name} must be in [0, 10]')
    for name in ('background_gain', 'show_gain', 'bell_gain', 'laugh_gain',
                 'voice_gain', 'status_brightness',
                 'par_idle_brightness'):
        if not 0 < config[name] <= 1:
            raise ValueError(f'{name} must be in (0, 1]')
    if (not .001 <= config['korad_idle_current_A'] <= config['korad_max_current_A'] <= .700
            or config['korad_max_current_A'] < .005):
        raise ValueError('KORAD requires .001 <= idle current <= max current <= .700 A')
    for name in ('blink_half_period_s', 'buzzer_debounce_s'):
        if not 0 < config[name] <= 2:
            raise ValueError(f'{name} must be in (0, 2]')
    cfg = config['myers_lighting']
    if not 0 < cfg['brightness'] <= 1 or cfg['period_s'] < 1 or cfg['color_hold_s'] < 1:
        raise ValueError('Invalid Myers lighting settings')
    if not 0 <= cfg['minimum_brightness'] < 1:
        raise ValueError('Myers minimum_brightness must be in [0, 1)')
    if not 0 <= cfg['peak_hold_s'] < cfg['period_s']:
        raise ValueError('Myers peak_hold_s must be shorter than period_s')
    if not cfg['colors'] or any(len(c) != 4 or any(
            type(v) is not int or not 0 <= v <= 255 for v in c) for c in cfg['colors']):
        raise ValueError('Myers colors must be RGBA values in [0, 255]')
    bell = config['bell_lighting']
    times = bell['gong_times_s']
    if (len(times) != 3 or any(not math.isfinite(t) or t < 0 for t in times)
            or any(a >= b for a, b in zip(times, times[1:]))):
        raise ValueError('Bell requires three increasing nonnegative gong times')
    if not 0 < bell['hold_s'] <= 1 or not 0 < bell['fade_out_s'] <= 5:
        raise ValueError('Invalid bell flash duration')
    if len(bell['color']) != 4 or any(type(v) is not int or not 0 <= v <= 255
                                     for v in bell['color']):
        raise ValueError('Bell color must contain four RGBA values in [0, 255]')
    art = config['artnet']
    if type(art['universe']) is not int or not 0 <= art['universe'] <= 32767:
        raise ValueError('Art-Net universe must be a zero-based address in [0, 32767]')
    if art['channel_mode'] not in (4, 5, 7):
        raise ValueError('Flat Par must use Ch.04, Ch.05 or Ch.07')
    if not 1 <= art['start_address'] <= 513 - art['channel_mode']:
        raise ValueError('Invalid DMX start address')
    if hardware:
        if not art['confirmed']:
            raise ValueError('Art-Net universe, DMX address and channel mode must first '
                             'be verified; then set artnet.confirmed=true in config/show.json')
        host = ipaddress.IPv4Address(art['host'])
        if host.is_multicast or host.is_unspecified or int(host) == 0xffffffff:
            raise ValueError('Art-Net requires the node unicast IPv4 address')
        if not config['audio_device']:
            raise ValueError('An explicit ALSA audio device is required')


def prepare_tracks(config, log=print):
    """Validate/cache every file before any actor or input is opened."""
    missing = [name for name in FILES if not (ROOT / 'audio' / name).is_file()]
    if missing:
        raise FileNotFoundError('Missing audio: ' + ', '.join(missing))
    tracks = {}
    for name in FILES:
        log('Audio vorbereiten: ' + name)
        pcm = sound_light.prepare_audio(ROOT / 'audio' / name)
        with wave.open(str(pcm)) as audio:
            if audio.getsampwidth() != 2 or audio.getcomptype() != 'NONE':
                raise ValueError(f'{name}: 16-bit PCM audio required')
            duration = audio.getnframes() / audio.getframerate()
            if duration <= 0:
                raise ValueError(f'{name}: empty audio')
        gain = (config['background_gain'] if name == BACKGROUND else
                config['voice_gain'] if name in VOICES else
                config['bell_gain'] if name == 'church_bell_final.mp3' else
                config['laugh_gain'] if name == 'laughing.wav' else
                config['myers_gain'] if name == 'michael_myers_final.mp3' else
                config['show_gain'])
        tracks[name] = {'path': sound_light.playback_audio(pcm, gain),
                        'duration': duration, 'gain': gain, 'pcm': pcm}
    return tracks


class Audio:
    def __init__(self, tracks, device, simulate=False, clock=time.monotonic, log=print):
        self.tracks, self.device, self.simulate = tracks, device, simulate
        self.clock, self.log = clock, log
        self.process = None
        self.ends = None

    def start(self, name):
        if not self.done():
            raise RuntimeError('Refusing overlapping audio playback')
        track = self.tracks[name]
        self.log(f'Audio: {name} ({track["gain"]:.0%})')
        if self.simulate:
            self.ends = self.clock() + track['duration']
        else:
            self.process = subprocess.Popen(
                ['aplay', '-q', '-D', self.device, str(track['path'])])

    def done(self):
        if self.simulate:
            return self.ends is None or self.clock() >= self.ends
        if self.process is None:
            return True
        code = self.process.poll()
        if code is None:
            return False
        if code != 0:
            raise RuntimeError(f'Audio playback failed (aplay exit {code})')
        return True

    def stop(self):
        self.ends = None
        if self.process is not None:
            try:
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=3)
            finally:
                self.process = None


class Korad:
    def __init__(self, port, simulate=False, log=print, clock=time.monotonic,
                 max_current=.500):
        if not .005 <= max_current <= .700:
            raise ValueError('KORAD current limit must be in [.005, .700] A')
        self.max_current = max_current
        self.simulate, self.log = simulate, log
        self.supply = None if simulate else sound_light.Supply(port, max_current=max_current)
        self.prepared = False
        self.next_check = 0
        self.clock = clock
        self.ramp = None
        self.next_ramp = 0
        self.level = .001
        self.output_on = False
        self.off_after_ramp = False

    def bright(self, fade_s=0, brightness=1, current_A=None):
        if not 0 < brightness <= 1:
            raise ValueError('LED brightness must be in (0, 1]')
        target = (max(.001, round(self.max_current * brightness, 3))
                  if current_A is None else current_A)
        if not .001 <= target <= self.max_current:
            raise ValueError('LED current exceeds configured limit')
        self.log(f'LED: {target * 1000:.0f} mA / Spannungsgrenze 10 V')
        initial = (self.level if self.output_on else .001) if fade_s > 0 else target
        if not self.simulate:
            if not self.prepared:
                self.supply.prepare(bright_current=initial)
            else:
                self.supply.current(initial)
                self.supply.send('OUT1')
                if not self.supply.enabled():
                    raise RuntimeError('KORAD output did not enable')
        self.prepared = True
        self.off_after_ramp = False
        self.level = initial
        self.output_on = True
        self.ramp = (self.clock(), fade_s, initial, target) if fade_s > 0 else None
        self.next_ramp = 0

    def current(self, current):
        if not .001 <= current <= self.max_current:
            raise ValueError('Current exceeds configured limit')
        if not self.simulate:
            self.supply.current(current)
        self.ramp = None
        self.level = current
        self.off_after_ramp = False

    def off(self, fade_s=0, deadline=None):
        started = self.clock()
        if deadline is not None:
            fade_s = min(fade_s, max(0, deadline - started))
        if fade_s > 0 and self.output_on:
            self.ramp = (started, fade_s, self.level, .001)
            self.next_ramp = 0
            self.off_after_ramp = True
            self.log(f'LED: ausblenden über {fade_s:g} s')
            return
        self.ramp = None
        self.off_after_ramp = False
        self.output_on = False
        self.log('LED: aus')
        if not self.simulate:
            self.supply.send('OUT0')
            if self.supply.enabled():
                raise RuntimeError('KORAD output still on')

    def tick(self, now):
        if self.ramp is not None and (now >= self.next_ramp
                                     or now >= self.ramp[0] + self.ramp[1]):
            started, duration, initial, target = self.ramp
            fraction = max(0, min(1, (now - started) / duration))
            eased = fraction * fraction * (3 - 2 * fraction)
            self.level = round(initial + (target - initial) * eased, 3)
            if not self.simulate:
                self.supply.current(self.level)
            self.next_ramp = now + .08
            if fraction >= 1:
                self.ramp = None
                if self.off_after_ramp:
                    self.off()
        if self.prepared and now >= self.next_check:
            if not self.simulate:
                self.supply.check()
            self.next_check = now + .4

    def close(self):
        self.ramp = None
        self.off_after_ramp = False
        if self.supply is not None:
            try:
                self.supply.shutdown()
            finally:
                self.supply.serial.close()
        else:
            self.log('LED: aus (Simulation)')


def dmx_packet(universe, sequence, data):
    if not 0 <= universe <= 32767 or not 2 <= len(data) <= 512 or len(data) % 2:
        raise ValueError('Invalid ArtDmx frame')
    return (b'Art-Net\0' + struct.pack('<H', 0x5000) + b'\0\x0e'
            + bytes((sequence, 0)) + struct.pack('<H', universe)
            + struct.pack('>H', len(data)) + data)


class Lighting:
    FRAME_PERIOD = 1 / 40

    def __init__(self, config, simulate=False, log=print, threaded=False):
        self.config, self.simulate, self.log = config, simulate, log
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.worker = None
        self.sender_error = None
        self.socket = None if simulate else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.value = BLACK
        self.last_sent = float('-inf')
        self.sequence = 0
        self.fade = None
        self.flashes = None
        if self.socket:
            try:
                self.socket.bind(('', 6454))
                self.socket.settimeout(.2)
            except BaseException:
                self.socket.close()
                raise
            if threaded:
                self.worker = threading.Thread(target=self.send_loop,
                                               name='artnet-40hz', daemon=True)
                self.worker.start()

    def color(self, color):
        with self.lock:
            self.fade = None
            self.flashes = None
            self.value = tuple(color)

    def update_fade(self, now):
        if self.flashes is not None:
            color, times, started, hold, fade_out = self.flashes
            elapsed = now - started
            index = bisect.bisect_right(times, elapsed) - 1
            if index < 0:
                if self.fade is None:
                    self.value = BLACK
                    return
            else:
                age = elapsed - times[index]
                if fade_out == 0:
                    strength = 1 if age < hold else 0
                else:
                    fraction = max(0, min(1, (age - hold) / fade_out))
                    strength = 1 - fraction * fraction * (3 - 2 * fraction)
                self.value = tuple(round(v * strength) for v in color)
                return
        if self.fade is None:
            return
        start, target, started, duration = self.fade
        fraction = max(0, min(1, (now - started) / duration))
        eased = fraction * fraction * (3 - 2 * fraction)
        self.value = tuple(round(a + (b - a) * eased) for a, b in zip(start, target))
        if fraction >= 1:
            self.fade = None

    def fade_to(self, color, duration, now):
        with self.lock:
            self.update_fade(now)
            self.flashes = None
            if duration <= 0:
                self.color(color)
            else:
                self.fade = (self.value, tuple(color), now, duration)

    def flash_at(self, color, times, started, hold, fade_out, preserve_fade=False):
        """Schedule audio-relative flashes on the independent sender clock."""
        with self.lock:
            if not preserve_fade:
                self.fade = None
                self.value = BLACK
            self.flashes = (tuple(color), tuple(times), started, hold, fade_out)

    def frame(self):
        data = bytearray(512)
        start = self.config['start_address'] - 1
        data[start:start + 4] = bytes(self.value)
        if self.config['channel_mode'] in (5, 7) and any(self.value):
            data[start + 4] = 255
        # Ch.07 adds strobe (6) and color macros (7). Both stay at zero
        # for direct RGBA control and the current non-strobing show.
        return bytes(data)

    def tick(self, now):
        if self.sender_error is not None:
            raise RuntimeError('Art-Net sender failed') from self.sender_error
        if self.worker is None:
            with self.lock:
                self.send_frame(now)

    def send_frame(self, now, force=False):
        self.update_fade(now)
        if not force and now - self.last_sent + 1e-9 < self.FRAME_PERIOD:
            return
        self.last_sent = now
        if self.socket:
            # Sequence 0 explicitly disables resequencing, including after a
            # controller restart. Keep the standard source port stable, too.
            self.socket.sendto(dmx_packet(self.config['universe'], 0,
                                          self.frame()),
                               (self.config['host'], 6454))

    def send_loop(self):
        deadline = time.monotonic()
        try:
            while not self.stop_event.is_set():
                with self.lock:
                    self.send_frame(time.monotonic(), force=True)
                deadline += self.FRAME_PERIOD
                now = time.monotonic()
                if deadline < now:
                    # Skip missed deadlines instead of sending a packet burst.
                    deadline = now + self.FRAME_PERIOD
                self.stop_event.wait(max(0, deadline - now))
        except Exception as error:
            self.sender_error = error
            self.stop_event.set()

    def blackout_now(self):
        with self.lock:
            self.color(BLACK)
            self.send_frame(time.monotonic(), force=True)

    def close(self):
        self.stop_event.set()
        if self.worker is not None:
            self.worker.join(timeout=1)
        self.color(BLACK)
        if self.socket:
            try:
                # Explicit blackout, even if the last frame was just sent.
                for _ in range(40):
                    with self.lock:
                        self.send_frame(time.monotonic(), force=True)
                    time.sleep(self.FRAME_PERIOD)
            finally:
                self.socket.close()
        else:
            self.log('Flat Par: aus (Simulation)')


class Inputs:
    def __init__(self, config):
        # Hardware-only dependencies: simulation stays usable without them.
        from evdev import InputDevice, ecodes, list_devices
        from gpiozero import Button
        self.button = None
        self.remote = None
        self.remotes = []
        self.key = config['remote_release_key']
        self.finish_key = config['remote_finish_key']
        self.power_key = config['remote_power_key']
        self.panic_key = config['remote_panic_key']
        self.heos_key = config['remote_heos_key'] if config.get('heos', {}).get('enabled') else None
        self.ecodes = ecodes
        self.debounce = config['buzzer_debounce_s']
        self.last_buzzer = float('-inf')
        try:
            required_keys = {self.key, self.finish_key, self.power_key, self.panic_key}
            if self.heos_key is not None:
                required_keys.add(self.heos_key)
            found_keys = set()
            for path in list_devices():
                device = InputDevice(path)
                if (device.info.vendor == config['remote_vendor']
                        and device.info.product == config['remote_product']):
                    keys = set(device.capabilities().get(ecodes.EV_KEY, []))
                    matched = keys & required_keys
                    if matched:
                        # OFF emits KEY_SLEEP. Keep it away from OS sleep
                        # handling while the show owns the Hama receiver.
                        try:
                            device.grab()
                        except BaseException:
                            device.close()
                            raise
                        self.remotes.append(device)
                        found_keys.update(matched)
                        if self.key in matched:
                            self.remote = device
                        continue
                device.close()
            if found_keys != required_keys:
                raise RuntimeError('Required Hama keys (1, 2, OFF, Play/Pause, OK) not found')
            self.button = Button(config['buzzer_gpio'], pull_up=True,
                                 bounce_time=self.debounce)
            self.was_pressed = self.button.is_pressed
            # Discard key events which predate startup.
            for device in self.remotes:
                try:
                    list(device.read())
                except BlockingIOError:
                    pass
        except BaseException:
            self.close()
            raise

    def poll(self):
        events = []
        pressed = self.button.is_pressed
        now = time.monotonic()
        if pressed and not self.was_pressed and now - self.last_buzzer >= self.debounce:
            events.append('buzzer')
            self.last_buzzer = now
        self.was_pressed = pressed
        for device in select.select(self.remotes, [], [], 0)[0]:
            for event in device.read():
                # Ignore release, repeat, NumLock and every other key.
                if event.type == self.ecodes.EV_KEY and event.value == 1:
                    if event.code == self.key:
                        events.append(('release', event.timestamp()))
                    elif event.code == self.finish_key:
                        events.append(('finish', event.timestamp()))
                    elif event.code == self.panic_key:
                        events.append(('panic', event.timestamp()))
                    elif event.code == self.power_key:
                        events.append('power')
                    elif event.code == self.heos_key:
                        events.append(('heos', event.timestamp()))
        return events

    def close(self):
        if self.button is not None:
            self.button.close()
        for device in self.remotes:
            device.close()
