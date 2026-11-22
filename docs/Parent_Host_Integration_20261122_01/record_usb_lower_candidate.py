"""下位USB診断の検証記録を、既存の案件文書へ反映する。"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
note = ('2026-11-22 CDC下位診断: 実機.22.2の初回IDNがTIMEOUT_RX0_T1_C0_XNONE|1となった。'
        '自動再送なし・fault保持。候補.22.3は受信関数の戻り後に対象bulk INのNAK/PID/転送状態を観測し、'
        'TIMEOUT Eだけへ追記する。vendor原典・転送制御・fault規則は変更しない。'
        'Host/Mock全467件成功（19.094秒）、ARMビルド確認中・実機未配置。'
        '[記録](Parent_Host_Integration_20261122_01/USB_Lower_Diagnostic_Rev0.md)。\n\n')
for name in ('CHANGELOG.md', 'Test_Specification.md', 'Software_Module_Interface.md', 'Open_Issues.md'):
    path = ROOT / 'docs' / name
    text = path.read_text(encoding='utf-8')
    if note not in text:
        first = text.find('\n') + 1
        path.write_text(text[:first] + '\n' + note + text[first:], encoding='utf-8')
path = BASE / 'Current_Status.json'
status = json.loads(path.read_text(encoding='utf-8'))
status.update(candidate='meter-host-relay-20261122.3',
              candidate_state='unit/mock 467 pass; ARM build in progress; not deployed',
              latest_report='USB_Lower_Diagnostic_Rev0.md')
path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('LOWER_DIAGNOSTIC_RECORDED')
