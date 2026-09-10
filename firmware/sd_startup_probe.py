"""Temporary diagnostic boot; NF55G disconnected. Restore firmware/main.py later.
First mount evidence is preserved before extra CMD0 commands; no auto remount.
"""
from src import main as runtime
from src.sd_sink import PicoSDSink
from src.sd_card import SDCard
from src.pico_clock import SystemClock

CASE = 'BASELINE'
CASES = {'BASELINE': (0, False), 'DELAY_ONLY': (500, False),
         'CS_ONLY': (0, True), 'DELAY_AND_CS': (500, True)}
diagnostic_report = None


def run_post_failure_probe(app, snapshot, factory=None):
    report = {'first_startup': dict(snapshot), 'results': [], 'error': None,
              'skipped': None, 'baudrate': 400000, 'delay_ms': 50}
    if app.logger.sd_sink.mounted or snapshot.get('mounted'):
        report['skipped'] = 'FILESYSTEM_MOUNTED'
        return report
    if (snapshot.get('stage') != 'CARD_INIT'
            or 'CMD0 failed' not in (snapshot.get('error') or '')):
        report['skipped'] = 'NOT_CMD0_FAILURE'
        return report
    if app._comm_busy():
        report['skipped'] = 'COMM_BUSY'
        return report
    card = None
    try:
        card = (factory or create_cmd0_probe)()
        report['results'] = card.diagnose_cmd0_multi(attempts=10, delay_ms=50)
    except Exception as exc:
        report['error'] = repr(exc)
    finally:
        if card is not None:
            card.cs(1)
            card.spi.deinit()
    return report


def create_cmd0_probe():
    # Raw diagnostic transport, never a mounted block device.
    from machine import Pin, SPI
    card = object.__new__(SDCard)
    card.clock = SystemClock()
    card.cmdbuf = bytearray(6)
    card.tokenbuf = bytearray(1)
    card.last_extra = bytearray()
    card.spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    try:
        card.cs = Pin(17, Pin.OUT, value=1)
        card.init_spi(400000)
        for _ in range(16):
            card.spi.write(bytes([255]))
        return card
    except Exception:
        card.spi.deinit()
        raise


def main():
    global diagnostic_report
    delay, early_cs = CASES[CASE]
    original = runtime.PicoSDSink
    runtime.PicoSDSink = lambda: PicoSDSink(startup_delay_ms=delay, cs_before_spi=early_cs)
    try:
        app = runtime.create_fixture_app()
    finally:
        runtime.PicoSDSink = original
    runtime.startup_sd_diagnostic['case'] = CASE
    diagnostic_report = run_post_failure_probe(app, runtime.startup_sd_diagnostic)
    print('CMD0_DIAGNOSTIC_REPORT', diagnostic_report)
    app.run()


if __name__ == '__main__':
    main()
