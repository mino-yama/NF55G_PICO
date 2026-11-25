from collections import Counter
from pathlib import Path, PurePosixPath
import subprocess


selected = {
    '.gitattributes',
    'docs/ATE_Command_Master.md',
    'docs/CHANGELOG.md',
    'docs/Open_Issues.md',
    'docs/Test_Specification.md',
}
documents = {'.md', '.pdf', '.txt', '.png', '.json', '.jsonl', '.log', '.csv', '.bin'}
folders = (
    'docs/ADC_Decimal_Hardware_Test_20261125/run_02/',
    'docs/QR_Hardware_Integration_20261123_01/',
    'docs/USB_Host_Reset_Study_20261121/',
)
untracked = subprocess.check_output(['git', 'ls-files', '-z', '--others', '--exclude-standard'])
staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'])
for entry in (untracked + staged).split(b'\0'):
    if not entry:
        continue
    name = entry.decode('utf-8')
    path = PurePosixPath(name)
    if not name.startswith(folders) or path.suffix not in documents:
        continue
    if any(part.startswith('candidate_') for part in path.parts):
        continue
    if path.name in ('operations.jsonl', 'deployment.jsonl', 'flash_before.bin'):
        continue
    selected.add(name)

assert sum(name.endswith('.csv') for name in selected) == 400
assert any(name.endswith('/csv_manifest.json') for name in selected)
Path('tmp/document_commit_20261125.paths').write_bytes(b''.join(
    name.encode('utf-8') + b'\0' for name in sorted(selected)))
print(len(selected), 'files', Counter(PurePosixPath(name).suffix for name in selected))
