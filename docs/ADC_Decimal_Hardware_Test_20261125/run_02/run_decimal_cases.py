"""Run the authorized decimal test once on the identified sample."""

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.frame import parse_frame
from src.nf55_decode import decode_ar

VALUES = ('0.50', '1.85', '1.86', '2.25')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remaining', action='store_true', help='use the checked post-0.50 AR capture')
    remaining = parser.parse_args().remaining
    source = '03_after_first_readonly.log' if remaining else '01_baseline.log'
    records = (HERE / source).read_text(encoding='utf-8').splitlines()
    if 'PROBE_COMPLETE' not in records:
        raise ValueError('Baseline did not complete')
    identity = next(json.loads(line.split('|', 1)[1]) for line in records if line.startswith('IDENTITY|'))
    if (identity['FW_REV'], identity['UNIT_SERIAL']) != ('S1.14B', '000001'):
        raise ValueError('Baseline is from a different sample')
    transactions = [json.loads(line.split('|', 1)[1]) for line in records if line.startswith('TRANSACTION|')]
    if [item['cmd'] for item in transactions] != ['D5', 'AR'] or not all(item['ok'] for item in transactions):
        raise ValueError('Expected D5 and a complete AR baseline')
    raw_hex = transactions[-1]['raw_response_hex']
    baseline = decode_ar(parse_frame(bytes.fromhex(raw_hex), 'AR', 140).data)
    if remaining:
        if baseline['AR_BATT_CHG_P1_REF_RAW'] != '00000000' or baseline['AR_BATT_CHG_P1_ADC'] != 1:
            raise ValueError('Unexpected AR capture after the first write')
        original = json.loads((HERE / 'baseline.json').read_text(encoding='utf-8'))['fields']
        if any(value != original[name] for name, value in baseline.items()
               if not name.startswith('AR_BATT_CHG_P1_')):
            raise ValueError('Non-target field changed in the first write')
    else:
        with (HERE / 'baseline.hex').open('x', encoding='ascii') as log:
            log.write(raw_hex + '\n')
        with (HERE / 'baseline.json').open('x', encoding='utf-8') as log:
            json.dump({'identity': identity, 'fields': baseline}, log, indent=2)
    values = VALUES[1:] if remaining else VALUES
    words = tuple(struct.pack('>f', float(value)).hex().upper() for value in values)
    params = f'adc_test_words={words!r}; adc_expected_baseline={baseline!r}'
    output = '04_remaining_cases.log' if remaining else '02_decimal_cases.log'
    with (HERE / output).open('xb') as log:
        run = subprocess.run([sys.executable, '-u', '-m', 'mpremote', 'connect', 'COM6', 'resume',
                              'exec', params, 'run', str(HERE / 'probe_parent.py')], cwd=ROOT,
                             stdout=log, stderr=subprocess.STDOUT, timeout=35)
    print('Requested decimal/VALUE8 pairs:', list(zip(values, words)))
    return run.returncode


if __name__ == '__main__':
    raise SystemExit(main())
