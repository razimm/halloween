import unittest
from unittest.mock import Mock, call
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.servo_test import run
from tools.servo_pwm import HardwarePWM


class ServoTest(unittest.TestCase):
    def test_movements_are_short_and_bounded(self):
        backend = Mock()
        wait = Mock()
        run(backend, Mock(side_effect=['m', 'l', 'r', 'q']), wait)
        self.assertEqual(backend.pulse.call_args_list, [
            call(width) for width in (1500, 1450, 1550)
        ])
        self.assertEqual(wait.call_args_list, [call(1)] * 3)
        self.assertEqual(backend.stop.call_count, 3)
        backend.close.assert_called_once_with()

    def test_no_motion_without_explicit_command(self):
        backend = Mock()
        run(backend, Mock(side_effect=['', '180', 'q']), Mock())
        backend.pulse.assert_not_called()
        backend.close.assert_called_once()

    def test_interrupt_releases_gpio(self):
        backend = Mock()
        with self.assertRaises(KeyboardInterrupt):
            run(backend, Mock(return_value='m'), Mock(side_effect=KeyboardInterrupt))
        backend.stop.assert_called_once()
        backend.close.assert_called_once()


class HardwarePWMTest(unittest.TestCase):
    def make_chip(self, root):
        chip = Path(root) / 'pwmchip3'
        node = chip / 'device/of_node'
        node.mkdir(parents=True)
        (node / 'compatible').write_bytes(b'brcm,bcm2835-pwm\0')
        return chip

    def test_refuses_missing_hardware(self):
        with TemporaryDirectory() as root:
            with self.assertRaises(RuntimeError):
                HardwarePWM(Path(root))

    def test_refuses_existing_owner(self):
        with TemporaryDirectory() as root:
            chip = self.make_chip(root)
            (chip / 'pwm0').mkdir()
            pwm = HardwarePWM(Path(root))
            with self.assertRaises(RuntimeError):
                pwm.open()
            self.assertFalse((chip / 'export').exists())

    def test_frequency_units_limits_and_cleanup(self):
        with TemporaryDirectory() as root:
            chip = self.make_chip(root)
            pwm = HardwarePWM(Path(root))
            # Emulate the sysfs channel appearing after export.
            original_write = Path.write_text

            def write(path, value, *args, **kwargs):
                result = original_write(path, value, *args, **kwargs)
                if path == chip / 'export':
                    (chip / 'pwm0').mkdir()
                    (chip / 'pwm0/enable').touch()
                return result

            from unittest.mock import patch
            with patch.object(Path, 'write_text', write):
                pwm.open()
                self.assertEqual((chip / 'pwm0/period').read_text(), '20000000')
                self.assertEqual((chip / 'pwm0/polarity').read_text(), 'normal')
                pwm.pulse(1500)
                self.assertEqual((chip / 'pwm0/duty_cycle').read_text(), '1500000')
                self.assertEqual((chip / 'pwm0/enable').read_text(), '1')
                for invalid in (1449, 1551, float('nan')):
                    with self.assertRaises(ValueError):
                        pwm.pulse(invalid)
                pwm.close()
                self.assertEqual((chip / 'pwm0/duty_cycle').read_text(), '0')
                self.assertEqual((chip / 'pwm0/enable').read_text(), '0')
                self.assertEqual((chip / 'unexport').read_text(), '0')
