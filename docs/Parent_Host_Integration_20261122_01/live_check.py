"""Host/親起動とIDN一回。再試行・測定・設定コマンドなし。"""
import contextlib,datetime,json,sys,time
import serial
from parent_deploy import OUT,MAN,PICO,run
phase=sys.argv[1]
if phase not in ('startup_idn','disconnected_idn','reconnected_idn','fault_hold_idn','after_active_disconnect_idn','scheduler_retest_idn','transfer_guard_retest_idn','transfer_guard_confirmed_idn','timeout_snapshot_confirmed_idn','usb_lower_confirmed_idn'):raise ValueError(phase)
target=OUT/phase
target.mkdir(exist_ok=False)
raw={k:bytearray() for k in ('parent','host','ate')}
with contextlib.ExitStack() as stack:
    ports={}
    for k,p,b in [('parent','COM6',115200),('host','COM22',115200),('ate','COM7',57600)]:
        port=serial.Serial(port=None,baudrate=b,timeout=0,write_timeout=1)
        port.port=p;port.dtr=False;port.rts=False;port.open()
        ports[k]=stack.enter_context(port)
    def collect(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            for k,p in ports.items():
                n=p.in_waiting
                if n:raw[k].extend(p.read(n))
            time.sleep(.005)
    try:
        collect(.3)
        if phase=='startup_idn':
            run([PICO,'reboot','--ser',MAN['host_serial']])
            collect(1)
            ports['parent'].write(b'\x02\x04')
            collect(6)
        pre={k:len(v) for k,v in raw.items()}
        command=b'EXT_QUERY 2000 *IDN?\r'
        ports['ate'].write(command)
        collect(5)
        reply=bytes(raw['ate'][pre['ate']:])
        result={'phase':phase,'date_jst':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'command':command.decode('ascii'),'reply':reply.decode('ascii','backslashreplace'),'pre_bytes':pre,'bytes':{k:len(v) for k,v in raw.items()},'query_count':1,'automatic_retry':False}
        (target/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False),flush=True)
        print('HOST_RAW|'+raw['host'].decode('ascii','backslashreplace'),flush=True)
        print('PARENT_RAW|'+raw['parent'].decode('utf-8','backslashreplace'),flush=True)
    finally:
        for k,v in raw.items():(target/(k+'.raw')).write_bytes(v)
