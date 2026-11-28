"""交換HOSTを退避・通常FW配置し、親の個体ID設定だけを更新する。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from mpremote.transport_serial import SerialTransport
from deploy_rtc_fallback_20261128 import HEADER

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
OUT=CASE/'host_replacement_01'
TOOL=ROOT/'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
SOURCE=ROOT/'docs/USB_Host_Reset_Study_20261121/Debug_20261125_01/candidate_20261125_105200_326526'
parser=argparse.ArgumentParser();parser.add_argument('action',choices=('flash','parent'));parser.add_argument('--uid',required=True)
args=parser.parse_args();uid=args.uid.upper()
assert re.fullmatch('[0-9A-F]{16}',uid)
assert uid not in ('69F7D45962CFDFAD','A06FEA01012EC137','BFCF2EDB84B0B37F'),'not a replacement HOST'
def sha(data):return hashlib.sha256(data).hexdigest()
def run(label,*options):
    p=subprocess.run([str(TOOL),*map(str,options),'--ser',uid],capture_output=True,timeout=120)
    (OUT/(label+'.log')).write_bytes(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(label+': '+(p.stdout+p.stderr).decode('utf-8','replace'))
    return p.stdout.decode('utf-8','replace')
if args.action=='flash':
    OUT.mkdir()
    info=run('host_before','info','-a')
    assert uid.lower() in info.lower() and 'RP2350' in info and 'bootsel' in info.lower() and '2048K' in info
    manifest=json.loads((SOURCE/'manifest.json').read_text())
    entry=next(f for f in manifest['files'] if f['name'].endswith('.uf2'))
    image=SOURCE/entry['name'];assert sha(image.read_bytes())==entry['sha256']
    assert manifest['version']=='meter-host-relay-20261125.2'
    backup=OUT/'replacement_before_2MB.bin'
    run('host_backup','save','-a','-v',backup)
    assert backup.stat().st_size==2097152
    run('host_backup_verify','verify',backup)
    (OUT/'backup.json').write_text(json.dumps({'uid':uid,'bytes':backup.stat().st_size,'sha256':sha(backup.read_bytes()),'verified':True},indent=2))
    try:
        run('host_load','load','-v',image)
        run('host_verify','verify',image)
        after=run('host_after','info','-a');assert manifest['version'] in after
    except Exception:
        run('failure_restore','load','-v',backup);run('failure_restore_verify','verify',backup)
        raise
    (OUT/'flash_result.json').write_text(json.dumps({'uid':uid,'version':manifest['version'],'uf2_sha256':entry['sha256'],'backup_verified':True,'flash_verified':True,'left_in_bootsel':True},indent=2))
    print('REPLACEMENT_FLASH_VERIFIED; '+uid+'; BOOTSEL',flush=True)
else:
    saved=json.loads((OUT/'flash_result.json').read_text());assert saved['uid']==uid and saved['flash_verified']
    before=json.loads((ROOT/'docs/QR_Production_Integration_20261128_Rev0/parent_after_hashes.json').read_text())
    remote=SerialTransport('COM6',timeout=2)
    reset=False
    try:
        remote.enter_raw_repl(soft_reset=False)
        def execute(code):
            out,err=remote.exec_raw(code,timeout=45)
            with (OUT/'parent_operations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'code':code,'out':out.decode('utf-8','replace'),'err':err.decode('utf-8','replace')})+'\n')
            if err:raise RuntimeError(err.decode())
            return out.decode()
        execute(HEADER)
        actual=json.loads(execute('print(json.dumps({p:digest(p) for p in '+repr(list(before))+'}))').strip());assert actual==before
        data=remote.fs_readfile('/src/config.py')
        (OUT/'parent_config_before.py').open('xb').write(data)
        updated,count=re.subn(rb'(?m)^EXTERNAL_HOST_CHIPID = "BFCF2EDB84B0B37F"\r?$',('EXTERNAL_HOST_CHIPID = "'+uid+'"').encode(),data)
        assert count==1
        a={};b={};exec(data,a);exec(updated,b)
        assert {k for k in a if not k.startswith('__') and a[k]!=b[k]}=={'EXTERNAL_HOST_CHIPID'}
        assert b['EXTERNAL_INSTRUMENT_ENABLED'] and b['QR_HOST_ARM_ENABLED']
        (OUT/'parent_config_candidate.py').open('xb').write(updated)
        h=sha(updated);stage='/meter_config_stage_replace_20261128.py';old='/meter_config_before_replace_20261128.py'
        execute('assert maybe_digest('+repr(stage)+') is None\nassert maybe_digest('+repr(old)+') is None')
        remote.fs_writefile(stage,updated)
        execute('with open('+repr(stage)+",'rb') as f: compile(f.read(),'config.py','exec')")
        execute('assert digest('+repr(stage)+')=='+repr(h)+'\nassert digest(\'/src/config.py\')=='+repr(before['/src/config.py'])+'\nos.rename(\'/src/config.py\','+repr(old)+')\ntry:os.rename('+repr(stage)+",'/src/config.py')\nexcept Exception:\n os.rename("+repr(old)+",'/src/config.py')\n raise")
        readback=remote.fs_readfile('/src/config.py');assert readback==updated
        (OUT/'parent_config_readback.py').open('xb').write(readback)
        expected=dict(before);expected['/src/config.py']=h
        actual=json.loads(execute('print(json.dumps({p:digest(p) for p in '+repr(list(expected))+'}))').strip());assert actual==expected
        (OUT/'parent_after_hashes.json').write_text(json.dumps(actual,indent=2))
        remote.exec_raw_no_follow('import machine;machine.reset()');reset=True
        print('NEW_HOST_ID_CONFIGURED; 37_HASHES_VERIFIED; PARENT_RESET',flush=True)
    finally:
        try:
            if not reset:remote.exec_raw_no_follow("import sys;sys.modules['src.main'].active_app.run()")
        finally:remote.close()
