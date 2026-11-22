"""Host個体照合・全Flash退避・候補配置。通常起動は別工程。"""
import hashlib,json
from parent_deploy import OUT,MAN,PICO,run
serial=MAN['host_serial']
info=run([PICO,'info','-a','--ser',serial])
if '0xbfcf2edb84b0b37f' not in info.lower() or 'bootsel' not in info:raise RuntimeError('Host identity/mode mismatch')
(OUT/'host_before_info.txt').write_text(info,encoding='utf-8')
backup=OUT/'backup/host_flash_before.bin'
if backup.exists():raise RuntimeError('backup exists')
run([PICO,'save','-a','-v',backup,'--ser',serial])
b=backup.read_bytes()
(OUT/'host_flash_backup.json').write_text(json.dumps({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'verify':'picotool save -a -v successful'},indent=2),encoding='utf-8')
uf2=OUT/MAN['host_candidate']['file']
if hashlib.sha256(uf2.read_bytes()).hexdigest()!=MAN['host_candidate']['sha256']:raise RuntimeError('UF2 mismatch')
run([PICO,'load','-v',uf2,'--ser',serial])
after=run([PICO,'info','-a','--ser',serial])
if MAN['host_candidate']['version'] not in after or '0xbfcf2edb84b0b37f' not in after.lower():raise RuntimeError('post load mismatch')
(OUT/'host_after_info.txt').write_text(after,encoding='utf-8')
print('HOST_DEPLOY_VERIFIED_BOOTSEL',flush=True)
