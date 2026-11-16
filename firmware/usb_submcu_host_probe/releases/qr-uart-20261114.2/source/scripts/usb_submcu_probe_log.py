"""QR単体Host評価のRAM／任意UART原文をオフライン検査する。実機操作なし。"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

RECORD = struct.Struct('<IIBBBB64s')
HEADER = struct.Struct('<IIIII')
MAGIC = 0x51525042
# 固定した診断FW版だけに容量を割り当てる。未知版は従来の256件上限を維持。
UART_CAPACITIES = {b'qr-uart-20261114.1': 1024,b'qr-uart-20261114.2': 1024}
KINDS = {1:'boot',2:'mount',3:'unmount',4:'hid_mount',5:'report_descriptor',6:'hid_report',7:'receive_request_failed',8:'hid_unmount',9:'oversize_report',10:'init_failed',11:'board_id',12:'qr_text',13:'qr_decode_error'}

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
        elif r['kind']=='qr_text':
            if key not in descriptors or len(data)!=35 or any(
                    c not in b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-' for c in data):
                raise ValueError('invalid decoded QR text')
        elif r['kind']=='qr_decode_error':
            if len(data)!=1 or not 1<=data[0]<=11:
                raise ValueError('invalid QR decode error')
        elif r['kind']=='hid_unmount':
            if key in descriptors and descriptors[key][0]!=descriptors[key][1]:
                raise ValueError('incomplete descriptor before unmount')
            descriptors.pop(key,None)
    if any(wanted!=actual for wanted,actual in descriptors.values()):
        raise ValueError('incomplete/missing report descriptor')
    errors=[r for r in records if r['kind'] in ('receive_request_failed','oversize_report','init_failed','qr_decode_error')]
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
    result=inspect_records(records)
    version = bytes.fromhex(records[0]['data_hex'])
    capacity = UART_CAPACITIES.get(version, 256)
    if len(records)>=capacity:
        raise ValueError('log at capacity: repeat shorter capture')
    result.update(transport='UART',dropped=None,tail_completeness='not_proven',record_capacity=capacity)
    return result

def read_uart_capture(raw, allow_startup_nul=False):
    """原文を保持し、明示指定時だけ起動前NUL 1byteを警告付きで分離する。"""
    prefix = b''
    body = raw
    if allow_startup_nul and raw.startswith(b'\x00@'):
        prefix, body = raw[:1], raw[1:]
    result = read_uart(body.decode('ascii'))
    if prefix:
        # 任意ノイズからの再同期や途中の破損除去はしない。起動識別も必要。
        events = result['events']
        if len(events) < 2 or events[1]['kind'] != 'board_id':
            raise ValueError('startup NUL requires boot and board_id records')
        identity = bytes.fromhex(events[1]['data_hex'])
        if len(identity) != 16 or any(c not in b'0123456789abcdefABCDEF' for c in identity):
            raise ValueError('invalid startup board_id')
        if not body.endswith(b'\n'):
            raise ValueError('startup capture missing final LF')
    result.update(source_sha256=hashlib.sha256(raw).hexdigest(),
                  source_bytes=len(raw), startup_prefix_hex=prefix.hex(),
                  original_framing_clean=not bool(prefix),
                  warnings=['leading_nul_observed_cause_unconfirmed'] if prefix else [])
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path)
    p.add_argument('--format',choices=('ram','uart'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-startup-nul', action='store_true',
                   help='UART先頭NUL 1byteのみ警告付きで分離。原文の形式合格とはしない')
    args=p.parse_args()
    if args.allow_startup_nul and args.format != 'uart':
        p.error('--allow-startup-nul requires --format uart')
    raw = args.input.read_bytes()
    result=read_ram(raw) if args.format=='ram' else read_uart_capture(raw,args.allow_startup_nul)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
