"""CH9350の同期・HID差分・不完全データの拒否を合成通信で検証。"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ch9350_decode import KeyboardDecoder, key_to_ascii


def frame(*keys, modifier=0, reserved=0):
    return bytes((0x57, 0xab, 1, modifier, reserved) +
                 tuple(keys) + (0,) * (6 - len(keys)))


def stroke(key, modifier=0):
    return frame(key, modifier=modifier) + frame()


def lines(events):
    return [event["text"] for event in events if event["type"] == "line"]


class DecodeTests(unittest.TestCase):
    def test_every_split_of_frame(self):
        wire = stroke(4) + stroke(0x28)
        for split in range(len(wire) + 1):
            decoder = KeyboardDecoder()
            events = decoder.feed(wire[:split]) + decoder.feed(wire[split:])
            self.assertEqual(lines(events), ["a"], split)

    def test_one_byte_chunks_and_multiple_lines(self):
        decoder = KeyboardDecoder()
        events = []
        for value in (stroke(4) + stroke(0x28)) * 2:
            events.extend(decoder.feed(bytes((value,))))
        self.assertEqual(lines(events), ["a", "a"])

    def test_repeated_held_reports_not_duplicate(self):
        events = KeyboardDecoder().feed(frame(4) * 3 + frame() + stroke(0x28))
        self.assertEqual(lines(events), ["a"])

    def test_release_allows_same_key_again(self):
        events = KeyboardDecoder().feed(stroke(4) * 2 + stroke(0x28))
        self.assertEqual(lines(events), ["aa"])

    def test_left_and_right_shift_and_digits(self):
        events = KeyboardDecoder().feed(stroke(4, 2) + stroke(5, 32) +
                                        stroke(30) + stroke(39) + stroke(0x28))
        self.assertEqual(lines(events), ["AB10"])
        self.assertEqual(key_to_ascii(30, 2), "!")

    def test_hyphen_space_and_us_symbols(self):
        events = KeyboardDecoder().feed(stroke(0x2d) + stroke(0x2c) +
                                        stroke(0x2d, 2) + stroke(0x28))
        self.assertEqual(lines(events), ["- _"])

    def test_mouse_header_in_payload_is_not_keyboard(self):
        mouse = b"\x57\xab\x02\x57\xab\x01\x00"
        events = KeyboardDecoder().feed(mouse + stroke(4) + stroke(0x28))
        self.assertEqual(lines(events), ["a"])
        self.assertEqual(events[0]["type"], "non_keyboard")

    def test_status_version_absolute_mouse_are_consumed(self):
        wire = (b"\x57\xab\x80\x57" + b"\x57\xab\x87" +
                b"\x57\xab\x04" + bytes(7) + stroke(4) + stroke(0x28))
        events = KeyboardDecoder().feed(wire)
        self.assertEqual(lines(events), ["a"])
        self.assertEqual(sum(e["type"] == "non_keyboard" for e in events), 3)

    def test_rollover_rejects_partial_line_then_recovers(self):
        wire = (stroke(4) + frame(1) + frame() + stroke(5) + stroke(0x28) +
                stroke(6) + stroke(0x28))
        events = KeyboardDecoder().feed(wire)
        self.assertEqual(lines(events), ["c"])
        self.assertTrue(any(e["type"] == "line_error" for e in events))

    def test_control_modifier_rejects_line(self):
        events = KeyboardDecoder().feed(stroke(4, 1) + stroke(0x28))
        self.assertEqual(lines(events), [])

    def test_capslock_rejects_line(self):
        events = KeyboardDecoder().feed(stroke(0x39) + stroke(4) + stroke(0x28))
        self.assertEqual(lines(events), [])

    def test_reserved_and_duplicate_slots_rejected(self):
        for invalid in (frame(4, reserved=1), frame(4, 4)):
            events = KeyboardDecoder().feed(invalid + frame() + stroke(0x28))
            self.assertEqual(lines(events), [])

    def test_noise_discards_line_until_enter(self):
        wire = b"\x00\x57\x57" + stroke(4) + stroke(0x28) + stroke(5) + stroke(0x28)
        self.assertEqual(lines(KeyboardDecoder().feed(wire)), ["b"])

    def test_state_zero_is_not_silently_decoded(self):
        events = KeyboardDecoder().feed(b"\x57\xab\x88" + stroke(4) + stroke(0x28))
        self.assertEqual(lines(events), [])
        self.assertTrue(any(e.get("reason") == "UNSUPPORTED_FRAME_88" for e in events))

    def test_incomplete_frame_and_unterminated_line(self):
        for wire in (frame(4)[:7], stroke(4)):
            decoder = KeyboardDecoder()
            self.assertEqual(lines(decoder.feed(wire)), [])
            self.assertEqual(decoder.finish()[0]["reason"], "INCOMPLETE_STREAM")

    def test_explicit_reset_discards_partial_and_held_keys(self):
        decoder = KeyboardDecoder()
        decoder.feed(frame(4))
        decoder.reset()
        self.assertEqual(lines(decoder.feed(stroke(4) + stroke(0x28))), ["a"])

    def test_line_limit_rejects_without_partial_success(self):
        events = KeyboardDecoder(max_line=1).feed(stroke(4) + stroke(5) + stroke(0x28))
        self.assertEqual(lines(events), [])
        self.assertTrue(any(e.get("reason") == "LINE_TOO_LONG" for e in events))

    def test_100_identical_reads(self):
        events = KeyboardDecoder().feed((stroke(4) + stroke(0x28)) * 100)
        self.assertEqual(lines(events), ["a"] * 100)

    def test_full_nf55g_sample_preserves_case_zeroes_hyphens(self):
        expected = "US250A-CGXE-009491-10101A2623000001"
        wire = bytearray()
        for char in expected:
            if char.isalpha(): key, mod = ord(char.lower()) - ord("a") + 4, 2
            elif char.isdigit(): key, mod = (39 if char == "0" else 29 + int(char)), 0
            else: key, mod = 0x2d, 0
            wire.extend(stroke(key, mod))
        wire.extend(stroke(0x28))
        self.assertEqual(lines(KeyboardDecoder().feed(wire)), [expected])

if __name__ == "__main__": unittest.main()
