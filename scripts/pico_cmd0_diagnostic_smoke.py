"""Warm diagnostic execution test, never evidence of a cold first attempt.

Use mpremote run (fresh raw interpreter), NF55G disconnected.
"""
import os
from sd_cmd0_probe import create_cmd0_probe
from src.sd_sink import PicoSDSink

# Never reset a mounted filesystem. This script requires an unmounted /sd.
assert os.statvfs('/sd')[2] == os.statvfs('/')[2], 'SD may be mounted; stop'
print('WARM_CMD0_DIAGNOSTIC_BEGIN')
card = create_cmd0_probe()
try:
    rows = card.diagnose_cmd0_multi(attempts=10, delay_ms=50)
    print('WARM_CMD0_RESULTS', rows)
    assert len(rows) == 10
    assert all(row[4] for row in rows), 'warm CMD0 failure'
finally:
    card.cs(1)
    card.spi.deinit()
sink = PicoSDSink()
try:
    sink.mount()
    print('POST_DIAGNOSTIC_MOUNT', sink.status, sink.usage())
    with open('/sd/BANK_A/20260910_094306.csv') as stream:
        lines = stream.readlines()
    assert len(lines) == 65
    print('EXISTING_CSV_READBACK', len(lines))
finally:
    if sink.mounted:
        os.umount('/sd')
print('WARM_CMD0_DIAGNOSTIC_PASS')
