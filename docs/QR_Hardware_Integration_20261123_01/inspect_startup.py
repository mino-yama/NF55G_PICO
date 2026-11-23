"""RST前後を混同せず、保存済みUARTをboot境界ごとに検査する。"""
import json
from pathlib import Path
import sys
from capture_and_inspect import inspect, probe


def inspect_boot_segments(raw):
    starts = [0]
    offset = 0
    for line in raw.splitlines(keepends=True):
        clean = line.rstrip(b'\r\n').lstrip(b'\0')
        if len(clean) == 153 and clean.startswith(b'@'):
            try:
                record = probe.decode_record(bytes.fromhex(clean[1:].decode('ascii')))
            except (ValueError, UnicodeError):
                record = None
            if record and record['kind'] == 'boot' and record['seq'] == 0 and offset:
                starts.append(offset)
        offset += len(line)
    ends = starts[1:] + [len(raw)]
    return [dict(start_byte=a, end_byte=b, result=inspect(raw[a:b], nf55g_profile=True))
            for a, b in zip(starts, ends)]


if __name__ == '__main__':
    out = Path(sys.argv[1])
    segments = inspect_boot_segments((out / 'qr_host.raw').read_bytes())
    (out / 'startup_segments.json').write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding='utf-8')
    for segment in segments:
        result = segment['result']
        print(json.dumps({k: v for k, v in result.items() if k not in ('records', 'health')}, ensure_ascii=False))
        print('health_last', result['health'][-1:])
        print('startup_events', [r for r in result['records'] if r['kind'] != 'host_health' and r['kind'] != 'qr_text'])
