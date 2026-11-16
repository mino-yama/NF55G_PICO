import hashlib,json,shutil,struct
from pathlib import Path
root=Path.cwd();fw=root/'firmware/usb_submcu_host_probe'
out=root/'docs/USB_SubMCU_Host_Preparation_20261111/Hardware_Modification_Power_20261111/QR_Evaluation_20261114/Decoder_FW_20261114'
old_checks=[]
for name in ['qr-uart-20261111.1','qr-probe-20261111.1-ram','qr-uart-20261114.1']:
 base=fw/'releases'/name;m=json.loads((base/'manifest.json').read_text(encoding='utf8'))
 for f in m['files']:
  b=(base/f['file']).read_bytes()
  assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],f['file']
 old_checks.append({'release':name,'verified_files':len(m['files'])})
release=fw/'releases/qr-uart-20261114.2';release.mkdir(exist_ok=False)
source=release/'source';target=source/'firmware/usb_submcu_host_probe';target.mkdir(parents=True)
for name in ['CMakeLists.txt','README.md','main.c','qr_alt_decoder.c','qr_alt_decoder.h','newlib_malloc_lock.c','tusb_config.h']:
 shutil.copy2(fw/name,target/name)
for name in ['boards','vendor']:shutil.copytree(fw/name,target/name)
(source/'scripts').mkdir()
for name in ['build_usb_submcu_host_probe.ps1','usb_submcu_probe_capture.py','usb_submcu_probe_log.py']:
 shutil.copy2(root/'scripts'/name,source/'scripts'/name)
(source/'tests').mkdir()
for name in ['test_usb_submcu_probe_log.py','test_usb_submcu_qr_alt_decoder.py']:
 shutil.copy2(root/'tests'/name,source/'tests'/name)
shutil.copytree(root/'tests/fixtures/usb_submcu_qr_alt',source/'tests/fixtures/usb_submcu_qr_alt')
for ext in ['uf2','elf','bin']:
 shutil.copy2(fw/f'build_uart_gp0/usb_submcu_host_probe.{ext}',release/f'usb_submcu_qr_uart_probe.{ext}')
uf2=(release/'usb_submcu_qr_uart_probe.uf2').read_bytes()
assert hashlib.sha256(uf2).hexdigest()=='419fadbc4d7e79704ff8703574d59524e4bea5262991f10eef71a2c5441d61f3'
assert len(uf2)%512==0
arm=[];aux=[]
for i in range(len(uf2)//512):
 block=uf2[512*i:512*(i+1)];h=struct.unpack_from('<8I',block)
 assert h[:2]==(0x0a324655,0x9e5d5157) and struct.unpack_from('<I',block,508)[0]==0x0ab16f30
 (arm if h[7]==0xe48bff59 else aux).append(h)
assert len(aux)==1 and aux[0][2:]==(0xa000,0x10ffff00,256,0,2,0xe48bff57)
assert all(h[5]==i and h[6]==len(arm) and h[4]==256 for i,h in enumerate(arm))
files=[]
for p in sorted(release.rglob('*')):
 if p.is_file():
  b=p.read_bytes();files.append({'file':p.relative_to(release).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
manifest={'date_jst':'2026-11-14','version':'qr-uart-20261114.2','program':'usb_submcu_qr_uart_probe','operational_target_usb_serial':'A06FEA01012EC137','profile':{'vid':'E851','pid':'1001','descriptor_bytes':63,'output_chars':35,'charset':'ASCII alphanumeric and hyphen','input_mode':'left Alt + 5 decimal keypad digits','suffix':'Enter','diagnostic_idle_timeout_ms':5000,'arm_decoder_state_bytes':52,'native_decoder_state_bytes':56,'log_capacity':1024,'ram_log_bytes':77844,'uart_tx':0,'baud':115200,'format':'8N1','usb_dp':12,'usb_dm':13},'status':{'built':True,'flashed':False,'hardware_acceptance':False},'checks':{'host_mock_count':346,'skipped':0,'native_c_decoder_tests':16,'log_parser_tests':29,'build_exit':0,'uf2_blocks':len(uf2)//512,'old_release_checks':old_checks},'files':files}
(release/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
for f in files:
 b=(release/f['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==f['sha256']
summary={'release':str(release.relative_to(root)),'files':len(files),'uf2_bytes':len(uf2),'uf2_sha256':hashlib.sha256(uf2).hexdigest(),'old_releases':old_checks,'native_test_compiler':json.loads((out/'Native_Compiler_Source.json').read_text(encoding='utf-8-sig'))}
(out/'Release_Verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
