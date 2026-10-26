#!/usr/bin/env python3
"""Build a light timeline from PCM audio; simulate by default, --play for hardware."""
import argparse
import array
import json
import math
import signal
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

PORT = '/dev/serial/by-id/usb-Nuvoton_USB_Virtual_COM_001C1A770452-if00'


def analyze(path):
    with wave.open(str(path)) as audio:
        if audio.getsampwidth() != 2 or audio.getnchannels() != 1:
            raise ValueError('Audio must be mono 16-bit PCM WAV')
        rate = audio.getframerate()
        samples = array.array('h', audio.readframes(audio.getnframes()))
    if sys.byteorder != 'little':
        samples.byteswap()
    if not samples:
        raise ValueError('Empty audio')
    hop = round(rate * .08)
    levels = []
    for pos in range(0, len(samples), hop):
        chunk = samples[pos:pos + hop]
        levels.append(math.sqrt(sum(v * v for v in chunk) / len(chunk)))
    peak = max(levels)
    active = [peak > 0 and level > peak * .08 for level in levels]
    # Bridge one short gap within a zap, without shifting its onset.
    for n in range(1, len(active) - 1):
        if active[n - 1] and active[n + 1]:
            active[n] = True
    events = []
    for n, level in enumerate(levels):
        if active[n]:
            strength = min(1, level / peak)
            current = round(.005 + .495 * strength ** .75, 3)
        else:
            current = .500
        events.append({'time_s': round(n * hop / rate, 4),
                       'current_A': current, 'zap': active[n]})
    return {'source': 'https://www.youtube.com/watch?v=Zfcaj7M0Qnk',
            'duration_s': len(samples) / rate,
            'voltage_ceiling_V': 10.0, 'max_current_A': .500,
            'events': events}


class Supply:
    def __init__(self, port):
        import serial
        self.confirmed = False
        self.serial = serial.Serial(port, 9600, timeout=.6,
                                    write_timeout=1, exclusive=True)

    def send(self, command):
        self.serial.write((command + '\n').encode('ascii'))
        self.serial.flush()

    def query(self, command):
        self.send(command)
        response = self.serial.read_until(b'\n', 128)
        if not response.endswith(b'\n'):
            raise RuntimeError(f'Incomplete response to {command}: {response!r}')
        return response[:-1]

    def enabled(self):
        response = self.query('STATUS?')
        if len(response) != 1:
            raise RuntimeError('Invalid status response')
        return bool(response[0] & 64)

    def check(self):
        voltage = float(self.query('VOUT1?'))
        current = float(self.query('IOUT1?'))
        if not 0 <= voltage <= 10.2 or not 0 <= current <= .525:
            raise RuntimeError(f'Unexpected reading: {voltage} V, {current} A')

    def current(self, current):
        if not .001 <= current <= .500:
            raise ValueError('Current outside tested range')
        self.send(f'ISET1:{current:.3f}')

    def prepare(self):
        identity = self.query('*IDN?')
        if not identity.startswith(b'KORAD KKG305P '):
            raise RuntimeError(f'Unexpected device: {identity!r}')
        self.confirmed = True
        if self.enabled():
            raise RuntimeError('Output must initially be off')
        self.send('VSET1:0.00')
        self.current(.001)
        time.sleep(.15)
        if float(self.query('VSET1?')) != 0 or float(self.query('ISET1?')) != .001:
            raise RuntimeError('Initial setpoints not confirmed')
        self.send('OUT1')
        time.sleep(.1)
        if not self.enabled():
            raise RuntimeError('Output did not enable')
        for step in range(1, 41):
            self.send(f'VSET1:{step * .25:.2f}')
            time.sleep(.04)
            self.check()
        if float(self.query('VSET1?')) != 10:
            raise RuntimeError('Voltage ceiling not confirmed')
        for step in range(1, 21):
            self.current(round(.001 + .499 * step / 20, 3))
            time.sleep(.05)
            self.check()
        if float(self.query('ISET1?')) != .500:
            raise RuntimeError('Bright setpoint not confirmed')

    def shutdown(self):
        # Attempt OFF even if a previous query failed. USB failure still requires
        # the independent physical stop; software cannot guarantee disconnection.
        if not self.confirmed:
            return
        self.send('OUT0')
        time.sleep(.4)
        self.send('VSET1:0.00')
        self.send('ISET1:0.010')
        time.sleep(.15)
        if self.enabled():
            raise RuntimeError('OUTPUT STILL REPORTED ON: switch off manually')
        print('Final:', {'output': 'off',
                         'V': float(self.query('VOUT1?')),
                         'A': float(self.query('IOUT1?')),
                         'set_V': float(self.query('VSET1?')),
                         'limit_A': float(self.query('ISET1?'))}, flush=True)


def play(args, timeline):
    if not args.audio_device:
        raise ValueError('--play requires an explicit --audio-device')
    if not 0 < args.gain <= 1:
        raise ValueError('--gain must be greater than 0 and at most 1')
    # Scale only this file, without changing mixer settings or other services.
    with tempfile.TemporaryDirectory(prefix='halloween-audio-') as directory:
        quiet = Path(directory) / 'playback.wav'
        with wave.open(str(args.audio)) as original:
            params = original.getparams()
            data = array.array('h', original.readframes(original.getnframes()))
        if sys.byteorder != 'little':
            data.byteswap()
        data = array.array('h', (round(v * args.gain) for v in data))
        if sys.byteorder != 'little':
            data.byteswap()
        with wave.open(str(quiet), 'wb') as output:
            output.setparams(params)
            output.writeframes(data.tobytes())
        supply = Supply(args.port)
        process = None
        try:
            supply.prepare()
            started = time.monotonic()
            process = subprocess.Popen(['aplay', '-q', '-D', args.audio_device,
                                        str(quiet)])
            next_check = started
            for event in timeline['events']:
                deadline = started + event['time_s'] - args.light_lead_ms / 1000
                time.sleep(max(0, deadline - time.monotonic()))
                if process.poll() not in (None, 0):
                    raise RuntimeError('Audio playback failed')
                supply.current(event['current_A'])
                if time.monotonic() >= next_check:
                    supply.check()
                    next_check = time.monotonic() + .4
            time.sleep(max(0, started + timeline['duration_s'] - time.monotonic()))
            supply.current(.500)
            if process.wait(timeout=3) != 0:
                raise RuntimeError('Audio playback failed')
            time.sleep(1)
        finally:
            try:
                supply.shutdown()
            finally:
                supply.serial.close()
                if process is not None and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path)
    parser.add_argument('--timeline', type=Path)
    parser.add_argument('--play', action='store_true')
    parser.add_argument('--port', default=PORT)
    parser.add_argument('--audio-device')
    parser.add_argument('--gain', type=float, default=.2)
    parser.add_argument('--light-lead-ms', type=float, default=0)
    args = parser.parse_args()
    timeline = analyze(args.audio)
    if args.timeline:
        args.timeline.write_text(json.dumps(timeline, indent=2) + '\n')
    print(json.dumps({key: value for key, value in timeline.items()
                      if key != 'events'}), flush=True)
    if args.play:
        def interrupt(signum, frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, interrupt)
        play(args, timeline)
    else:
        print('Simulation only: no USB access or audio playback.')


if __name__ == '__main__':
    main()
