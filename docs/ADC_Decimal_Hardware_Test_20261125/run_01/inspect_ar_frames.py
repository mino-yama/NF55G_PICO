"""Validate saved AR response frames and report observed field changes."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.frame import parse_frame
from src.nf55_decode import decode_ar


def inspect_capture(path):
    raw = bytes.fromhex(path.read_text(encoding='utf-8'))
    frame = parse_frame(raw, expected_cmd='AR', expected_length=140)
    return {'source': str(path), 'frame_hex': frame.raw.hex().upper(),
            'fields': decode_ar(frame.data)}


def inspect_readback(before, after=None):
    before_capture = inspect_capture(before)
    report = {'before': before_capture}
    if after is not None:
        after_capture = inspect_capture(after)
        report['after'] = after_capture
        report['changed_fields'] = {
            name: {'before': value, 'after': after_capture['fields'][name]}
            for name, value in before_capture['fields'].items()
            if value != after_capture['fields'][name]
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path, help='file containing the complete AR response as hex')
    parser.add_argument('--after', type=Path, help='second complete AR response as hex')
    args = parser.parse_args()
    try:
        report = inspect_readback(args.before, args.after)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'AR capture rejected: {exc}\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
