import unittest
from src.qr_reader import QRReceiver, decode_qr

RAW = "ABCDEFGH" + "01234567890123" + "A03" + "26" + "39" + "000001"


class QRTests(unittest.TestCase):
    def test_layout_and_zeros(self):
        self.assertEqual(decode_qr(RAW), dict(product_name="ABCDEFGH",
            item_code="01234567890123", product_rev="A03",
            manufacture_year="26", manufacture_week="39", serial="000001"))

    def test_every_fragment_boundary(self):
        wire = (RAW + "\r\n").encode()
        for split in range(len(wire) + 1):
            r = QRReceiver(); r.start(0)
            r.feed(wire[:split], 1); r.feed(wire[split:], 2)
            self.assertEqual(r.state, "READY")

    def test_inactive_and_second_scan_ignored(self):
        r = QRReceiver(); r.feed((RAW + "\n").encode(), 0)
        self.assertEqual(r.state, "IDLE")
        r.start(1); r.feed((RAW + "\n" + "Z" * 35 + "\n").encode(), 2)
        self.assertEqual(r.raw, RAW)

    def test_no_prefix_success(self):
        r = QRReceiver(); r.start(0); r.feed(RAW.encode(), 1)
        self.assertIsNone(r.fields)
        r.feed(b"X\n", 2)
        self.assertEqual(r.error, "QR_LENGTH")

    def test_errors_and_no_partial_cache(self):
        for wire, error in [(RAW[:-1] + "\n", "QR_LENGTH"),
                            (RAW[:-1] + "!\n", "QR_CHAR"),
                            (RAW + "\rX", "QR_TERMINATOR")]:
            r = QRReceiver(); r.start(0); r.feed(wire.encode(), 1)
            self.assertEqual(r.error, error); self.assertIsNone(r.fields)

    def test_timeout_cannot_be_revived(self):
        r = QRReceiver(timeout_ms=10); r.start(0)
        r.feed((RAW + "\n").encode(), 10)
        self.assertEqual(r.error, "QR_TIMEOUT")
        self.assertEqual(r.command("QR_GET", 11), "ERR:CACHE_INVALID")

    def test_new_start_invalidates_old(self):
        r = QRReceiver(); r.start(0); r.feed((RAW + "\n").encode(), 1)
        r.start(2); self.assertIsNone(r.fields); self.assertEqual(r.raw, "")
        r.feed(b"!", 3); self.assertIsNone(r.fields)

    def test_commands_busy_query_cancel(self):
        r = QRReceiver()
        self.assertEqual(r.command("QR_SCAN", 0, False), "ERR:QR_INPUT_BUSY")
        self.assertEqual(r.command("QR_SCAN", 1), "OK:ARMED")
        self.assertEqual(r.command("QR_SCAN", 2), "ERR:QR_BUSY")
        r.feed((RAW + "\n").encode(), 3)
        self.assertEqual(r.command("QR_GET", 4), RAW)
        self.assertIn("serial=000001", r.command("QR_DATA", 4))
        r.command("QR_CANCEL", 5); self.assertIsNone(r.fields)
        self.assertEqual(r.command("SS", 6), "ERR:UNKNOWN_COMMAND")
        self.assertEqual(r.command("FW_UPDATE", 6), "ERR:FU_DISABLED")

    def test_character_policy_explicit(self):
        wire = "US250A-CGXE-009491-101A032639000001"
        self.assertEqual(len(wire), 35)
        with self.assertRaisesRegex(ValueError, "QR_CHAR"):
            decode_qr(wire, False)
        self.assertEqual(decode_qr(wire, True)["product_name"], "US250A-C")
        with self.assertRaises(ValueError):
            decode_qr("Ａ" + RAW[1:])


if __name__ == "__main__":
    unittest.main()
