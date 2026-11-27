from pathlib import Path
import sys
import re
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.command_parser import parse_ate_command

commands = []
for circuit in ('DISCHG_I', 'BATT_CHG', 'BATT_V'):
    for point, dest in (('A', 'P1'), ('B', 'P2')):
        commands.extend((f'CAL_MEASURE_{circuit} {point} 4000 MD?',
                         f'CAL_MEASUREMENT_{circuit}? {point}',
                         f'CAL_WRITE_{circuit} {point} {dest}',
                         f'AD_VERIFY_{circuit} {dest}'))
for cmd in ('F1', 'INIC1', 'TRS0', 'H0', 'RN0', 'PR4', 'R3', 'R5'):
    commands.append('EXT_SEND 2500 ' + cmd)
for cmd in ('F?', 'INIC?', 'TRS?', 'H?', 'RN?', 'PR?', 'R?', 'MD?'):
    commands.append('EXT_QUERY 2500 ' + cmd)
commands += ['QR_SCAN 10000', 'QR_CANCEL', 'TEST_START', 'TEST_END', 'INFO_REFRESH',
             'FW_REV?', 'UNIT_REV?', 'UNIT_LOT?', 'UNIT_SERIAL?', 'PICO_SELF_CHECK?',
             'SD_STATUS?', 'LOG_DROP_COUNT?', 'COMM_STATUS?', 'HOST_INFO? METER']
for command in commands:
    parsed = parse_ate_command(command)
    assert parsed.category != 'UNKNOWN', command
path = ROOT / 'docs/ATE_Command_List_for_Test_Program_Rev3_20261126.md'
text = path.read_text(encoding='utf-8')
tables, expected = 0, None
for line in text.splitlines():
    if line.startswith('|'):
        count = len(line.strip('|').split('|'))
        if expected is None:
            tables += 1
            expected = count
        assert count == expected, line
    else:
        expected = None
for sec in ('10.4', '10.5', '14.16', '14.17'):
    assert f'### {sec} ' in text
assert 'Revision: Rev.3' in text and 'Date: 2026-11-26' in text
print(f'PASS: {len(commands)} command examples; {tables} Markdown tables; revision and added sections')
