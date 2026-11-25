from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path.cwd()))
from tests.test_qr_ss_workflow import QRSSWorkflowTests, record


folder = Path('docs/QR_Hardware_Integration_20261123_01/Production_Label_Retest_20261125')
expected = json.loads((folder / 'expected.json').read_text(encoding='utf8'))
frame_a = record(100, expected['A']['payload'])
frame_b = record(101, expected['B']['payload'])
cases = (
    ('complete_frame_waiting_before_scan', frame_a, frame_b),
    ('frame_spans_scan_boundary_at_parent', frame_a[:64], frame_a[64:] + frame_b),
    ('complete_old_frame_reaches_parent_after_scan', b'', frame_a + frame_b),
)
rows = []
for scenario, before, after in cases:
    app, uart, port, clock = QRSSWorkflowTests().make()
    port.rx.extend(before)
    armed = app.execute_ate_line('QR_SCAN 60000')
    token = armed.split(':')[-1]
    port.rx.extend(after)
    app.service_once()
    received = app.execute_ate_line('QR_GET? ' + token)
    preview = app.execute_ate_line('QR_DATA? ' + token)
    rows.append({'case': scenario, 'bytes_waiting_before_qr_scan': len(before),
                 'bytes_arrived_after_qr_scan': len(after), 'qr_get_reply': received,
                 'qr_data_reply': preview, 'nf55g_transmissions': len(uart.tx_log)})

assert rows[0]['qr_get_reply'].endswith(expected['B']['payload'])
assert rows[1]['qr_get_reply'] == 'ERR:QR_FRAME'
assert rows[2]['qr_get_reply'].endswith(expected['A']['payload'])
assert rows[2]['qr_data_reply'].endswith(expected['A']['ss_data_hex'])
assert all(row['nf55g_transmissions'] == 0 for row in rows)
output = folder / 'QR_Delayed_Frame_Replay_Rev0.json'
with output.open('x', encoding='utf8') as file:
    json.dump({'scope': 'Host Mock with synthetic QR HOST UART frame arrival timing; physical timing unmeasured',
               'cases': rows}, file, indent=2)
    file.write('\n')
print(output)
