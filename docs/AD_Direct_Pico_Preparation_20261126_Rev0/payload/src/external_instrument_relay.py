# 外部測定器中継の要求・応答をRAM内で管理する。ATE/UARTの正式書式とは独立。
# 送信開始前にmark_tx_startedを呼び、送信完了と機器の実行成功を区別する。
# 期限切れ・切断・取消後は明示的なリンク再確立まで次要求を受け付けない。

"""Transport-independent relay core, not an ATE or parent/Host wire protocol.

The adapter must correlate callbacks to the original internal token. It must
not label uncorrelated CDC bytes with the newest request token. establish_link
requires an adapter-verified clean connection, never just a quiet-time delay.
Limits, deadline and response delimiter are supplied by the caller. This core
has no GPIO, UART, USB, NF55G, cache, logger or product-judgement side effects.
"""


class RelayError(ValueError):
    pass


def _positive_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


class ExternalInstrumentRelay:
    def __init__(self, clock, max_command_bytes, max_response_bytes):
        if not _positive_integer(max_command_bytes) or not _positive_integer(max_response_bytes):
            raise RelayError("LIMIT")
        self.clock = clock
        self.max_command_bytes = max_command_bytes
        self.max_response_bytes = max_response_bytes
        self._generation = 0
        self._sequence = 0
        self._ready = False
        self._pending = None
        self._result = None

    @property
    def busy(self):
        return self._pending is not None or self._result is not None

    @property
    def ready(self):
        return self._ready

    def establish_link(self):
        # 起動識別/旧データ排除はadapterが確認する。単なるtimeout後の再許可ではない。
        if self.busy:
            raise RelayError("BUSY")
        self._generation += 1
        self._ready = True

    def begin(self, command, expects_response, timeout_ms, response_ending):
        if self.busy:
            raise RelayError("BUSY")
        if not self._ready:
            raise RelayError("LINK_NOT_READY")
        if not isinstance(command, bytes) or not command or len(command) > self.max_command_bytes:
            raise RelayError("COMMAND")
        if any(value < 32 or value > 126 for value in command):
            raise RelayError("COMMAND_ASCII")
        if not isinstance(expects_response, bool) or not _positive_integer(timeout_ms):
            raise RelayError("REQUEST")
        if expects_response:
            if (not isinstance(response_ending, bytes) or not response_ending or
                    len(response_ending) > self.max_response_bytes):
                raise RelayError("RESPONSE_ENDING")
        elif response_ending is not None:
            raise RelayError("RESPONSE_ENDING")
        self._sequence += 1
        token = (self._generation, self._sequence)
        self._pending = {
            "token": token, "command": command, "expects_response": expects_response,
            "timeout_ms": timeout_ms, "response_ending": response_ending,
            "started_at": self.clock.ticks_ms(), "tx_started": False,
            "tx_complete": False, "raw": b"", "response_complete": False,
        }
        return token

    def request(self, token):
        # 本文は変形しない。機器別adapterが送信終端を1回だけ付加する。
        if not self._match(token):
            raise RelayError("REQUEST_INVALID")
        return {key: self._pending[key] for key in
                ("token", "command", "expects_response", "timeout_ms", "response_ending")}

    def mark_tx_started(self, token):
        if not self._match(token) or self._pending["tx_started"]:
            return False
        self._pending["tx_started"] = True
        return True

    def mark_tx_complete(self, token):
        if not self._match(token):
            return False
        pending = self._pending
        if not pending["tx_started"] or pending["tx_complete"]:
            return False
        pending["tx_complete"] = True
        if not pending["expects_response"]:
            # adapterによる全送信完了だけを示す。機器の設定受理/実行完了は示さない。
            self._finish("TX_COMPLETE", False)
        elif pending["response_complete"]:
            self._finish("RESPONSE_COMPLETE", False)
        return True

    def receive(self, token, data):
        if not self._match(token):
            # 完了後の追加データは新要求へ回さず、adapterに再同期を要求する。
            if (self._result is not None and self._result["token"] == token and data and
                    self._result["status"] in ("TX_COMPLETE", "RESPONSE_COMPLETE")):
                self._ready = False
                self._result["status"] = "EXTRA_DATA"
                self._result["ambiguous"] = True
            return False
        pending = self._pending
        if not isinstance(data, bytes):
            raise RelayError("RESPONSE_BYTES")
        if not data:
            return True
        if not pending["tx_started"] or not pending["expects_response"]:
            self._finish("UNEXPECTED_DATA", pending["tx_started"], recover=True)
            return False
        if len(pending["raw"]) + len(data) > self.max_response_bytes:
            self._finish("RESPONSE_TOO_LONG", True, recover=True)
            return False
        pending["raw"] += data
        end = pending["raw"].find(pending["response_ending"])
        if end < 0:
            return True
        if end + len(pending["response_ending"]) != len(pending["raw"]):
            self._finish("EXTRA_DATA", True, recover=True)
            return False
        pending["response_complete"] = True
        # RX callbackがTX完了callbackより先でも、両方揃うまで成功を返さない。
        if pending["tx_complete"]:
            self._finish("RESPONSE_COMPLETE", False)
        return True

    def fail(self, token, reason):
        if not self._match(token):
            return False
        if not isinstance(reason, str) or not reason:
            raise RelayError("FAILURE_REASON")
        self._finish(reason, self._pending["tx_started"], recover=True)
        return True

    def cancel(self, token):
        return self.fail(token, "CANCELLED")

    def disconnect(self):
        self._ready = False
        if self._pending is not None:
            self._finish("DISCONNECTED", self._pending["tx_started"], recover=True)

    def poll(self):
        if self._pending is not None:
            elapsed = self.clock.ticks_ms() - self._pending["started_at"]
            if elapsed >= self._pending["timeout_ms"]:
                self._finish("TIMEOUT", self._pending["tx_started"], recover=True)

    def take_result(self):
        self.poll()
        result = self._result
        self._result = None
        return result

    def _match(self, token):
        self.poll()
        return self._pending is not None and self._pending["token"] == token

    def _finish(self, status, ambiguous, recover=False):
        pending = self._pending
        self._result = {
            "token": pending["token"], "status": status, "raw": pending["raw"],
            "ambiguous": ambiguous, "tx_complete": pending["tx_complete"],
        }
        self._pending = None
        if recover:
            self._ready = False
