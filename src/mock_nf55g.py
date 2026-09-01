"""Host-side Mock NF55G for protocol and integration tests.

This module is a deterministic test peer. It is not an authoritative product
specification.
"""

try:
    from . import config
    from .frame import build_frame
except ImportError:  # pragma: no cover
    import config
    from frame import build_frame


class FakeClock:
    def __init__(self, start_ms=0):
        self._now_ms = int(start_ms)

    def ticks_ms(self):
        return self._now_ms

    def sleep_ms(self, ms):
        self._now_ms += int(ms)

    def advance_ms(self, ms):
        self.sleep_ms(ms)


class ResponseFactory:
    @staticmethod
    def ack():
        return bytes((config.ACK,))

    @staticmethod
    def nak(reason):
        reason_b = _to_ascii_bytes(reason)
        if len(reason_b) != 2:
            raise ValueError("NAK reason must be 2 ASCII chars")
        return bytes((config.NAK,)) + reason_b

    @staticmethod
    def frame(cmd, data=b""):
        return build_frame(cmd, data)

    @staticmethod
    def bcc_ng_frame(cmd, data=b""):
        frame = bytearray(build_frame(cmd, data))
        frame[-1] = ord("0") if frame[-1] != ord("0") else ord("1")
        return bytes(frame)

    @staticmethod
    def error_frame(error_code, cmd="ER"):
        error_b = _to_ascii_bytes(error_code)
        if error_b not in (b"CME", b"PME", b"SQE", b"HWE", b"MCM", b"FUE"):
            raise ValueError("unsupported NF55G error code")
        return build_frame(cmd, error_b)


class ScenarioStep:
    def __init__(self, outputs=(), consume_command=True, response_retry_outputs=()):
        self.outputs = tuple(outputs)
        self.consume_command = bool(consume_command)
        self.response_retry_outputs = tuple(response_retry_outputs)

    @staticmethod
    def ack_response(cmd, data=b"", ack_delay_ms=0, response_delay_ms=0):
        return ScenarioStep(
            (
                (ack_delay_ms, ResponseFactory.ack()),
                (response_delay_ms, ResponseFactory.frame(cmd, data)),
            )
        )

    @staticmethod
    def nak(reason="33", delay_ms=0):
        return ScenarioStep(((delay_ms, ResponseFactory.nak(reason)),))

    @staticmethod
    def ack_timeout():
        return ScenarioStep(())

    @staticmethod
    def resp_timeout(ack_delay_ms=0):
        return ScenarioStep(((ack_delay_ms, ResponseFactory.ack()),))

    @staticmethod
    def bcc_ng(cmd, data=b"", ack_delay_ms=0, response_delay_ms=0):
        return ScenarioStep(
            (
                (ack_delay_ms, ResponseFactory.ack()),
                (response_delay_ms, ResponseFactory.bcc_ng_frame(cmd, data)),
            )
        )

    @staticmethod
    def error(error_code, cmd="ER", ack_delay_ms=0, response_delay_ms=0):
        return ScenarioStep(
            (
                (ack_delay_ms, ResponseFactory.ack()),
                (response_delay_ms, ResponseFactory.error_frame(error_code, cmd=cmd)),
            )
        )

    @staticmethod
    def bcc_ng_then_retry(
        cmd,
        data=b"",
        retry_data=None,
        ack_delay_ms=0,
        response_delay_ms=0,
        retry_delay_ms=0,
    ):
        if retry_data is None:
            retry_data = data
        return ScenarioStep(
            (
                (ack_delay_ms, ResponseFactory.ack()),
                (response_delay_ms, ResponseFactory.bcc_ng_frame(cmd, data)),
            ),
            response_retry_outputs=((retry_delay_ms, ResponseFactory.frame(cmd, retry_data)),),
        )


class MockNF55GScenario:
    def __init__(self, steps=()):
        self._steps = list(steps)
        self.handled_command_count = 0
        self.response_retry_request_count = 0
        self._pending_response_retry_outputs = ()

    def add(self, step):
        self._steps.append(step)
        return self

    def on_pico_write(self, data, uart):
        data_b = bytes(data)
        if data_b == bytes((config.NAK,)):
            self.response_retry_request_count += 1
            for delay_ms, payload in self._pending_response_retry_outputs:
                uart.enqueue_rx(payload, delay_ms=delay_ms)
            self._pending_response_retry_outputs = ()
            return
        if data_b == bytes((config.ACK,)):
            return
        if not self._steps:
            return
        step = self._steps.pop(0)
        if step.consume_command:
            self.handled_command_count += 1
        self._pending_response_retry_outputs = step.response_retry_outputs
        for delay_ms, payload in step.outputs:
            uart.enqueue_rx(payload, delay_ms=delay_ms)

    def remaining(self):
        return len(self._steps)


class MockUART:
    def __init__(self, clock=None, scenario=None):
        self.clock = clock or FakeClock()
        self.scenario = scenario or MockNF55GScenario()
        self.tx_log = []
        self._rx = []

    def write(self, data):
        data_b = bytes(data)
        self.tx_log.append(data_b)
        self.scenario.on_pico_write(data_b, self)
        return len(data_b)

    def enqueue_rx(self, data, delay_ms=0):
        due_ms = self.clock.ticks_ms() + int(delay_ms)
        self._rx.append([due_ms, bytes(data)])
        self._rx.sort(key=lambda item: item[0])

    def any(self):
        return len(self._available_bytes())

    def read(self, n=1):
        if n is None or n < 0:
            n = self.any()
        available = self._available_bytes()
        if not available:
            return b""
        out = available[:n]
        self._consume_available(len(out))
        return out

    def read_all(self):
        return self.read(-1)

    def tx_count(self):
        return len(self.tx_log)

    def clear(self):
        self.tx_log = []
        self._rx = []

    def _available_bytes(self):
        now = self.clock.ticks_ms()
        chunks = []
        for due_ms, payload in self._rx:
            if due_ms <= now:
                chunks.append(payload)
        return b"".join(chunks)

    def _consume_available(self, count):
        remaining_to_consume = count
        new_rx = []
        now = self.clock.ticks_ms()
        for due_ms, payload in self._rx:
            if due_ms > now or remaining_to_consume <= 0:
                new_rx.append([due_ms, payload])
                continue
            if len(payload) <= remaining_to_consume:
                remaining_to_consume -= len(payload)
            else:
                new_rx.append([due_ms, payload[remaining_to_consume:]])
                remaining_to_consume = 0
        self._rx = new_rx


def _to_ascii_bytes(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    return str(value).encode("ascii")

