"""完成した診断候補と、書込み前の実機停止点を記録する。"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
candidate = json.loads((BASE / 'Timeout_Snapshot_Candidate/manifest.json').read_text(encoding='utf-8'))
status_path = BASE / 'Current_Status.json'
status = json.loads(status_path.read_text(encoding='utf-8'))
status.update(candidate_state='unit 465 pass; ARM/ELF/UF2 verified; not deployed; awaiting isolated BOOTSEL',
              parent_running=False, parent_external_pio_active=False,
              parent_external_pins='input; verified stopped before flash preparation')
status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
manifest_path = ROOT / 'firmware/usb_submcu_external_meter_host/build_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['timeout_snapshot_candidate'] = dict(candidate, record='docs/Parent_Host_Integration_20261122_01/Timeout_Snapshot_Diagnostic_Rev0.md')
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report_path = BASE / 'Timeout_Snapshot_Diagnostic_Rev0.md'
report = report_path.read_text(encoding='utf-8')
report = report.replace('親は通常RAM runtime稼働、', '親は書込み準備のためruntime停止・外部PIO SM4/5停止・外部端子入力化、')
report = report.replace('ARMビルド進行中、未配置。', 'ARMビルド成功、ELFのCDC callback wrapperとsnapshot文字列・UF2 metadata/SHA照合済み、未配置。')
report += '\n## .22.2 候補固定\n\nUF2 95,232 byte、SHA256 `ebbb7f99e09524a7cd89cb5ac7fb44c70d1be931358b8141a2135c888410c847`。[候補manifest](Timeout_Snapshot_Candidate/manifest.json)、[ARM build](Timeout_Snapshot_Build_Native.log)。親RUNNING=False、SM4=False、SM5=False、Logger=Falseを実機照合後、Host単独BOOTSEL準備を依頼。実機版はまだ.22.1であり、候補を実機検証済みとは扱わない。\n'
report_path.write_text(report, encoding='utf-8')
for name in ('CHANGELOG.md', 'Test_Specification.md', 'Software_Module_Interface.md'):
    path = ROOT / 'docs' / name
    text = path.read_text(encoding='utf-8')
    text = text.replace('ARM build進行中・未配置', 'ARM build/ELF/UF2照合成功・未配置')
    path.write_text(text, encoding='utf-8')
readme = ROOT / 'firmware/usb_submcu_external_meter_host/README.md'
text = readme.read_text(encoding='utf-8')
note = 'Candidate `meter-host-relay-20261122.2` records RX length, TX/response completion flags and the final four RX bytes on TIMEOUT. All 465 tests and ARM/ELF/UF2 checks pass. It is not deployed; the actual .22.1 firmware reproduced READ timeout at both 2 s and 10 s deadlines. See [latest diagnostic](../../docs/Parent_Host_Integration_20261122_01/Timeout_Snapshot_Diagnostic_Rev0.md).\n\n'
if note not in text:
    pos = text.find('\n') + 1
    text = text[:pos] + '\n' + note + text[pos:]
    readme.write_text(text, encoding='utf-8')
print('CANDIDATE_READY_RECORDED')
