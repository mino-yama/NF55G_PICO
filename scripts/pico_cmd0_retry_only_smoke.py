"""Warm-only retained-object test with injected CMD0 error; not cold evidence."""
import os
import sd_cmd0_probe as probe
from src.sd_card import SDCard
from src.sd_sink import PicoSDSink
from machine import SPI, Pin

MODE = globals().get('SMOKE_MODE', 'RETRY_ONLY')

assert os.statvfs('/sd')[2] == os.statvfs('/')[2], 'requires unmounted SD'
SDCard.CMD0_PRE_DUMMY = False
original = SDCard.cmd
calls = []
def injected(self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    calls.append((args[0], result))
    return 31 if args[0] == 0 else result
spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
SDCard.cmd = injected
try:
    try:
        probe.ObservedSDCard(spi, Pin(17))
    except OSError as exc:
        assert 'CMD0 failed: 31' in str(exc)
    else:
        raise AssertionError('injection did not run')
finally:
    SDCard.cmd = original
assert probe.failed_card.spi is spi
print('INJECTED_FAILURE_REAL_RESPONSES', calls)
class Context:
    def _comm_busy(self):
        return False
app = Context()
app.logger = Context()
app.logger.sd_sink = Context()
app.logger.sd_sink.mounted = False
snapshot = dict(stage='CARD_INIT', error='CMD0 failed: 31', mounted=False)
report = probe.run_post_failure_probe(app, snapshot, mode=MODE,
                                      retained_card=probe.failed_card)
print('WARM_INJECTED_RETRY_REPORT', report)
assert report['error'] is None and len(report['results']) == 1
assert report['results'][0][4]
sink = PicoSDSink()
try:
    sink.mount()
    with open('/sd/BANK_A/20260910_114306.csv') as source:
        assert len(source.readlines()) == 65
    print('POST_PROBE_MOUNT_READBACK', sink.status)
finally:
    if sink.mounted:
        os.umount('/sd')
print(MODE + '_WARM_INJECTION_PASS')
