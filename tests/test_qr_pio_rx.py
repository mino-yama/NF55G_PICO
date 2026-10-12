"""Buffer/IRQ tests only; physical PIO sampling requires HIL."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class Pin:
    IN, OUT, PULL_UP = 0, 1, 2
    def __init__(self, *args, **kwargs):
        pass


class SM:
    def __init__(self, *args, **kwargs):
        self.fifo = []
    def irq(self, *args, **kwargs):
        pass
    def active(self, value):
        pass
    def rx_fifo(self):
        return len(self.fifo)
    def get(self, buffer, shift):
        assert buffer is None and shift == 24
        return self.fifo.pop(0)


class PioBufferTests(unittest.TestCase):
    def setUp(self):
        machine = types.SimpleNamespace(Pin=Pin, disable_irq=lambda: 0,
                                        enable_irq=lambda token: None)
        rp2 = types.SimpleNamespace(PIO=types.SimpleNamespace(SHIFT_RIGHT=0, JOIN_RX=0),
            StateMachine=SM, asm_pio=lambda **kwargs: lambda fn: fn)
        spec = importlib.util.spec_from_file_location("qr_pio_test_module",
            Path(__file__).resolve().parents[1] / "src" / "qr_pio_rx.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, machine=machine, rp2=rp2):
            spec.loader.exec_module(module)
            self.receiver_class = module.QRPioRx
            self.q = module.QRPioRx()

    def inject(self, values):
        self.q.sm.fifo.extend(values)
        self.q._irq(self.q.sm)

    def test_ring_wrap_preserves_data(self):
        for _ in range(8):
            values = list(range(100))
            self.inject(values)
            self.assertEqual(self.q.read(200), bytes(values))
            self.assertEqual(self.q.any(), 0)

    def test_overflow_discards_partial_scan(self):
        self.inject([65] * 256)
        self.assertEqual(self.q.take_error(), "QR_RX_OVERFLOW")
        self.assertEqual(self.q.any(), 0)
        self.assertIsNone(self.q.take_error())

    def test_frame_error_discards_buffer(self):
        self.inject([65, 255, 66])
        self.assertEqual(self.q.take_error(), "QR_UART_FRAME")
        self.assertEqual(self.q.read(35), b"")

    def test_diagnostic_ring_handles_burst_and_wrap(self):
        self.q = self.receiver_class(rx_pin=10, baudrate=230400, sm_id=1,
                                     tx_idle_pin=None, buffer_size=16384)
        self.assertIsNone(self.q.tx_idle)
        for _ in range(3):
            values = [i % 128 for i in range(12000)]
            self.inject(values)
            self.assertIsNone(self.q.take_error())
            self.assertEqual(self.q.read(16384), bytes(values))
        self.inject([65] * 16384)
        self.assertEqual(self.q.take_error(), "QR_RX_OVERFLOW")
        self.assertEqual(self.q.any(), 0)

    def test_non_power_of_two_buffer_rejected(self):
        with self.assertRaises(ValueError):
            self.receiver_class(buffer_size=300)
