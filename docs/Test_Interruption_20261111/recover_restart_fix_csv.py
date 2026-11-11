"""終了済み試行CSVを分割回収し、SD/PCのhashとファイル分離を検証する。"""
import csv
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import time
import serial
from mpremote.transport_serial import SerialTransport

FOLDER = Path(__file__).parent


def main():
    seq_path = sorted(FOLDER.glob('Restart_Fix_Sequence_*.json'))[-1]
    seq = json.loads(seq_path.read_text(encoding='utf-8'))
    assert seq['completed'], 'Sequence incomplete'
    stamp = seq_path.stem.replace('Restart_Fix_Sequence_', '')
    out = FOLDER / ('verified_' + stamp)
    out.mkdir()
    report = {'sequence': seq_path.name, 'files': [], 'completed': False}
    repl = SerialTransport('COM6', wait=2)
    try:
        repl.enter_raw_repl(soft_reset=False)
        assert repl.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()") == '69f7d45962cfdfad'
        stdout, stderr = repl.exec_raw("""
import os, json, binascii, hashlib
paths = []
for bank in ('BANK_A', 'BANK_B'):
    for name in os.listdir('/sd/' + bank):
        if name.endswith('.csv') and '_T' in name:
            paths.append('/sd/' + bank + '/' + name)
print(json.dumps(sorted(paths)))
""")
        assert not stderr, stderr
        paths = json.loads(stdout.decode())
        # 今回は初回配置。旧日時名のログを回収対象に混ぜない。
        assert len(paths) == 3, paths
        ids = []
        for path in paths:
            raw, error = repl.exec_raw("data=open(" + repr(path) + ",'rb').read(); print(json.dumps({'size':len(data),'sha256':binascii.hexlify(hashlib.sha256(data).digest()).decode()}))")
            assert not error, error
            meta = json.loads(raw.decode())
            data = bytearray()
            for offset in range(0, meta['size'], 256):
                raw, error = repl.exec_raw('print(binascii.hexlify(data[' + str(offset) + ':' + str(offset + 256) + ']).decode())')
                assert not error, error
                chunk = bytes.fromhex(raw.decode().strip())
                assert len(chunk) == min(256, meta['size'] - offset)
                data.extend(chunk)
            assert hashlib.sha256(data).hexdigest() == meta['sha256']
            target = out / Path(path).name
            target.write_bytes(data)
            rows = list(csv.DictReader(io.StringIO(data.decode())))
            counts = sorted(set(len(row) for row in csv.reader(io.StringIO(data.decode()))))
            assert counts == [14], counts
            starts = [r for r in rows if r['event'] == 'TRIAL_START']
            endings = [r for r in rows if r['event'] == 'TRIAL_END_REQUEST']
            assert len(starts) == 1 and len(endings) == 1
            trial_id = starts[0]['detail'].split('trial_id=')[1]
            assert path.endswith('_' + trial_id + '.csv')
            ids.append(trial_id)
            frames = []
            for row in rows:
                if row['category'] == 'NF55' and row['event'] == 'RAW':
                    frame = bytes.fromhex(row['raw_hex'])
                    if frame.startswith(b'\x02'):
                        bcc = 0
                        for byte in frame[1:-2]:
                            bcc ^= byte
                        assert int(frame[-2:], 16) == bcc
                        frames.append({'cmd': frame[1:3].decode(), 'direction': row['direction'], 'bcc_ok': True})
            transactions = [dict(cmd=r['cmd'], result=r['result'], cmd_retry=r['cmd_retry'],
                                 rsp_retry=r['rsp_retry'], detail=r['detail'])
                            for r in rows if r['event'] == 'TRANSACTION']
            assert all(t['result'] == 'OK' and t['cmd_retry'] == '0' and t['rsp_retry'] == '0' for t in transactions)
            report['files'].append(dict(path=path, local=target.name, trial_id=trial_id,
                                       size=len(data), sha256=meta['sha256'], sd_pc_hash_match=True,
                                       data_rows=len(rows), column_counts=counts, ending=endings[0]['detail'],
                                       frames=frames, transactions=transactions))
            print('Verified:', path, len(data), 'bytes', flush=True)
        assert len(set(ids)) == 3
        for i, item in enumerate(report['files']):
            expected = 'NEXT_TEST_START' if i < 2 else 'TEST_END'
            assert item['ending'] == 'trial_id=' + item['trial_id'] + ';reason=' + expected
            expected_cmds = ['SC', 'D0'] if i == 0 else ['D0']
            assert [t['cmd'] for t in item['transactions']] == expected_cmds
        report['completed'] = True
    except Exception as exc:
        report['error'] = repr(exc)
        raise
    finally:
        (out / 'csv_analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        repl.exit_raw_repl()
        repl.serial.write(b'\x04')
        time.sleep(2)
        repl.close()
    with serial.Serial('COM20', 115200, timeout=2, write_timeout=2) as port:
        for command in ('*IDN?', 'COMM_STATUS?', 'SD_STATUS?', 'PICO_SELF_CHECK?', 'LOG_DROP_COUNT?'):
            time.sleep(0.15)
            port.write((command + '\r\n').encode())
            answer = port.read_until(b'\n').decode().strip()
            report.setdefault('after_restart', []).append(dict(command=command, response=answer))
            print(command, '=>', answer, flush=True)
            if command == '*IDN?':
                assert answer.startswith('NF55G_PICO_FIXTURE,')
            elif command == 'COMM_STATUS?':
                assert answer == 'OK:state=IDLE'
            elif command == 'PICO_SELF_CHECK?':
                assert answer.startswith('OK:')
            elif command == 'LOG_DROP_COUNT?':
                assert answer == '0'
            else:
                assert answer == 'OK'
    (out / 'csv_analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Evidence:', out, flush=True)


if __name__ == '__main__':
    main()
