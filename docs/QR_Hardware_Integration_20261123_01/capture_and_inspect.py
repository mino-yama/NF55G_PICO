"""親GP9の受動採取と診断レコード解析。途中接続を起動世代照合済みと扱わない。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.qr_reader import decode_qr, decode_nf55g_label
spec=importlib.util.spec_from_file_location('qr_probe_log',ROOT/'scripts/usb_submcu_probe_log.py')
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def inspect(raw,expected=None,nf55g_profile=False):
    lines=raw.split(b'\n')
    prefix=b''; tail=b''
    if raw.endswith(b'\n'): lines.pop()
    elif lines: tail=lines.pop()
    if lines:
        first=lines[0][:-1] if lines[0].endswith(b'\r') else lines[0]
        if first.startswith(b'@') and len(first)==153:
            lines[0]=first
        elif first.startswith(b'\x00@') and len(first)==154:
            prefix=b'\x00';lines[0]=first[1:]
        else:
            prefix=lines.pop(0)+b'\n'
    events=[];texts=[];health=[];errors=[]
    for line in lines:
        try:
            if line.endswith(b'\r'): line=line[:-1]
            assert line.startswith(b'@') and len(line)==153,'invalid full-line framing'
            record=probe.decode_record(bytes.fromhex(line[1:].decode('ascii')))
            if events: assert record['seq']==events[-1]['seq']+1,'sequence gap/restart'
            events.append(record)
            payload=bytes.fromhex(record['data_hex'])
            if record['kind']=='qr_text':
                text=payload.decode('ascii')
                fields=decode_nf55g_label(text) if nf55g_profile else decode_qr(text)
                texts.append({'seq':record['seq'],'raw':text,'fields':fields,
                              'expected_match':text==expected if expected is not None else None})
            elif record['kind']=='host_health':
                assert len(payload)==24
                values=struct.unpack('<6I',payload)
                health.append(dict(zip(('loops','frames','drop','texts','reports','flags'),values)))
                assert values[2]==0 and not values[5]&~15,'drop/invalid health flags'
            elif record['kind']=='boot':
                assert payload in probe.STREAM_VERSIONS,'unexpected QR firmware version'
            elif record['kind']=='board_id':
                assert len(payload)==16 and all(c in b'0123456789abcdefABCDEF' for c in payload),'invalid board ID'
            elif record['kind'] in ('receive_request_failed','oversize_report','init_failed','qr_decode_error'):
                errors.append({'record':record,'reason':'host diagnostic error'})
        except (ValueError,AssertionError,UnicodeError) as exc:
            errors.append({'line_hex':line.hex(),'reason':repr(exc)})
    board=[bytes.fromhex(r['data_hex']).decode('ascii','replace') for r in events if r['kind']=='board_id']
    boot=[bytes.fromhex(r['data_hex']).decode('ascii','replace') for r in events if r['kind']=='boot']
    return {'status':'CAPTURE_ERRORS' if errors else 'CAPTURE_ONLY',
        'record_count':len(events),'records':events,'texts':texts,'health':health,'errors':errors,
        'boot_versions':boot,'board_ids':board,'identity_verified':not errors and len(boot)==1 and boot[0] in [v.decode() for v in probe.STREAM_VERSIONS] and board==['A06FEA01012EC137'],
        'midstream':not events or events[0]['seq']!=0 or events[0]['kind']!='boot',
        'prefix_hex':prefix.hex(),'tail_hex':tail.hex(),'expected_qr':expected,
        'all_texts_match':bool(texts) and all(t['expected_match'] for t in texts) if expected is not None else None,
        'hardware_acceptance':False,'nf55g_commands_sent':0,'ss_or_cache_integration':False,
        'label_profile':'NF55802-G_03' if nf55g_profile else None}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected')
    parser.add_argument('--port',default='COM6')
    parser.add_argument('--seconds',type=int,choices=range(30,181),default=60,metavar='30..180')
    parser.add_argument('--profile',choices=('nf55g-rev3','generic'),default='nf55g-rev3',help='既定は図面の35文字構造/数字欄照合。型式・品目・REVの値は固定しない')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.expected is not None:
        (decode_nf55g_label if args.profile=='nf55g-rev3' else decode_qr)(args.expected)
    args.output.mkdir(parents=True,exist_ok=False)
    # 実行した採取条件を各runに保持。起動操作の待ち時間も明示指定する。
    program=args.output/'capture_program.py'
    program.write_text((OUT/'capture_parent.py').read_text(encoding='utf-8').replace(
        'QR_DURATION_MS=60000','QR_DURATION_MS='+str(args.seconds*1000)),encoding='utf-8')
    with (args.output/'parent.log').open('wb') as log:
        process=subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),'-u','-m','mpremote','connect',args.port,
            'resume','run',str(program)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=args.seconds+45)
    text=(args.output/'parent.log').read_text(encoding='utf-8')
    assert process.returncode==0 and 'QR_CAPTURE_DONE_PIO_INPUT' in text,text[-2000:]
    meta=json.loads(next(x.split('|',1)[1] for x in text.splitlines() if x.startswith('QR_CAPTURE_META|')))
    raw=b''.join(bytes.fromhex(x.split('|',1)[1]) for x in text.splitlines() if x.startswith('QR_CAPTURE_HEX|'))
    assert len(raw)==meta['bytes'] and hashlib.sha256(raw).hexdigest()==meta['sha256']
    (args.output/'qr_host.raw').write_bytes(raw)
    result=inspect(raw,args.expected,args.profile=='nf55g-rev3')
    result['capture']=meta
    if meta['fault']: result['status']='CAPTURE_ERRORS'
    (args.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','health')},ensure_ascii=False,indent=2))
