"""退避済み親Picoへ照合済みパッケージを配置し、raw REPLでimport検証する。"""
import hashlib
import json
import os
from pathlib import Path
import re
from mpremote.transport_serial import SerialTransport

BASE_OUT = Path(__file__).resolve().parent
BASE_ROOT = next(path for path in BASE_OUT.parents if (path/'AGENTS.md').is_file())
def long_path(path):
    return Path(chr(92)*2+'?'+chr(92)+str(path)) if os.name=='nt' else path
OUT, ROOT = long_path(BASE_OUT), long_path(BASE_ROOT)
PACKAGE = ROOT / 'docs/USB_SubMCU_Host_Preparation_20261111/DMM_CDC_Preparation_20261114/Relay_Development_20261120_Rev0/Link_Implementation_Rev0/Deployment_Package'
EVIDENCE = OUT / 'Deployment_Manifest.json'


def remote_hash(transport, relative):
    return transport.eval("__import__('binascii').hexlify(__import__('hashlib').sha256(open("+repr('/'+relative)+",'rb').read()).digest()).decode()")


def main():
    if EVIDENCE.exists():
        raise RuntimeError('Preserve existing deployment manifest')
    backup=json.loads((OUT/'Backup_Manifest_02.json').read_text(encoding='utf8'))
    if not backup['backup_complete'] or backup['unique_id']!='69f7d45962cfdfad':
        raise RuntimeError('Incomplete/wrong backup')
    previous={row['path']:row for row in backup['files']}
    package=json.loads((PACKAGE/'manifest.json').read_text(encoding='utf8'))
    rows=[]
    for row in package['files']:
        if not row['file'].startswith('Parent/'):
            continue
        relative=row['file'][7:]
        if relative!='main.py' and re.fullmatch(r'src/[A-Za-z_][A-Za-z_0-9]*\.py',relative) is None:
            raise RuntimeError('Unexpected deployment path')
        data=(PACKAGE/row['file']).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise RuntimeError('Package hash mismatch')
        rows.append((relative,row,data))
    if len(rows)!=30:
        raise RuntimeError('Unexpected parent package size')
    evidence={'date_jst':'2026-11-20','port':'COM6','unique_id':None,'files':[],
              'deployed':False,'normal_boot_performed':False,'gpio_uart_started':False}
    def save():
        EVIDENCE.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    transport=SerialTransport('COM6',wait=2)
    changed=[]
    try:
        transport.enter_raw_repl(soft_reset=False)
        uid=transport.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()")
        if uid!='69f7d45962cfdfad':
            raise RuntimeError('Wrong parent')
        evidence['unique_id']=uid
        for relative,row,data in rows:
            exists=transport.eval(repr(relative.rsplit('/',1)[-1])+" in __import__('os').listdir("+repr('/'+relative.rsplit('/',1)[0] if '/' in relative else '/')+")")
            if relative in previous:
                if not exists or remote_hash(transport,relative)!=previous[relative]['sha256']:
                    raise RuntimeError('Device changed since backup: '+relative)
                local=(OUT/'backup'/relative).read_bytes()
                if hashlib.sha256(local).hexdigest()!=previous[relative]['sha256']:
                    raise RuntimeError('Backup changed: '+relative)
            elif exists:
                raise RuntimeError('Unbacked existing target: '+relative)
        # 依存moduleを先に置き、src/main.pyを最後に切り替える。
        rows.sort(key=lambda item:(2 if item[0] in ('src/main.py','main.py') else 0 if item[0] not in previous else 1,item[0]))
        for relative,row,data in rows:
            old=previous.get(relative)
            update=old is None or old['sha256']!=row['sha256']
            if update:
                changed.append(relative)
                transport.fs_writefile('/'+relative,data)
            digest=remote_hash(transport,relative)
            if digest!=row['sha256']:
                raise RuntimeError('Post-deployment mismatch: '+relative)
            evidence['files'].append({'path':relative,'bytes':len(data),'sha256':digest,'updated':update,'previous_sha256':old['sha256'] if old else None})
            save()
            print('DEPLOY_OK' if update else 'UNCHANGED_OK',relative,flush=True)
        # raw REPL soft resetはmain.pyを通常実行せず、旧moduleキャッシュを消してから検証する。
        transport.enter_raw_repl(soft_reset=True)
        command="""
import machine,binascii,rp2
assert binascii.hexlify(machine.unique_id()).decode()=='69f7d45962cfdfad'
import src.config as cfg
import src.external_instrument_contract as contract
import src.external_instrument_link as link
import src.external_instrument_pio as pio
import src.main as app
assert cfg.EXTERNAL_INSTRUMENT_ENABLED is True
assert contract.parse_monitor_request(b'EXT_QUERY 2000 *IDN?')['command']==b'*IDN?'
assert len(pio._transmit[0])==4 and len(pio._receive[0])==12
assert not rp2.StateMachine(4).active() and not rp2.StateMachine(5).active()
print('PARENT_DEPLOYMENT_IMPORT_OK')
print('EXTERNAL_ENABLED='+str(cfg.EXTERNAL_INSTRUMENT_ENABLED))
print('PIO4_ACTIVE='+str(rp2.StateMachine(4).active()))
print('PIO5_ACTIVE='+str(rp2.StateMachine(5).active()))
"""
        stdout,stderr=transport.exec_raw(command,timeout=30)
        (OUT/'Post_Deployment_Import.log').write_bytes(stdout+b'\nSTDERR\n'+stderr)
        if stderr or b'PARENT_DEPLOYMENT_IMPORT_OK' not in stdout:
            raise RuntimeError('Import validation failed: '+stderr.decode())
        for relative,row,data in rows:
            if remote_hash(transport,relative)!=row['sha256']:
                raise RuntimeError('Final hash mismatch: '+relative)
        evidence['deployed']=True
        evidence['raw_soft_reset_performed']=True
        evidence['import_validation']=stdout.decode()
        evidence['device_state']='Friendly REPL after close; normal main.py not started'
        save()
        print(stdout.decode(),flush=True)
        print('PARENT_DEPLOYMENT_COMPLETE',len(rows),'verified files;',len(changed),'updated/added',flush=True)
    except Exception as error:
        evidence['error']=repr(error)
        evidence['rollback']=[]
        for relative in reversed(changed):
            if relative in previous:
                data=(OUT/'backup'/relative).read_bytes()
                transport.fs_writefile('/'+relative,data)
                if remote_hash(transport,relative)!=previous[relative]['sha256']:
                    raise RuntimeError('Rollback hash mismatch: '+relative)
                evidence['rollback'].append({'path':relative,'restored':True})
            else:
                stdout,stderr=transport.exec_raw("import os; os.remove("+repr('/'+relative)+")")
                if stderr:
                    raise RuntimeError('Rollback cleanup failed: '+relative)
                evidence['rollback'].append({'path':relative,'removed_new_file':True})
        save()
        raise
    finally:
        save()
        transport.exit_raw_repl()
        transport.close()


if __name__=='__main__':
    main()
