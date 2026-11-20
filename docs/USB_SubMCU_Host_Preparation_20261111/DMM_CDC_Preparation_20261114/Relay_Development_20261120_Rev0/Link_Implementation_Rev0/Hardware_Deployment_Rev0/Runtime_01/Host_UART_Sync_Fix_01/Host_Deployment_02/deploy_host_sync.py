"""個体/版/UF2を照合し、現行全Flash退避後にHost同期修正版を配置する。"""
from pathlib import Path
import subprocess,json,hashlib,shutil
BASE=Path(__file__).resolve().parent
PREFIX=chr(92)*2+'?'+chr(92)
OUT=BASE if str(BASE).startswith(PREFIX) else Path(PREFIX+str(BASE))
ROOT=next(p for p in BASE.parents if (p/'src'/'external_instrument_contract.py').exists())
# picotoolへ渡す入出力は短い作業パス。長い案件保存先はPythonで保管する。
SHORT_ROOT=Path(str(ROOT).removeprefix(PREFIX))
WORK=SHORT_ROOT/'tmp'/'host_sync_deploy_20261120_02'
TOOL=SHORT_ROOT/'tools'/'usb_submcu'/'picotool-2.2.0'/'picotool'/'picotool.exe'
SERIAL='BFCF2EDB84B0B37F'
SHA='cb3fc420088b72eae1bab80fad5ddb09c75f0bd8a79889aefddb08f42a869def'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest=OUT/'Deployment_Manifest.json'
    if manifest.exists() or WORK.exists():
        raise RuntimeError('Preserve previous deployment')
    WORK.mkdir(parents=True)
    result={'target_usb_serial':SERIAL,'target_chipid':'0xbfcf2edb84b0b37f',
            'date_jst':'2026-11-20','version':'meter-host-relay-20261120.2',
            'backup_verified':False,'flash_verified':False,'rebooted':False,'runtime_accepted':False}
    def run(name,args):
        proc=subprocess.run([str(TOOL)]+args,cwd=SHORT_ROOT,capture_output=True,timeout=90)
        raw=proc.stdout+b'\nSTDERR\n'+proc.stderr
        (OUT/name).write_bytes(raw)
        if proc.returncode:
            raise RuntimeError(name+' failed: '+raw.decode(errors='replace')[-2000:])
        return proc.stdout.decode(errors='replace')
    try:
        source=OUT.parent/'meter_host_relay_20261120_2.uf2'
        if sha(source)!=SHA:
            raise RuntimeError('Candidate UF2 hash mismatch')
        image=WORK/'relay_v2.uf2'
        shutil.copyfile(source,image)
        if sha(image)!=SHA:
            raise RuntimeError('Staged UF2 hash mismatch')
        info=run('candidate_info.log',['info','-a',str(image)])
        if 'meter-host-relay-20261120.2' not in info:
            raise RuntimeError('Candidate metadata mismatch')
        before=run('before_info.log',['info','-a','--ser',SERIAL])
        if not all(x in before for x in ('0xbfcf2edb84b0b37f','meter-host-relay-20261120.1','bootsel','2048K')):
            raise RuntimeError('Unexpected target identity/version/state/size')
        print('TARGET_VERIFIED '+SERIAL+' old=.1 BOOTSEL 2048K',flush=True)
        backup=WORK/'before_relay_v2_flash.bin'
        run('backup_verify.log',['save','-a','-v',str(backup),'--ser',SERIAL])
        if backup.stat().st_size!=2097152:
            raise RuntimeError('Backup size mismatch')
        archive=OUT/'before_relay_v2_flash_2MB.bin'
        shutil.copyfile(backup,archive)
        if sha(archive)!=sha(backup):
            raise RuntimeError('Archived backup hash mismatch')
        result.update(backup_verified=True,backup_file=archive.name,backup_bytes=archive.stat().st_size,
                      backup_sha256=sha(archive),uf2_sha256=SHA,uf2_bytes=image.stat().st_size)
        manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('FULL_FLASH_BACKUP_VERIFIED '+result['backup_sha256'],flush=True)
        run('load_verify.log',['load','-v',str(image),'--ser',SERIAL])
        result['flash_verified']=True
        after=run('after_info.log',['info','-a','--ser',SERIAL])
        if not all(x in after for x in ('0xbfcf2edb84b0b37f','meter-host-relay-20261120.2','bootsel')):
            raise RuntimeError('Post-write identity/version/state mismatch')
        result['post_info_verified']=True
        result['result']='DEPLOYED_VERIFIED_BOOTSEL_NOT_REBOOTED'
        print('FLASH_VERIFY_OK; .2 identity/version confirmed; BOOTSEL retained',flush=True)
    except Exception as error:
        result.update(result='STOPPED',error=repr(error))
        raise
    finally:
        manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':
    main()
