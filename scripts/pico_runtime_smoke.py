"""Finite deployed-runtime check; NF55G must be disconnected.

ATE framing uses an in-memory peer, not physical UART wiring. Leaves CSV on SD.
No NF55G command is requested. Run via mpremote on a fresh interpreter.
"""
import os
from src.main import create_fixture_app
from src.ate_server import ATEServer


class Peer:
    def __init__(self):
        self.rx = b''
        self.tx = b''

    def any(self):
        return len(self.rx)

    def read(self, count=1):
        result, self.rx = self.rx[:count], self.rx[count:]
        return result

    def write(self, data):
        self.tx += bytes(data)
        return len(data)


class ObservedUART:
    def __init__(self, uart):
        self.uart = uart
        self.tx_bytes = 0

    def any(self):
        return self.uart.any()

    def read(self, count=1):
        return self.uart.read(count)

    def write(self, data):
        self.tx_bytes += len(data)
        return self.uart.write(data)


print('RUNTIME_SMOKE_BEGIN')
app = create_fixture_app()
observed = ObservedUART(app.nf55_uart)
app.protocol.uart = observed
peer = Peer()
app.server = ATEServer(peer)


def command(line):
    peer.rx = line.encode() + b'\r'
    app.service_once()
    assert not peer.tx, 'reply before CRLF'
    peer.rx = b'\n'
    app.service_once()
    reply, peer.tx = peer.tx, b''
    assert reply.endswith(b'\r\n'), repr(reply)
    print('ATE|{}|{}'.format(line, reply.decode().strip()))
    return reply.decode().strip()


try:
    print('SELF_CHECK|' + str(app.self_check()))
    assert app.rtc is not None
    first = app.rtc.datetime()
    app.clock.sleep_ms(1100)
    second = app.rtc.datetime()
    print('RTC_ADVANCE|{}|{}'.format(first, second))
    assert first != second
    command('*IDN?')
    command('RTC_CHECK?')
    assert command('FW_UPDATE') == 'ERR:FU_DISABLED'
    assert command('SD_STATUS?') == 'OK'
    print('SD_USAGE|' + str(app.logger.usage()))
    command('TEST_START')
    assert app.logger.active
    path = app.logger.sd_sink.open_filename
    for index in range(64):
        assert app.logger.log(category='PICO_SMOKE', event='ROW', detail='row={}'.format(index))
    for _ in range(3):
        app.service_once()
    command('TEST_END')
    assert not app.logger.active
    assert app.logger.status() == 'OK'
    assert not app.logger.queue
    with open(path, 'r') as source:
        lines = source.readlines()
    assert len(lines) == 65, len(lines)
    for index, line in enumerate(lines[1:]):
        assert line.rstrip().endswith('row={}'.format(index))
    print('SD_READBACK|{}|rows=64|drop={}'.format(path, app.logger.drop_count))
    assert app.logger.reinit()
    with open(path, 'r') as source:
        assert len(source.readlines()) == 65
    print('SD_REMOUNT_READBACK|OK')
    assert observed.tx_bytes == 0, observed.tx_bytes
    print('NF55_TX_BYTES|0')
    cycles = [0]
    pump = app._pump_ate
    def stop_after_cycles():
        pump()
        cycles[0] += 1
        if cycles[0] == 5:
            app.stop()
    app._pump_ate = stop_after_cycles
    app.run()
    assert cycles[0] == 5 and not app.running
    print('RUN_STOP|OK')
finally:
    app.stop()
    app.logger.sd_sink.close()
    if app.logger.sd_sink.mounted:
        os.umount('/sd')
    app.ate_uart.uart.deinit()
    app.nf55_uart.uart.deinit()
    print('RUNTIME_SMOKE_END')
print('RUNTIME_SMOKE_PASS')
