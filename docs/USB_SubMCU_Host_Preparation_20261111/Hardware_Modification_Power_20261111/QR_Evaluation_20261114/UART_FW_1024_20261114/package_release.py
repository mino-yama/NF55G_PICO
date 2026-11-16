import hashlib,json,shutil,struct
from pathlib import Path
root=Path.cwd()
fw=root/'firmware/usb_submcu_host_probe'
out=root/'docs/USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/UART_FW_1024_20261114'
old_checks=[]
for name in ['qr-uart-20261111.1','qr-probe-20261111.1-ram']:
 base=fw/'releases'/name
 m=json.loads((base/'manifest.json').read_text(encoding='utf8'))
 for f in m['files']:
  p=base/f['file']; b=p.read_bytes()
  assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],str(p)
 old_checks.append({'release':name,'verified_files':len(m['files'])})
release=fw/'releases/qr-uart-20261114.1'
assert not (release/'manifest.json').exists(), 'Preserve a completed release'
release.mkdir(exist_ok=True)
source=release/'source';source.mkdir(exist_ok=True)
for name in ['CMakeLists.txt','README.md','main.c','newlib_malloc_lock.c','tusb_config.h']:
 shutil.copy2(fw/name,source/name)
for name in ['boards','vendor']:
 shutil.copytree(fw/name,source/name,dirs_exist_ok=True)
for name in ['build_usb_submcu_host_probe.ps1','usb_submcu_probe_capture.py','usb_submcu_probe_log.py']:
 shutil.copy2(root/'scripts'/name,source/name)
shutil.copy2(root/'tests/test_usb_submcu_probe_log.py',source/'test_usb_submcu_probe_log.py')
for ext in ['uf2','elf','bin']:
 shutil.copy2(fw/f'build_uart_gp0/usb_submcu_host_probe.{ext}',release/f'usb_submcu_qr_uart_probe.{ext}')
uf2=(release/'usb_submcu_qr_uart_probe.uf2').read_bytes()
assert hashlib.sha256(uf2).hexdigest()=='0ce5168e546f25431e51922fb6fd0728a38697efb65937b9532da9f9aece1b81'
assert len(uf2)%512==0
arm_blocks=[]
aux_blocks=[]
for i in range(len(uf2)//512):
 block=uf2[512*i:512*(i+1)]
 assert struct.unpack_from('<II',block)==(0x0A324655,0x9E5D5157)
 assert struct.unpack_from('<I',block,508)[0]==0x0AB16F30
 header=struct.unpack_from('<8I',block)
 if header[7]==0xE48BFF59:
  arm_blocks.append(header)
 else:
  aux_blocks.append(header)
assert len(aux_blocks)==1 and aux_blocks[0][2:]==(0xA000,0x10FFFF00,256,0,2,0xE48BFF57)
assert all(h[5]==i and h[6]==len(arm_blocks) and h[4]==256
           for i,h in enumerate(arm_blocks))
files=[]
for p in sorted(release.rglob('*')):
 if p.is_file():
  b=p.read_bytes();files.append({'file':p.relative_to(release).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
manifest={'date_jst':'2026-11-14','program':'usb_submcu_qr_uart_probe','version':'qr-uart-20261114.1','record_capacity':1024,'ram_log_bytes':77844,'record_bytes':76,'uart':{'tx_pin':0,'baud':115200,'format':'8N1','rx':False},'pio_usb':{'dp':12,'dm':13},'status':{'built':True,'flashed':False,'qr_text_verified':False,'hardware_acceptance':False},'checks':{'host_mock_passed':326,'build_exit':0,'uf2_blocks_verified':len(uf2)//512,'old_release_checks':old_checks},'files':files}
(release/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
(out/'Preservation_Check.json').write_text(json.dumps(old_checks,indent=2),encoding='utf8')
summary={'release':str(release.relative_to(root)),'files':len(files),'uf2_bytes':len(uf2),'uf2_sha256':hashlib.sha256(uf2).hexdigest(),'old_releases':old_checks}
(out/'Release_Verification.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
print(json.dumps(summary,indent=2))
