"""公式MicroPython v1.27.0 assemblerでPIOを組立て、FIFO/IRQのHost動作を検証。"""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLER = ROOT / 'docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/rp2_v1_27_0.py'


class Pin:
    IN, OUT, PULL_UP = 0, 1, 2
    calls = []

    def __init__(self, number, *args, **kwargs):
        self.number = number
        self.calls.append((number, args, kwargs))


class StateMachine:
    def __init__(self, number):
        self.number = number
        self.running = False
        self.input = []
        self.output = []
        self.handler = None
        self.program = None

    def init(self, program, **kwargs):
        self.program, self.options = program, kwargs

    def active(self, value=None):
        if value is not None:
            self.running = bool(value)
        return self.running

    def irq(self, handler=None, **kwargs):
        self.handler = handler

    def rx_fifo(self):
        return len(self.input)

    def tx_fifo(self):
        return len(self.output)

    def get(self, buffer, shift):
        assert buffer is None and shift == 24
        return self.input.pop(0)

    def put(self, value):
        if len(self.output) >= 4:
            raise AssertionError('blocking FIFO put')
        self.output.append(value)


class ExternalPioTests(unittest.TestCase):
    def setUp(self):
        self.machines = {4: StateMachine(4), 5: StateMachine(5)}
        Pin.calls = []
        pio = types.SimpleNamespace(SHIFT_LEFT=0, SHIFT_RIGHT=1, JOIN_NONE=0,
                                    JOIN_RX=2, OUT_HIGH=3)
        native = types.ModuleType('_rp2')
        native.PIO = pio
        native.StateMachine = lambda number: self.machines[number]
        machine = types.SimpleNamespace(Pin=Pin, disable_irq=lambda: 0, enable_irq=lambda value: None)
        assembler_spec = importlib.util.spec_from_file_location('external_test_rp2', ASSEMBLER)
        assembler = importlib.util.module_from_spec(assembler_spec)
        with patch.dict(sys.modules, _rp2=native, micropython=types.SimpleNamespace(const=lambda value: value)):
            assembler_spec.loader.exec_module(assembler)
        module_spec = importlib.util.spec_from_file_location('external_test_pio', ROOT/'src/external_instrument_pio.py')
        self.module = importlib.util.module_from_spec(module_spec)
        with patch.dict(sys.modules, machine=machine, rp2=assembler):
            module_spec.loader.exec_module(self.module)

    def test_programs_assemble_and_fit_pio1_without_import_side_effects(self):
        self.assertEqual(Pin.calls, [])
        self.assertEqual(len(self.module._transmit[0]), 4)
        self.assertEqual(len(self.module._receive[0]), 12)
        self.assertLessEqual(len(self.module._transmit[0])+len(self.module._receive[0]), 32)
        uart = self.module.ExternalPioUART()
        self.assertEqual([number for number, _, _ in Pin.calls], [12,13])
        self.assertEqual(self.machines[4].options['freq'], 115200*8)
        self.assertTrue(self.machines[4].running)
        self.assertTrue(self.machines[5].running)
        uart.close()

    def test_existing_active_machine_is_not_reconfigured(self):
        self.machines[5].running = True
        with self.assertRaises(RuntimeError):
            self.module.ExternalPioUART()
        self.assertEqual(Pin.calls, [])
        self.assertTrue(self.machines[5].running)
        self.assertIsNone(self.machines[4].program)

    def test_tx_never_puts_beyond_fifo_capacity(self):
        uart = self.module.ExternalPioUART()
        self.assertEqual(uart.write(b'abcdef'), 4)
        self.assertEqual(uart.write(b'ef'), 0)
        self.assertEqual(self.machines[4].output, list(b'abcd'))
        self.machines[4].output.clear()
        self.assertEqual(uart.write(b'ef'), 2)
        self.assertEqual(self.machines[4].output, list(b'ef'))

    def test_rx_ring_wrap_preserves_ascii(self):
        uart = self.module.ExternalPioUART(buffer_size=256)
        for _ in range(8):
            raw = bytes(range(128))
            self.machines[5].input.extend(raw)
            uart._irq(self.machines[5])
            self.assertEqual(uart.read(256), raw)
            self.assertIsNone(uart.take_error())

    def test_overflow_and_bad_stop_discard_partial_frame(self):
        uart = self.module.ExternalPioUART(buffer_size=8)
        self.machines[5].input.extend([65]*9)
        uart._irq(self.machines[5])
        self.assertEqual(uart.take_error(), 'RX_OVERFLOW')
        self.assertEqual(uart.any(), 0)
        self.machines[5].input.extend([65,255,66])
        uart._irq(self.machines[5])
        self.assertEqual(uart.take_error(), 'UART_FRAME')
        self.assertEqual(uart.any(), 0)

    def test_close_stops_only_owned_machines(self):
        uart = self.module.ExternalPioUART()
        uart.close()
        self.assertFalse(self.machines[4].running)
        self.assertFalse(self.machines[5].running)
        self.assertIsNone(self.machines[5].handler)
        with self.assertRaises(OSError):
            uart.write(b'x')

    def test_bad_ring_limit_has_no_pin_side_effect(self):
        with self.assertRaises(ValueError):
            self.module.ExternalPioUART(buffer_size=3)
        self.assertEqual(Pin.calls, [])


if __name__ == '__main__':
    unittest.main()
