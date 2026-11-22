"""2026-11-22 引継ぎ: 個体・旧ソース照合、全Flash退避後の親単一ファイル配置。"""
import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
PY=ROOT/'.venv/Scripts/python.exe'
PICO=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
BASE=[str(PY),'-m','mpremote','connect','COM6','resume']
MAN=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
LOG=json.loads((OUT/'operations.json').read_text(encoding='utf-8')) if (OUT/'operations.json').exists() else []
def run(args,timeout=35,allow_disconnect=False):
    try:
        p=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,timeout=timeout)
        result={'args':[str(x) for x in args],'code':p.returncode,'stdout':p.stdout.decode('utf-8','replace'),'stderr':p.stderr.decode('utf-8','replace')}
    except subprocess.TimeoutExpired as e:
        result={'args':[str(x) for x in args],'code':'timeout','stdout':(e.stdout or b'').decode('utf-8','replace'),'stderr':str(e)}
    LOG.append(result)
    (OUT/'operations.json').write_text(json.dumps(LOG,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if result['code']!=0 and not allow_disconnect:raise RuntimeError('operation failed; no automatic retry')
    return result['stdout']
def probe():
    s=run(BASE+['exec',"import machine,binascii,os,hashlib,json; b=open('src/external_instrument_link.py','rb').read(); print('PROBE|'+json.dumps({'uid':binascii.hexlify(machine.unique_id()).decode(),'size':len(b),'sha256':binascii.hexlify(hashlib.sha256(b).digest()).decode()}))"])
    data=json.loads(next(x.split('PROBE|',1)[1] for x in s.splitlines() if x.startswith('PROBE|')))
    if data['uid']!=MAN['parent_uid']:raise RuntimeError('unexpected parent identity')
    return data
if __name__=='__main__':
    phase=sys.argv[1]
    if phase=='backup':
        before=probe()
        if before['sha256']!=MAN['baseline']['sha256']:raise RuntimeError('baseline mismatch')
        (OUT/'parent_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
        backup=OUT/'backup/external_instrument_link_before.py'
        if backup.exists():raise RuntimeError('backup exists')
        run(BASE+['fs','cp',':src/external_instrument_link.py',backup])
        if hashlib.sha256(backup.read_bytes()).hexdigest()!=before['sha256']:raise RuntimeError('backup mismatch')
        run(BASE+['exec','import machine; machine.bootloader()'],timeout=8,allow_disconnect=True)
        time.sleep(2)
        info=run([PICO,'info','-a','--ser',MAN['parent_uid'].upper()])
        (OUT/'parent_bootsel_info.txt').write_text(info,encoding='utf-8')
        run([PICO,'save','-a','-v',OUT/'backup/parent_flash_before.bin','--ser',MAN['parent_uid'].upper()])
        raw=(OUT/'backup/parent_flash_before.bin').read_bytes()
        (OUT/'parent_flash_backup.json').write_text(json.dumps({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'verify':'picotool save -a -v successful'},indent=2),encoding='utf-8')
    elif phase=='deploy':
        saved=json.loads((OUT/'parent_flash_backup.json').read_text())
        if hashlib.sha256((OUT/'backup/parent_flash_before.bin').read_bytes()).hexdigest()!=saved['sha256']:raise RuntimeError('flash backup mismatch')
        run([PICO,'reboot','--ser',MAN['parent_uid'].upper()])
        time.sleep(3)
        if probe()['sha256']!=MAN['baseline']['sha256']:raise RuntimeError('baseline changed')
        source=OUT/MAN['parent_candidate']['file']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=MAN['parent_candidate']['sha256']:raise RuntimeError('package changed')
        run(BASE+['fs','cp',source,':src/external_instrument_link.new'])
        run(BASE+['exec',"import hashlib,binascii,os; p='src/external_instrument_link.new'; b=open(p,'rb').read(); assert binascii.hexlify(hashlib.sha256(b).digest()).decode()=='"+MAN['parent_candidate']['sha256']+"'; compile(b,p,'exec'); os.rename(p,'src/external_instrument_link.py'); os.sync(); print('INSTALL_OK')"])
        after=probe()
        if after['sha256']!=MAN['parent_candidate']['sha256']:raise RuntimeError('after mismatch')
        (OUT/'parent_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
        run(BASE+['exec','import machine; machine.reset()'],timeout=8,allow_disconnect=True)
        time.sleep(3)
        after_reboot=probe()
        if after_reboot['sha256']!=MAN['parent_candidate']['sha256']:raise RuntimeError('post reboot mismatch')
        (OUT/'parent_after_reboot.json').write_text(json.dumps(after_reboot,indent=2),encoding='utf-8')
        print('PARENT_DEPLOY_VERIFIED_REPL_STOPPED',flush=True)
    else:raise ValueError('phase')
