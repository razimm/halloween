"""Isolated, short servo movements on GPIO18; no show or fog integration."""
import time
import signal

from tools.servo_pwm import HardwarePWM


PULSES = {'m': 1500, 'l': 1450, 'r': 1550}


def run(backend, ask=input, wait=time.sleep):
    backend.open()
    try:
        print('Hardware-PWM: GPIO18 / Pin 12. Hebel abnehmen, Nebeltaster frei lassen.')
        print('m = Mitte, l/r = kleine Bewegung, q = Ende; jeweils Enter.')
        print('Jeder Befehl sendet nur eine Sekunde lang PWM, danach Signal aus.')
        while True:
            command = ask('Servo> ').strip().lower()
            if command == 'q':
                return
            if command not in PULSES:
                print('Bitte m, l, r oder q eingeben.')
                continue
            width = PULSES[command]
            print(f'{width} µs für 1 Sekunde')
            try:
                backend.pulse(width)
                wait(1)
            finally:
                backend.stop()
    finally:
        backend.close()


def main():
    def terminate(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, terminate)

    try:
        run(HardwarePWM())
    except (KeyboardInterrupt, EOFError):
        print('\nServotest beendet, PWM aus.')
    except (RuntimeError, OSError) as error:
        raise SystemExit(str(error))


if __name__ == '__main__':
    main()
