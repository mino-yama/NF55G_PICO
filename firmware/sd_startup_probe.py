"""Temporary cold-start investigation entry; copy to /main.py for each case.

Restore firmware/main.py after investigation. NF55G remains disconnected.
No automatic retries or experimental setting changes within one boot.
"""
from src import main as runtime
from src.sd_sink import PicoSDSink

# Change only CASE between power cycles. Each case requires a real cold start.
CASE = 'DELAY_AND_CS'
CASES = {
    'BASELINE': (0, False),
    'DELAY_ONLY': (500, False),
    'CS_ONLY': (0, True),
    'DELAY_AND_CS': (500, True),
}
delay_ms, early_cs = CASES[CASE]


def probe_sink():
    return PicoSDSink(startup_delay_ms=delay_ms, cs_before_spi=early_cs)


runtime.PicoSDSink = probe_sink
app = runtime.create_fixture_app()
runtime.startup_sd_diagnostic['case'] = CASE
app.run()
