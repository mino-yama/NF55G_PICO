"""停止済み実機CSVを読戻し、hash・列・D1/READ相関をPCで照合する。"""
import csv
from collections import Counter
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import statistics
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT))
from src.external_instrument_link import FrameReader


def run(args):
    result = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, timeout=40)
    with (OUT / 'export_operations.jsonl').open('a', encoding='utf-8') as log:
        log.write(json.dumps({'args': [str(x) for x in args], 'code': result.returncode,
            'stdout': result.stdout.decode('utf-8', 'replace'), 'stderr': result.stderr.decode('utf-8', 'replace')}) + '\n')
    assert result.returncode == 0, result.stderr
    return result.stdout.decode('utf-8')


if __name__ == '__main__':
    assert not (OUT / 'verification.json').exists()
    data = json.loads((OUT / 'result.json').read_text())
    assert data['status'] == 'COEXIST50_SUCCESS'
    path = data['parent']['log_path']
    base = [ROOT / '.venv/Scripts/python.exe', '-m', 'mpremote', 'connect', 'COM6', 'resume']
    code = "import hashlib,binascii,os,json; assert not app.logger.active and len(app.logger.queue)==0; p=" + repr(path) + "; h=hashlib.sha256(); f=open(p,'rb')\nwhile True:\n b=f.read(512)\n if not b: break\n h.update(b)\nf.close(); print('SD_CSV|'+json.dumps({'path':p,'bytes':os.stat(p)[6],'sha256':binascii.hexlify(h.digest()).decode()}))"
    text = run(base + ['exec', code])
    remote = json.loads(next(line.split('|', 1)[1] for line in text.splitlines() if line.startswith('SD_CSV|')))
    local = OUT / Path(path).name
    run(base + ['fs', 'cp', ':' + path, local])
    raw = local.read_bytes()
    assert len(raw) == remote['bytes'] and hashlib.sha256(raw).hexdigest() == remote['sha256']
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8'))))
    assert len(rows[0]) == 14 and all(len(row) == 14 for row in rows)
    assert len(rows) - 1 == data['parent']['sd_stats']['writes']
    records = [dict(zip(rows[0], row)) for row in rows[1:]]
    d1 = [r for r in records if r['category'] == 'NF55' and r['event'] == 'TRANSACTION']
    assert len(d1) == 50
    assert all(r['cmd'] == 'D1' and r['result'] == 'OK' and r['cmd_retry'] == r['rsp_retry'] == '0' for r in d1)
    read_rows = [r for r in records if r['category'] == 'ATE' and r['event'] == 'RESULT' and r['detail'] == 'EXT_QUERY 2000 :READ?']
    assert len(read_rows) == 50
    measures = []
    for row in read_rows:
        prefix, name, count, encoded = row['result'].split(':', 3)
        value = bytes.fromhex(encoded)
        assert (prefix, name) == ('OK', 'EXT_RX') and int(count) == len(value) and value.endswith(b'\r\n')
        measures.append(Decimal(value.decode('ascii').strip()))
    reader = FrameReader()
    sent = reader.feed(bytes.fromhex(data['parent']['external_tx_hex']))
    assert reader.errors == 0
    queries = [f for f in sent if f['kind'] == 'Q']
    assert len(queries) == 50 and all(f['payload'] == b':READ?' for f in queries)
    frames = json.loads((OUT / 'Burst_01/host_frames.json').read_text())
    counts = Counter(f['kind'] for f in frames)
    assert counts == Counter({'A': 50, 'T': 50, 'R': 50})
    for request in queries:
        received = [f for f in frames if f['request'] == request['request'] and f['session'] == request['session'].hex()]
        assert [f['kind'] for f in received] == ['A', 'T', 'R']
    assert bytes.fromhex(data['parent']['nf_tx_hex']) == bytes.fromhex('02443103373606') * 51
    requests = json.loads((OUT / 'Burst_01/requests.json').read_text())
    timings = [r['elapsed_ms'] for r in requests if r['command_hex'].startswith(b'EXT_QUERY'.hex())]
    assert len(timings) == 50
    verification = {'csv': remote, 'local_file': local.name, 'hash_match': True,
        'data_rows': len(records), 'malformed_rows': 0, 'nf_d1_transaction_rows': len(d1),
        'read_result_rows': len(read_rows), 'host_kind_counts': dict(counts),
        'request_response_correlated': True, 'nf_d1_plus_ack_only': True,
        'measure_min_v': str(min(measures)), 'measure_max_v': str(max(measures)),
        'burst_ms': {'min': min(timings), 'median': statistics.median(timings), 'max': max(timings)},
        'sd_stats': data['parent']['sd_stats'], 'drop': data['parent']['drop'], 'queue': data['parent']['queue']}
    (OUT / 'verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
    print(json.dumps(verification, indent=2))
