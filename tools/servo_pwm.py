"""GPIO18 / PWM0 via the Linux hardware PWM interface."""
from pathlib import Path
import time


class HardwarePWM:
    def __init__(self, root=Path('/sys/class/pwm')):
        chips = [chip for chip in root.glob('pwmchip*')
                 if (chip / 'device/of_node/compatible').exists()
                 and b'brcm,bcm2835-pwm' in
                 (chip / 'device/of_node/compatible').read_bytes().split(b'\0')]
        if len(chips) != 1:
            raise RuntimeError('Hardware-PWM fehlt oder ist nicht eindeutig. '
                               'Boot-Konfiguration für GPIO18 prüfen und Pi neu starten.')
        self.chip = chips[0]
        self.channel = self.chip / 'pwm0'
        self.owned = False

    def write(self, name, value):
        (self.channel / name).write_text(str(value))

    def open(self):
        # Refuse an already exported channel instead of taking over an actuator.
        if self.channel.exists():
            raise RuntimeError('PWM0 ist bereits belegt; kein zweiter Servotest möglich.')
        (self.chip / 'export').write_text('0')
        self.owned = True
        try:
            for _ in range(100):
                if (self.channel / 'enable').exists():
                    break
                time.sleep(.01)
            self.write('enable', 0)
            self.write('duty_cycle', 0)
            self.write('period', 20_000_000)  # 50 Hz, nanoseconds
            self.write('polarity', 'normal')
        except BaseException:
            self.close()
            raise

    def pulse(self, width_us):
        if not self.owned:
            raise RuntimeError('PWM ist nicht geöffnet')
        if type(width_us) is not int or not 1450 <= width_us <= 1550:
            raise ValueError('Servotest erlaubt nur 1450–1550 µs')
        self.write('duty_cycle', width_us * 1000)
        self.write('enable', 1)

    def stop(self):
        if self.owned:
            # Zero duty ensures no further servo pulses before disabling.
            self.write('duty_cycle', 0)
            self.write('enable', 0)

    def close(self):
        if self.owned:
            try:
                self.stop()
            finally:
                (self.chip / 'unexport').write_text('0')
                self.owned = False
