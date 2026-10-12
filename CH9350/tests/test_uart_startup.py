"""PIO受信は明示起動時だけ。GP8/GP9固定・停止解放を検証。"""
import sys
import types
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ch9350_capture import start_pio
from test_capture import Clock, Receiver

class PioStartupTests(unittest.TestCase):
    def test_gp8_gp9_115200_and_release(self):
        seen = {}
        receiver = Receiver(b"\x00\xff")
        def make_receiver(**kwargs):
            seen.update(kwargs)
            return receiver
        module = types.SimpleNamespace(QRPioRx=make_receiver)
        with patch.dict(sys.modules, {"qr_pio_rx": module, "time": Clock()}):
            with patch("builtins.print"):
                result = start_pio(duration_ms=2)
        self.assertEqual(seen, {"rx_pin": 9, "baudrate": 115200, "sm_id": 0,
                                "tx_idle_pin": 8, "buffer_size": 4096})
        self.assertEqual(result["bytes"], 2)
        self.assertTrue(receiver.closed)

    def test_bad_parameters_never_initialize_gpio(self):
        for args in ({"buffer_size": 1}, {"buffer_size": 1000}, {"duration_ms": 0}):
            with patch.dict(sys.modules, {"qr_pio_rx": None}):
                with self.assertRaises(ValueError):
                    start_pio(**args)

if __name__ == "__main__": unittest.main()
