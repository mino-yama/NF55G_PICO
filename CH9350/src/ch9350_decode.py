"""CH9350状態2/3/4の標準キーボードフレームを解析する純Python層。
分割・連結受信を同期し、押下差分だけをUS配列文字へ変換する。
不明/不正入力を含む行はEnterまで無効。製品判定・正式Cacheは扱わない。
"""

_HEADER = b"\x57\xab"
_LENGTHS = {1: 11, 2: 7, 4: 10, 0x80: 4, 0x87: 3, 0x86: 3, 0x12: 11}
_SYMBOLS = {
    0x2c: (" ", " "), 0x2d: ("-", "_"), 0x2e: ("=", "+"),
    0x2f: ("[", "{"), 0x30: ("]", "}"), 0x31: ("\\", "|"),
    0x33: (";", ":"), 0x34: ("'", '"'), 0x35: ("`", "~"),
    0x36: (",", "<"), 0x37: (".", ">"), 0x38: ("/", "?"),
}


def key_to_ascii(key, modifier=0):
    """US配列のみ。Ctrl/Alt/GUI/CapsLock/JISは推測で変換しない。"""
    if modifier & ~0x22:
        return None
    shifted = bool(modifier & 0x22)
    if 4 <= key <= 29:
        return chr((65 if shifted else 97) + key - 4)
    if 30 <= key <= 39:
        return ("!@#$%^&*()" if shifted else "1234567890")[key - 30]
    if key == 0x28:
        return "\n"
    if key in _SYMBOLS:
        return _SYMBOLS[key][int(shifted)]
    return None


class KeyboardDecoder:
    def __init__(self, max_line=512):
        if max_line < 1:
            raise ValueError("max_line must be positive")
        self.max_line = max_line
        self.reset()

    def reset(self):
        """試行間・再接続時に明示して呼ぶ。途中の行は廃棄する。"""
        self._buffer = bytearray()
        self._pressed = ()
        self._line = ""
        self._valid = True

    def _error(self, events, reason):
        self._line = ""
        self._valid = False
        events.append({"type": "error", "reason": reason})

    def _keyboard(self, frame, events):
        modifier, reserved = frame[3], frame[4]
        keys = tuple(key for key in frame[5:] if key)
        if reserved or any(key <= 3 for key in keys) or len(set(keys)) != len(keys):
            self._pressed = ()
            self._error(events, "INVALID_KEYBOARD_REPORT")
            return
        new_keys = tuple(key for key in keys if key not in self._pressed)
        released = tuple(key for key in self._pressed if key not in keys)
        self._pressed = keys
        events.append({"type": "report", "modifier": modifier,
                       "pressed": new_keys, "released": released})
        for key in new_keys:
            char = key_to_ascii(key, modifier)
            if char is None:
                self._error(events, "UNSUPPORTED_KEY_OR_MODIFIER")
            elif char == "\n":
                if self._valid:
                    events.append({"type": "line", "text": self._line})
                else:
                    events.append({"type": "line_error", "reason": "INCOMPLETE_LINE"})
                self._line = ""
                self._valid = True
            elif self._valid:
                if len(self._line) >= self.max_line:
                    self._error(events, "LINE_TOO_LONG")
                else:
                    self._line += char
                    events.append({"type": "char", "text": char})

    def feed(self, data):
        """確定したフレームだけ処理。状態0/1は対象外で送信応答も行わない。"""
        events = []
        # 入力が大きくても内部バッファは最大11byteに制限する。
        for value in data:
            self._buffer.append(value)
            while self._buffer:
                if self._buffer[0] != 0x57:
                    del self._buffer[0]
                    self._error(events, "STREAM_NOISE")
                    continue
                if len(self._buffer) < 2:
                    break
                if self._buffer[1] != 0xab:
                    del self._buffer[0]
                    self._error(events, "HEADER_MISMATCH")
                    continue
                if len(self._buffer) < 3:
                    break
                code = self._buffer[2]
                length = _LENGTHS.get(code)
                if length is None:
                    self._error(events, "UNSUPPORTED_FRAME_%02X" % code)
                    del self._buffer[:3]
                    self._pressed = ()
                    continue
                if len(self._buffer) < length:
                    break
                frame = bytes(self._buffer[:length])
                del self._buffer[:length]
                if code == 1:
                    self._keyboard(frame, events)
                else:
                    events.append({"type": "non_keyboard", "code": code,
                                   "hex": " ".join("%02X" % b for b in frame)})
                    if code == 0x86:
                        self._pressed = ()
                        self._error(events, "DISCONNECTED")
        return events

    def finish(self):
        """ファイル終端で未完フレーム/Enterなしの行を成功にしない。"""
        incomplete = bool(self._buffer or self._line or not self._valid)
        self.reset()
        return ([{"type": "error", "reason": "INCOMPLETE_STREAM"}]
                if incomplete else [])
