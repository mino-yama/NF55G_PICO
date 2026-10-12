"""実機不要の生バイト保存・欠落表示・停止テスト。"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ch9350_capture import capture, format_hex

class Clock:
    def __init__(self): self.now = 0
    def ticks_ms(self): return self.now
    def ticks_diff(self, later, earlier): return later - earlier
    def sleep_ms(self, value): self.now += value

class Receiver:
    def __init__(self, data=b"", error=None, interrupt=False):
        self.data, self.error, self.interrupt = data, error, interrupt
        self.closed = False
    def any(self):
        if self.interrupt: raise KeyboardInterrupt
        return len(self.data)
    def read(self, count):
        data, self.data = self.data[:count], self.data[count:]
        return data
    def take_error(self):
        error, self.error = self.error, None
        return error
    def close(self): self.closed = True

class CaptureTests(unittest.TestCase):
    def test_binary_bytes_across_chunks(self):
        receiver, lines = Receiver(bytes(range(256))), []
        result = capture(receiver, 3, 17, lines.append, Clock())
        restored = b"".join(bytes.fromhex(line.split("hex=")[1])
                            for line in lines if line.startswith("RX "))
        self.assertEqual(restored, bytes(range(256)))
        self.assertEqual(result["bytes"], 256)
        self.assertTrue(receiver.closed)
    def test_loss_is_explicit(self):
        lines = []
        result = capture(Receiver(error="RX_OVERFLOW"), 2,
                         emit=lines.append, clock=Clock())
        self.assertEqual(result["errors"], 1)
        self.assertTrue(any(line.startswith("LOSS ") for line in lines))
    def test_control_c_closes_receiver(self):
        receiver, lines = Receiver(interrupt=True), []
        result = capture(receiver, emit=lines.append, clock=Clock())
        self.assertTrue(receiver.closed)
        self.assertEqual(result["bytes"], 0)
        self.assertIn("CAPTURE_INTERRUPTED", lines)
    def test_output_failure_closes_receiver(self):
        receiver = Receiver(b"a")
        def emit(line):
            if line.startswith("RX "): raise OSError("output unavailable")
        with self.assertRaises(OSError):
            capture(receiver, 2, emit=emit, clock=Clock())
        self.assertTrue(receiver.closed)
    def test_hex_includes_zero_and_ff(self):
        self.assertEqual(format_hex(b"\x00\x57\xab\xff"), "00 57 AB FF")

if __name__ == "__main__": unittest.main()
