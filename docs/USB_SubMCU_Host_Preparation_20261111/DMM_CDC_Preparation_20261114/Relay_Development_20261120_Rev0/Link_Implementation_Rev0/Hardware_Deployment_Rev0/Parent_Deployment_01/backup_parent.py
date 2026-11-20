"""親Picoをsoft resetせず読み取り、既存ファイルを退避・SHA照合する。"""
import hashlib
import json
from pathlib import Path
from mpremote.transport_serial import SerialTransport

OUT = Path(__file__).resolve().parent
EVIDENCE = OUT / 'Backup_Manifest.json'
EXPECTED = '69f7d45962cfdfad'


def main():
    if EVIDENCE.exists():
        raise RuntimeError('Existing backup manifest must be preserved')
    evidence = {'date_jst':'2026-11-20','port':'COM6','files':[], 'backup_complete':False,
                'device_files_written':False,'soft_reset_performed':False}
    def save():
        EVIDENCE.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    transport = SerialTransport('COM6',wait=2)
    try:
        transport.enter_raw_repl(soft_reset=False)
        uid = transport.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()")
        evidence['unique_id'] = uid
        if uid != EXPECTED:
            raise RuntimeError('Wrong parent Pico')
        evidence['version'] = transport.eval("__import__('sys').version")
        evidence['root_names'] = transport.eval("__import__('os').listdir('/')")
        stdout, stderr = transport.exec_raw("import rp2,os,binascii; print('PIO4_ACTIVE='+str(rp2.StateMachine(4).active())); print('PIO5_ACTIVE='+str(rp2.StateMachine(5).active())); print('CRC32='+str(binascii.crc32(b'123456789'))); print('NONCE_BYTES='+str(len(os.urandom(8))))")
        if stderr:
            raise RuntimeError(stderr.decode())
        (OUT/'Runtime_API_Precheck.log').write_bytes(stdout)
        evidence['runtime_precheck'] = stdout.decode()
        pending = ['']
        files = []
        while pending:
            directory = pending.pop()
            names = transport.eval("__import__('os').listdir("+repr('/'+directory)+")")
            for name in names:
                relative = directory+'/'+name if directory else name
                mode = transport.eval("__import__('os').stat("+repr('/'+relative)+")[0]")
                if mode & 0x4000:
                    if relative == 'src' or relative.startswith('src/'):
                        pending.append(relative)
                else:
                    files.append(relative)
        for relative in sorted(files):
            data = bytes(transport.fs_readfile('/'+relative))
            target = OUT/'backup'/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as output:
                output.write(data)
            digest = hashlib.sha256(data).hexdigest()
            code = "import hashlib,binascii; _backup_hash=hashlib.sha256(); _backup_file=open("+repr('/'+relative)+",'rb'); _backup_block=_backup_file.read(512)\nwhile _backup_block:\n _backup_hash.update(_backup_block)\n _backup_block=_backup_file.read(512)\n_backup_file.close(); print(binascii.hexlify(_backup_hash.digest()).decode())"
            remote, error = transport.exec_raw(code)
            if error or remote.decode().strip() != digest:
                raise RuntimeError('Backup hash mismatch: '+relative)
            evidence['files'].append({'path':relative,'bytes':len(data),'sha256':digest,'device_sha256':remote.decode().strip()})
            save()
            print('BACKUP_OK',relative,len(data),flush=True)
        evidence['backup_complete'] = True
        save()
        print('BACKUP_COMPLETE',len(evidence['files']),flush=True)
    except Exception as error:
        evidence['error'] = repr(error)
        save()
        raise
    finally:
        transport.exit_raw_repl()
        transport.close()


if __name__ == '__main__':
    main()
