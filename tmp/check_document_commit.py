from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


paths = [name.decode('utf8') for name in Path('tmp/document_commit_20261125.paths').read_bytes().split(b'\0') if name]
staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'])
assert set(paths) == {name.decode('utf8') for name in staged.split(b'\0') if name}
assert all(name.startswith('docs/') or name == '.gitattributes' for name in paths)
assert not any(Path(name).suffix in ('.py', '.c', '.h', '.elf', '.uf2') for name in paths)
manifest_path, = (Path(name) for name in paths if name.endswith('/csv_manifest.json'))
manifest = json.loads(manifest_path.read_text(encoding='utf8'))
assert manifest['complete'] and manifest['csv_count'] == 400
expected = {(manifest_path.parent / 'csv' / row['filename']).as_posix(): row['sha256'] for row in manifest['files']}
preserved = sorted(set(expected) | {name for name in paths if name.endswith(('.bin', '/csv_usb_raw.log'))})
objects = subprocess.run(['git', 'cat-file', '--batch'], check=True, capture_output=True,
                         input=''.join(f':{name}\n' for name in preserved).encode('utf8')).stdout
offset = 0
for name in preserved:
    end = objects.index(b'\n', offset)
    oid, kind, size = objects[offset:end].split()
    assert kind == b'blob'
    size = int(size)
    raw = objects[end + 1:end + 1 + size]
    assert raw == Path(name).read_bytes(), name
    if name in expected:
        assert hashlib.sha256(raw).hexdigest() == expected[name], name
    offset = end + size + 2
print('Staged:', len(paths), Counter(Path(name).suffix for name in paths))
print('Original bytes verified:', len(preserved), 'including', len(expected), 'CSV SHA-256 values')
