"""Temporary diagnostic boot; NF55G disconnected. Restore firmware/main.py later.
First mount evidence is preserved before extra CMD0 commands; no auto remount.
"""
from src import main as runtime
from src.sd_sink import PicoSDSink
from src.sd_card import SDCard
from src.pico_clock import SystemClock
from src import sd_card as card_module

CASE = 'CMD0_NO_PRE_FF'
PROBE_MODE = 'CLOCKS_ONLY'
CASES = {'BASELINE': (0, False), 'DELAY_ONLY': (500, False),
         'CS_ONLY': (0, True), 'DELAY_AND_CS': (500, True),
         'CMD0_NO_PRE_FF': (0, False)}
diagnostic_report = None
failed_card = None


class ObservedSDCard(SDCard):
    def __init__(self, *args, **kwargs):
        global failed_card
        try:
            super().__init__(*args, **kwargs)
        except OSError:
            failed_card = self
            raise


def run_post_failure_probe(app, snapshot, factory=None, mode='REBUILD', retained_card=None):
    report = {'first_startup': dict(snapshot), 'results': [], 'error': None,
              'skipped': None, 'baudrate': 400000, 'delay_ms': 50}
    report['mode'] = mode
    report['attempts'] = 1 if mode in ('RETRY_ONLY', 'CLOCKS_ONLY') else 10
    report['extra_idle_bytes'] = 16 if mode in ('CLOCKS_ONLY', 'REBUILD') else 0
    if mode in ('RETRY_ONLY', 'CLOCKS_ONLY'):
        report['delay_ms'] = 0
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
        if mode in ('RETRY_ONLY', 'CLOCKS_ONLY'):
            if retained_card is None:
                report['skipped'] = 'NO_RETAINED_CARD'
                return report
            card = retained_card
            if mode == 'CLOCKS_ONLY':
                card.cs(1)
                for _ in range(16):
                    card.spi.write(b'\xff')
        elif mode == 'REBUILD':
            card = (factory or create_cmd0_probe)()
        else:
            raise ValueError('unknown probe mode')
        report['results'] = card.diagnose_cmd0_multi(
            attempts=report['attempts'], delay_ms=report['delay_ms'])
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
    global diagnostic_report, failed_card
    failed_card = None
    delay, early_cs = CASES[CASE]
    SDCard.CMD0_PRE_DUMMY = CASE != 'CMD0_NO_PRE_FF'
    original = runtime.PicoSDSink
    original_card = card_module.SDCard
    card_module.SDCard = ObservedSDCard
    runtime.PicoSDSink = lambda: PicoSDSink(startup_delay_ms=delay, cs_before_spi=early_cs)
    try:
        app = runtime.create_fixture_app()
    finally:
        runtime.PicoSDSink = original
        card_module.SDCard = original_card
    runtime.startup_sd_diagnostic['case'] = CASE
    runtime.startup_sd_diagnostic['cmd0_pre_dummy'] = SDCard.CMD0_PRE_DUMMY
    runtime.startup_sd_diagnostic['probe_mode'] = PROBE_MODE
    diagnostic_report = run_post_failure_probe(app, runtime.startup_sd_diagnostic,
                                              mode=PROBE_MODE, retained_card=failed_card)
    print('CMD0_DIAGNOSTIC_REPORT', diagnostic_report)
    app.run()


if __name__ == '__main__':
    main()
