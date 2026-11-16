"""完了した候補FWを旧配布物と別名で固定保存しhashを検証する。"""
import hashlib,json,shutil,struct
from pathlib import Path
root=Path.cwd()
def long(p): return Path('\\\\?\\'+str(p.resolve()))
case=Path(__file__).resolve().parent
release=root/'firmware/usb_submcu_host_probe/releases/qr-fixed-20261114.1'
if (release/'manifest.json').exists(): raise SystemExit('Final release already exists: do not overwrite')
old=root/'firmware/usb_submcu_host_probe/releases/qr-uart-20261114.2'
m=json.loads((old/'manifest.json').read_text(encoding='utf-8'))
for x in m['files']:
    f=long(old/x['file'])
    assert f.stat().st_size==x['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256'],x['file']
sources=[x['file'][7:] for x in m['files'] if x['file'].startswith('source/')]
sources+=['firmware/usb_submcu_host_probe/probe_stream.c','firmware/usb_submcu_host_probe/probe_stream.h','tests/test_usb_submcu_stream.py']
release.mkdir(exist_ok=True)
for rel in sorted(set(sources)):
    src=long(root/rel); dst=long(release/'source'/rel)
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists(): assert dst.read_bytes()==src.read_bytes()
    else: shutil.copyfile(src,dst)
for ext in ('uf2','elf','bin'):
    src=root/f'firmware/usb_submcu_host_probe/build_uart_continuous/usb_submcu_host_probe.{ext}'
    dst=release/f'usb_submcu_qr_uart_probe.{ext}'
    if dst.exists(): assert dst.read_bytes()==src.read_bytes()
    else: shutil.copyfile(src,dst)
raw=(release/'usb_submcu_qr_uart_probe.uf2').read_bytes()
assert len(raw)%512==0
# SDK2.2.0の補助ブロックをARMイメージの連番へ混ぜない。
oldraw=(old/'usb_submcu_qr_uart_probe.uf2').read_bytes()
assert raw[:512]==oldraw[:512]
families=set(); arm_blocks=len(raw)//512-1
for i in range(len(raw)//512):
    block=raw[i*512:(i+1)*512]; h=struct.unpack_from('<8I',block)
    assert h[:2]==(0x0a324655,0x9e5d5157) and struct.unpack_from('<I',block,508)[0]==0x0ab16f30
    assert h[2]&0x2000 and h[4]==256
    if i:
        assert h[2]==0x2000 and h[5]==i-1 and h[6]==arm_blocks and h[7]==0xe48bff59
        assert h[3]==0x10000000+(i-1)*256
    families.add(h[7])
assert families=={0xe48bff57,0xe48bff59}
files=[]
for f in sorted(long(release).rglob('*')):
    if f.is_file(): files.append(dict(file=f.relative_to(long(release)).as_posix(),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
manifest=dict(date_jst='2026-11-14',version='qr-fixed-20261114.1',operational_target_usb_serial='A06FEA01012EC137',built=True,flashed=False,hardware_acceptance=False,startup_wait_ms=3000,queue_records=64,lifetime_record_limit=None,raw_hid_output=False,host_mock_tests=354,skipped=0,uf2_blocks=len(raw)//512,family_ids=sorted(families),previous_release_files_verified=len(m['files']),files=files)
(release/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for x in files: assert hashlib.sha256(long(release/x['file']).read_bytes()).hexdigest()==x['sha256']
(case/'Release_Verification_Rev0.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(version=manifest['version'],files=len(files),uf2_bytes=len(raw),uf2_sha256=hashlib.sha256(raw).hexdigest(),previous_release_files_verified=len(m['files'])),indent=2))
