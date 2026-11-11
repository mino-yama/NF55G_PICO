"""QR単体Host評価のRAM／任意UART原文をオフライン検査する。実機操作なし。"""
import argparse
import json
import struct
from pathlib import Path

RECORD = struct.Struct('<IIBBBB64s')
HEADER = struct.Struct('<IIIII')
MAGIC = 0x51525042
KINDS = {1:'boot',2:'mount',3:'unmount',4:'hid_mount',5:'report_descriptor',6:'hid_report',7:'receive_request_failed',8:'hid_unmount',9:'oversize_report',10:'init_failed',11:'board_id'}

def decode_record(raw):
    if len(raw) != RECORD.size:
        raise ValueError('record must be 76 bytes')
    seq,ms,kind,addr,instance,length,data = RECORD.unpack(raw)
    if length > 64 or kind not in KINDS:
        raise ValueError('invalid record length/kind')
    return dict(seq=seq,ms=ms,kind=KINDS[kind],addr=addr,instance=instance,data_hex=data[:length].hex())

def inspect_records(records):
    if not records or records[0]['kind'] != 'boot':
        raise ValueError('boot record missing')
    descriptors = {}
    for idx,r in enumerate(records):
        if r['seq'] != idx:
            raise ValueError('sequence gap/restart')
        key=(r['addr'],r['instance'])
        data=bytes.fromhex(r['data_hex'])
        if r['kind']=='hid_mount':
            if len(data)!=4:
                raise ValueError('invalid HID mount metadata')
            wanted=int.from_bytes(data[2:4],'little')
            if not wanted:
                raise ValueError('missing report descriptor')
            if key in descriptors and descriptors[key][0]!=descriptors[key][1]:
                raise ValueError('incomplete descriptor before remount')
            descriptors[key]=[wanted,0]
        elif r['kind']=='report_descriptor':
            if key not in descriptors:
                raise ValueError('descriptor without HID mount')
            descriptors[key][1]+=len(data)
            if descriptors[key][1]>descriptors[key][0]:
                raise ValueError('descriptor length overflow')
        elif r['kind']=='hid_report':
            if key not in descriptors:
                raise ValueError('report without HID mount')
        elif r['kind']=='hid_unmount':
            if key in descriptors and descriptors[key][0]!=descriptors[key][1]:
                raise ValueError('incomplete descriptor before unmount')
            descriptors.pop(key,None)
    if any(wanted!=actual for wanted,actual in descriptors.values()):
        raise ValueError('incomplete/missing report descriptor')
    errors=[r for r in records if r['kind'] in ('receive_request_failed','oversize_report','init_failed')]
    return {'status':'capture_errors' if errors else 'raw_capture_only',
            'records':len(records),'errors':errors,'events':records,
            'qr_text_verified':False,'hardware_acceptance':False}

def read_ram(raw):
    if len(raw)!=HEADER.size+256*RECORD.size:
        raise ValueError('RAM dump size must be 19476 bytes')
    magic,version,count,dropped,heartbeat=HEADER.unpack_from(raw)
    if magic!=MAGIC or version!=1 or count>256:
        raise ValueError('invalid log header')
    if dropped or count==256:
        raise ValueError('log full or dropped: repeat shorter capture')
    records=[decode_record(raw[20+i*76:20+(i+1)*76]) for i in range(count)]
    result=inspect_records(records)
    result.update(heartbeat_ms=heartbeat,dropped=dropped,transport='RAM')
    return result

def read_uart(text):
    records=[]
    for line in text.splitlines():
        if not line.startswith('@') or len(line)!=153:
            raise ValueError('invalid UART framing/truncated line')
        records.append(decode_record(bytes.fromhex(line[1:])))
    if len(records)>=256:
        raise ValueError('log at capacity: repeat shorter capture')
    result=inspect_records(records)
    result.update(transport='UART',dropped=None,tail_completeness='not_proven')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path)
    p.add_argument('--format',choices=('ram','uart'),required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=read_ram(args.input.read_bytes()) if args.format=='ram' else read_uart(args.input.read_text(encoding='ascii'))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
