# 親Pico側の非blocking中継リンク。ATE入口とは独立に1要求ずつ処理する。
# HELLOは起動照合のみで、機器コマンドは明示要求の本文だけを送る。
# 失敗後は自動再送/再同期せず、旧機器応答を排除した再起動を必要とする。

try:
    from .external_instrument_contract import (ContractError, encode_frame, decode_frame,
        format_query_response, format_error, SEND_COMPLETE_REPLY)
    from .external_instrument_relay import ExternalInstrumentRelay, RelayError
except ImportError:  # pragma: no cover
    from external_instrument_contract import (ContractError, encode_frame, decode_frame,
        format_query_response, format_error, SEND_COMPLETE_REPLY)
    from external_instrument_relay import ExternalInstrumentRelay, RelayError


class FrameReader:
    def __init__(self):
        self.buffer = bytearray()
        self.dropping = False
        self.previous = None
        self.errors = 0

    def feed(self, raw):
        frames = []
        for value in raw:
            if len(self.buffer) >= 512:
                self.buffer = bytearray()
                self.dropping = True
            if not self.dropping:
                self.buffer.append(value)
            if value == 10 and self.previous == 13:
                if not self.dropping:
                    try:
                        frames.append(decode_frame(bytes(self.buffer)))
                    except ContractError:
                        self.errors += 1
                else:
                    self.errors += 1
                self.buffer = bytearray()
                self.dropping = False
            self.previous = value
        return frames


def new_nonce():
    import os
    nonce = os.urandom(8)
    if len(nonce) != 8 or nonce == bytes(8):
        raise ValueError('NONCE')
    return nonce


