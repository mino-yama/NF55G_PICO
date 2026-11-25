"""旧service_usb_rxと同じ64byte読出しで、新規境界回帰が失敗することを確認する。"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import test_external_meter_rx_service as regression

with tempfile.TemporaryDirectory(prefix='nf55g_legacy_rx_') as temporary:
    legacy = Path(temporary) / 'legacy.c'
    legacy.write_text('''#include "tusb.h"
#include "relay_cdc_rx.h"
void relay_cdc_rx_service(relay_host_t *host, uint8_t index, uint32_t now) {
    uint8_t bytes[64];
    if (tuh_cdc_read_available(index) > 0u) {
        uint32_t count = tuh_cdc_read(index, bytes, sizeof(bytes));
        if (count > 0u) relay_host_rx(host, bytes, count, now);
    }
}
''', encoding='ascii')
    real_run = regression.subprocess.run

    def compile_legacy(args, **kwargs):
        args = [str(legacy) if arg == str(regression.SOURCE / 'relay_cdc_rx.c') else arg for arg in args]
        return real_run(args, **kwargs)

    regression.subprocess.run = compile_legacy
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(regression.MeterRxServiceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # 旧処理で4 test method（境界2 subtestを含む）が失敗、deadline/emptyは成功する。
    if result.errors or len(result.failures) != 5:
        raise SystemExit('Unexpected legacy reproduction result')
    print('EXPECTED_LEGACY_FAILURES_CONFIRMED')
