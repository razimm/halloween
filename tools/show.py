"""Full Halloween show. Simulation is the default; --play enables hardware."""
import argparse
from contextlib import ExitStack
import json
import select
import signal
import sys
import time
from pathlib import Path

from tools import sound_light
from tools.heos import Soundboard
from tools.show_controller import Show, STAGES, VOICES, ZAP, ZAP_UP
from tools.show_hardware import (ROOT, Audio, Inputs, Korad, Lighting,
                                 prepare_tracks, validate_config)


def dispatch_events(show, heos, events):
    # OFF wins the complete batch, including an already buffered release key.
    if any((e[0] if isinstance(e, tuple) else e) == 'panic' for e in events):
        show.panic()
        return
    for event in events:
        pressed_at = None
        if isinstance(event, tuple):
            event, pressed_at = event
        if event == 'buzzer':
            show.buzzer()
        elif event == 'release':
            show.release(pressed_at=pressed_at)
        elif event == 'power':
            show.power()
        elif event == 'heos' and show.state != 'PANIC':
            if heos is not None:
                heos.trigger(pressed_at=pressed_at)
            else:
                print('HEOS-Soundboard ist nicht verfügbar.')


def demo(config, tracks, zap, up):
    """Exercise the real state machine on a virtual clock, without device I/O."""
    now = [0.0]
    clock = lambda: now[0]
    audio = Audio(tracks, config['audio_device'], simulate=True, clock=clock)
    show = Show(audio, Korad('', simulate=True, clock=clock,
                             max_current=config['korad_max_current_A']),
                Lighting(config['artnet'], simulate=True), config, zap,
                clock=clock, choose=lambda voices: voices[0], up_timeline=up)
    try:
        show.start()
        show.buzzer()
        for name in STAGES:
            duration = tracks[name]['duration']
            if name == ZAP:
                duration += config['zap_bell_pause_s']
            for _ in range(round(duration / .02) + 2):
                now[0] += .02
                show.tick()
        assert show.state == 'LOCKED', show.state
        show.power()
        for _ in range(round(tracks[ZAP_UP]['duration'] / .02) + 2):
            now[0] += .02
            show.tick()
        assert show.state == 'LOCKED' and show.manual_light_on
        show.power()
        show.buzzer()
        show.buzzer()  # ignored while voice plays
        now[0] += .1
        show.tick()
        show.release()  # lamps change immediately; voice continues
        show.buzzer()  # ignored until the voice ends
        assert show.state == 'RELEASING'
        now[0] += tracks[VOICES[0]]['duration'] + .1
        show.tick()
        assert show.state == 'IDLE'
        show.panic()
        assert show.state == 'PANIC' and audio.done()
        show.buzzer()
        show.power()
        assert show.state == 'PANIC'
        show.release()
        assert show.state == 'IDLE'
        print('Demo bestanden: Show, Sperre, Freigabe und Panic-Stopp mit Rückkehr zu Idle.')
    finally:
        show.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--play', action='store_true')
    mode.add_argument('--simulate', action='store_true')
    parser.add_argument('--demo', action='store_true', help='Fast simulation on a virtual clock')
    parser.add_argument('--config', type=Path, default=ROOT / 'config/show.json')
    parser.add_argument('--background-gain', type=float,
                        help='Override background sample amplitude, e.g. 0.3 = 30%%')
    args = parser.parse_args()
    if args.demo and args.play:
        parser.error('--demo cannot be combined with --play')
    config = json.loads(args.config.read_text())
    if args.background_gain is not None:
        config['background_gain'] = args.background_gain
    validate_config(config, hardware=args.play)
    tracks = prepare_tracks(config)
    zap = sound_light.analyze(tracks[ZAP]['pcm'], config['korad_max_current_A'])
    up = sound_light.analyze(tracks[ZAP_UP]['pcm'], config['korad_max_current_A'])
    if args.demo:
        demo(config, tracks, zap, up)
        return

    def interrupt(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupt)
    simulate = not args.play
    with ExitStack() as cleanup:
        # Acquire and register each resource separately; later constructor
        # failures still close every resource already acquired.
        audio = Audio(tracks, config['audio_device'], simulate=simulate)
        cleanup.callback(audio.stop)
        heos = None
        if config.get('heos', {}).get('enabled'):
            try:
                heos = Soundboard(config['heos'], simulate=simulate)
                cleanup.callback(heos.close)
            except Exception as error:
                print(f'HEOS-Soundboard nicht verfügbar; Hauptshow läuft weiter: {error}')
        lighting = Lighting(config['artnet'], simulate=simulate, threaded=not simulate)
        cleanup.callback(lighting.close)
        inputs = None
        if not simulate:
            inputs = Inputs(config)
            cleanup.callback(inputs.close)
        supply = Korad(config['serial_port'], simulate=simulate,
                       max_current=config['korad_max_current_A'])
        cleanup.callback(supply.close)
        show = Show(audio, supply, lighting, config, zap, up_timeline=up,
                    panic_audio=heos.panic if heos else None,
                    resume_audio=heos.resume if heos else None)
        show.start()
        print('Simulation: b = Buzzer, 1 = Freigabe, p = KORAD, o = HEOS, x = PANIC (je + Enter), q = Ende'
              if simulate else 'Show bereit; Abbruch mit Strg+C.')
        while True:
            if simulate:
                events = []
                if select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline()
                    if not line or line.strip() == 'q':
                        break
                    command = line.strip()
                    if command in ('b', '1', 'p', 'o', 'x'):
                        events.append({'b': 'buzzer', '1': 'release', 'p': 'power',
                                       'o': 'heos', 'x': 'panic'}[command])
            else:
                events = inputs.poll()
            # Consume inputs before ticking audio completion: button presses
            # observed during a voice cannot become queued starts afterwards.
            dispatch_events(show, heos, events)
            show.tick()
            time.sleep(.02)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Show gestoppt.')
    except Exception as error:
        print(f'Show abgebrochen: {error}', file=sys.stderr)
        sys.exit(1)