class ExternalInstrumentLink:
    def __init__(self, transport, clock, parent_nonce, expected_chipid):
        if not isinstance(parent_nonce, bytes) or len(parent_nonce) != 8 or parent_nonce == bytes(8):
            raise ValueError('NONCE')
        # 有効化時に必要なCRC/書式APIを先に検査し、任意機能の欠落をATE起動から分離する。
        encode_frame(parent_nonce + bytes(8), 0, 'H', 0, 0, b'')
        self.transport = transport
        self.clock = clock
        self.parent_nonce = parent_nonce
        self.expected_chipid = expected_chipid.upper()
        self.reader = FrameReader()
        self.core = ExternalInstrumentRelay(clock, 192, 192)
        self.session = None
        self.host_info = None
        self.fault = False
        self._active = None
        self._token = None
        self._tx = b''
        self._tx_kind = None
        self._remote_ambiguous = None
        self._immediate = None
        self.stale_frames = 0
        self._management = None
        self._management_reply = None
        self._management_counter = 0
        self._reset_boot_nonce = None

    @property
    def busy(self):
        return (self._active is not None or self._immediate is not None or
                self._management is not None or self._management_reply is not None)

    def start_management(self, operation):
        if operation not in ("INFO", "RESET"):
            raise RelayError("MANAGEMENT_COMMAND")
        if self.busy or self._tx:
            raise RelayError("BUSY")
        request_id = self._next_management_id()
        challenge = ("{:08X}{:08X}".format(request_id, self.clock.ticks_ms() & 0xffffffff)).encode("ascii")
        payload = self.expected_chipid.encode("ascii") + b"|" + challenge
        self._management = {
            "operation": operation,
            "stage": "INFO",
            "request_id": request_id,
            "challenge": challenge,
            "payload": payload,
            "started_at": self.clock.ticks_ms(),
            "timeout_ms": 1000,
            "session": None,
            "tx_started": False,
        }
        self._tx = encode_frame(self.parent_nonce + bytes(8), request_id, "I", 0, 1000, payload)
        self._tx_kind = "I"

    def _next_management_id(self):
        if self._management_counter >= 0xffffffff:
            raise RelayError("SESSION_EXHAUSTED")
        self._management_counter += 1
        return self._management_counter

    def _finish_management(self, reply):
        self._tx = b""
        self._management = None
        self._management_reply = reply

    def _management_error(self, reason, ambiguous=False):
        if ambiguous:
            operation = self._management
            self.fault = True
            self.session = None
            self.host_info = None
            if operation is not None and operation["session"] is not None:
                self._reset_boot_nonce = operation["session"][8:]
        self._finish_management("ERR:HOST_{}".format(reason))

    def _receive_management_frame(self, frame):
        operation = self._management
        if (frame["request"] != operation["request_id"] or
                frame["session"][:8] != self.parent_nonce or frame["mode"] != 0 or
                frame["timeout_ms"] != operation["timeout_ms"]):
            self.stale_frames += 1
            return
        if frame["kind"] == "E":
            try:
                reason, ambiguous = frame["payload"].decode("ascii").split("|")
                if ambiguous != "0" or not reason or not reason.replace("_", "").isalnum():
                    raise ValueError("management error")
            except (UnicodeError, ValueError):
                self._management_error("RESPONSE_FRAME")
                return
            self._management_error(reason)
            return
        if operation["stage"] == "INFO":
            if frame["kind"] != "i" or frame["session"][8:] == bytes(8):
                self._management_error("RESPONSE_FRAME")
                return
            try:
                identity, version, state, challenge = frame["payload"].decode("ascii").split("|")
            except (UnicodeError, ValueError):
                self._management_error("HOST_IDENTITY")
                return
            if (identity.upper() != self.expected_chipid or
                    not version.startswith("meter-host-relay-") or
                    challenge.encode("ascii") != operation["challenge"] or
                    state not in ("READY", "NOT_READY", "BUSY", "FAULT")):
                self._management_error("HOST_IDENTITY")
                return
            self.host_info = (identity, version, state)
            host_nonce = frame["session"][8:]
            if operation["operation"] == "INFO":
                if self._reset_boot_nonce is not None:
                    if host_nonce == self._reset_boot_nonce:
                        self._management_error("RESET_NOT_CONFIRMED")
                        return
                    old_nonce = self._reset_boot_nonce
                    self._reset_boot_nonce = None
                    # 管理INFOは通常sessionをbindしない。次の明示要求でH/hを照合する。
                    self.session = None
                    self._finish_management("OK:HOST_RESET_DONE:{}:{}:{}:{}".format(
                        identity.upper(), old_nonce.hex().upper(), host_nonce.hex().upper(), state))
                    return
                self._finish_management("OK:HOST_INFO:{}:{}:{}:{}".format(
                    identity.upper(), version, host_nonce.hex().upper(), state))
                return
            if state == "BUSY":
                self._management_error("BUSY")
                return
            request_id = self._next_management_id()
            operation["request_id"] = request_id
            operation["stage"] = "RESET"
            operation["session"] = frame["session"]
            operation["started_at"] = self.clock.ticks_ms()
            self._tx = encode_frame(frame["session"], request_id, "S", 0,
                                    operation["timeout_ms"], operation["payload"])
            self._tx_kind = "S"
            return
        if frame["session"] != operation["session"] or frame["kind"] != "K" or frame["payload"] != b"RESET_ACCEPTED":
            self._management_error("RESULT_UNKNOWN", ambiguous=operation["tx_started"])
            return
        self._reset_boot_nonce = frame["session"][8:]
        self.session = None
        self.host_info = None
        self.reader.buffer = bytearray()
        self.reader.dropping = False
        self.reader.previous = None
        self._finish_management("OK:HOST_RESET_ACCEPTED:{}:{}".format(
            self.expected_chipid, self._reset_boot_nonce.hex().upper()))

    def start(self, request):
        if self.busy:
            raise RelayError('BUSY')
        # RST受理だけでは通常通信へ戻さず、別INFOによる新boot確認を待つ。
        if self.fault or self._reset_boot_nonce is not None:
            raise RelayError('RECOVERY_REQUIRED')
        self._active = dict(request)
        self._active['started_at'] = self.clock.ticks_ms()
        self._remote_ambiguous = None
        if self.session is None:
            self._tx = encode_frame(self.parent_nonce + bytes(8), 0, 'H', 0, 0, b'')
            self._tx_kind = 'H'
        else:
            self._begin_command()

    def _begin_command(self):
        left = self._active['timeout_ms'] - (self.clock.ticks_ms() - self._active['started_at'])
        if left <= 0:
            self._fail_handshake('TIMEOUT', True)
            return
        req = self._active
        self._token = self.core.begin(req['command'], req['expects_response'], left, req['response_ending'])
        request_id = self._token[1]
        if request_id > 0xffffffff:
            self.core.fail(self._token, 'SESSION_EXHAUSTED')
            self.fault = True
            return
        req['wire_timeout'] = left
        req['mode'] = 1 if req['expects_response'] else 0
        self._tx = encode_frame(self.session, request_id, 'Q', req['mode'], left, req['command'])
        self._tx_kind = 'Q'

    def poll(self):
        if self._management is not None:
            operation = self._management
            if self.clock.ticks_ms() - operation["started_at"] >= operation["timeout_ms"]:
                ambiguous = operation["stage"] == "RESET" and operation["tx_started"]
                self._management_error("RESULT_UNKNOWN" if ambiguous else "TIMEOUT", ambiguous)
        if self._active is not None:
            elapsed = self.clock.ticks_ms() - self._active['started_at']
            if elapsed >= self._active['timeout_ms'] and self._token is None:
                self._fail_handshake('TIMEOUT', True)
        self.core.poll()
        try:
            fault = self.transport.take_error() if hasattr(self.transport, 'take_error') else None
            if fault:
                self._transport_fail('UART')
            if self._token is not None:
                try:
                    self.core.request(self._token)
                except RelayError:
                    self._tx = b''
            if self._tx:
                # UART投入前に成否不明の可能性を記録する。USB全送信完了はTで別確認。
                if self._tx_kind == 'Q' and self._token is not None:
                    self.core.mark_tx_started(self._token)
                written = self.transport.write(self._tx[:64])
                if written is not None:
                    if not isinstance(written, int) or written < 0 or written > min(64, len(self._tx)):
                        self._transport_fail('UART')
                    else:
                        if written > 0 and self._management is not None and self._management["stage"] == "RESET":
                            self._management["tx_started"] = True
                        self._tx = self._tx[written:]
            if self.transport.any():
                for frame in self.reader.feed(self.transport.read(64) or b''):
                    self._receive_frame(frame)
        except OSError:
            self._transport_fail('UART')
        # 期限切れ後に残りQを送らない。resultが未回収でもpendingは既に終了している。
        if self._token is not None:
            try:
                self.core.request(self._token)
            except RelayError:
                self._tx = b''

    def _receive_frame(self, frame):
        if self._management is not None:
            self._receive_management_frame(frame)
            return
        if self._active is None:
            self.stale_frames += 1
            return
        if self._token is None:
            if (frame['kind'] != 'h' or frame['request'] != 0 or frame['mode'] != 0 or
                    frame['timeout_ms'] != 0 or frame['session'][:8] != self.parent_nonce or
                    frame['session'][8:] == bytes(8)):
                self.stale_frames += 1
                return
            try:
                identity, version, state = frame['payload'].decode('ascii').split('|')
            except (UnicodeError, ValueError):
                self._fail_handshake('HOST_IDENTITY', True)
                return
            if identity.upper() != self.expected_chipid or not version.startswith('meter-host-relay-'):
                self._fail_handshake('HOST_IDENTITY', True)
                return
            self.host_info = (identity, version, state)
            if state != 'READY':
                self._fail_handshake('RECOVERY_REQUIRED' if state == 'FAULT' else 'LINK_NOT_READY', state == 'FAULT')
                return
            self.session = frame['session']
            self.core.establish_link()
            self._begin_command()
            return
        req = self._active
        if (frame['session'] != self.session or frame['request'] != self._token[1] or
                frame['mode'] != req['mode'] or frame['timeout_ms'] != req['wire_timeout']):
            self.stale_frames += 1
            return
        if frame['kind'] == 'A' and not frame['payload']:
            return
        if frame['kind'] == 'T' and not frame['payload']:
            self.core.mark_tx_complete(self._token)
        elif frame['kind'] == 'R' and req['expects_response']:
            if not frame['payload'] or not frame['payload'].endswith(b'\r\n'):
                self.core.fail(self._token, 'RESPONSE_FRAME')
            else:
                self.core.receive(self._token, frame['payload'])
        elif frame['kind'] == 'E':
            try:
                reason, flag = frame['payload'].decode('ascii').split('|')
                if flag not in ('0', '1'):
                    raise ValueError('flag')
                format_error(reason, flag == '1')
            except (UnicodeError, ValueError):
                self.core.fail(self._token, 'RESPONSE_FRAME')
                return
            self._remote_ambiguous = flag == '1'
            self.core.fail(self._token, reason)
        else:
            self.core.fail(self._token, 'RESPONSE_FRAME')

    def _fail_handshake(self, reason, latch):
        self._tx = b''
        self._immediate = format_error(reason, False)
        self._active = None
        if latch:
            self.fault = True

    def _transport_fail(self, reason):
        self.fault = True
        self._tx = b''
        if self._management is not None:
            operation = self._management
            ambiguous = operation["stage"] == "RESET" and operation["tx_started"]
            self._management_error("RESULT_UNKNOWN" if ambiguous else reason, ambiguous)
            return
        if self._token is not None:
            self.core.fail(self._token, reason)
        elif self._active is not None:
            self._fail_handshake(reason, True)

    def take_reply(self):
        if self._management_reply is not None:
            reply, self._management_reply = self._management_reply, None
            return reply
        if self._immediate is not None:
            reply, self._immediate = self._immediate, None
            return reply
        result = self.core.take_result()
        if result is None:
            return None
        self._tx = b''
        self._active = None
        self._token = None
        if result['status'] == 'RESPONSE_COMPLETE':
            return format_query_response(result['raw'])
        if result['status'] == 'TX_COMPLETE':
            return SEND_COMPLETE_REPLY
        self.fault = True
        ambiguous = result['ambiguous'] if self._remote_ambiguous is None else self._remote_ambiguous
        if result['status'] == 'LINK_NOT_READY' and not ambiguous:
            self.session = None
            self.host_info = None
            self.fault = False
        return format_error(result['status'], ambiguous)

    def cancel(self):
        if self._token is not None:
            self.core.cancel(self._token)
        elif self._active is not None:
            self._fail_handshake('CANCELLED', True)
