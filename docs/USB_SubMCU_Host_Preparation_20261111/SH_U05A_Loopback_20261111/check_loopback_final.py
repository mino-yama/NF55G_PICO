"""SH-U05A単体・TXD-RXD短絡の実機ループバック。製品・追加基板は接続しない。"""
import json
import time
from pathlib import Path
import serial
from serial.tools import list_ports

base=Path(__file__).parent
for index in range(1,1000):
    run=base/f"run{index:02d}"
    try:
        run.mkdir()
        break
    except FileExistsError:
        continue
else:
    raise SystemExit("No unused evidence folder")

ports=list(list_ports.comports())
rows=[dict(device=p.device,description=p.description,vid=p.vid,pid=p.pid,location=p.location,hwid=p.hwid) for p in ports]
matched=[p for p in ports if p.device.upper()=="COM22" and p.vid==0x1a86 and p.pid==0x5523 and (p.location or "").split(":",1)[0]=="1-4.3"]
result=dict(scope="SH-U05A physical TXD-RXD loopback only",user_authorized=True,port_inventory=rows,cases=[],success=False,total_written=0,total_received=0,closed=True)
s=None
start=time.monotonic()
failed=False
cases=[("ascii",b"SH-U05A LOOPBACK 0123456789\r\n"),("synthetic_35_chars",("AbC-"+"0"*25+"123456").encode("ascii")),("control_bytes",bytes([0,255,0x55,0xaa,13,10,0x11,0x13])),("all_256_values",bytes(range(256)))]
cases.extend((f"length_{n}",bytes((i*73+n)&255 for i in range(n))) for n in (1,63,64,65,255,256,257,1024))
cases.extend((f"sequence_{i:03d}",f"LOOP-{i:04d}|AbC-001234567890\r\n".encode("ascii")) for i in range(100))
try:
    if len(matched)!=1:
        raise RuntimeError("COM22 / 1A86:5523 / location 1-4.3 not uniquely matched; no port opened")
    s=serial.Serial(port=None,baudrate=115200,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=0.01,write_timeout=2,xonxoff=False,rtscts=False,dsrdtr=False)
    s.dtr=False
    s.rts=False
    s.port=matched[0].device
    s.open()
    result["closed"]=False
    result["settings"]=s.get_settings()
    result["dtr"]=s.dtr
    result["rts"]=s.rts
    # バッファを消去して証跡を隠さず、送信前の予期しない入力も検出する。
    baseline=bytearray()
    deadline=time.monotonic()+0.2
    while time.monotonic()<deadline:
        baseline.extend(s.read(256))
    result["baseline_hex"]=baseline.hex()
    if baseline:
        raise RuntimeError("Unexpected input before loopback test; stopped without transmitting")
    for name,payload in cases:
        item=dict(name=name,tx_hex=payload.hex(),written=0,rx_hex="",extra_hex="",match=False)
        result["cases"].append(item)
        t0=time.monotonic()
        while item["written"]<len(payload):
            n=s.write(payload[item["written"]:])
            if not n:
                raise RuntimeError("zero-byte write")
            item["written"]+=n
            result["total_written"]+=n
        rx=bytearray()
        deadline=time.monotonic()+2
        while len(rx)<len(payload) and time.monotonic()<deadline:
            rx.extend(s.read(len(payload)-len(rx)))
        item["rx_hex"]=rx.hex()
        result["total_received"]+=len(rx)
        extra=s.read(256)
        item["extra_hex"]=extra.hex()
        result["total_received"]+=len(extra)
        item["elapsed_ms"]=round((time.monotonic()-t0)*1000,3)
        item["match"]=(bytes(rx)==payload and not extra)
        if not item["match"]:
            raise RuntimeError(f"loopback mismatch: {name}")
    result["trailing_hex"]=s.read(256).hex()
    if result["trailing_hex"]:
        raise RuntimeError("unexpected trailing bytes")
    result["success"]=True
except Exception as error:
    result["error"]=repr(error)
    failed=True
finally:
    if s is not None:
        s.close()
        result["closed"]=not s.is_open
    result["elapsed_seconds"]=round(time.monotonic()-start,3)
    result["planned_cases"]=len(cases)
    result["passed_cases"]=sum(x["match"] for x in result["cases"])
    (run/"Loopback_Result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:result[k] for k in ("success","planned_cases","passed_cases","total_written","total_received","closed","elapsed_seconds")},ensure_ascii=False))
print("Evidence:",run/"Loopback_Result.json")
if failed:
    print(result["error"])
    raise SystemExit(1)
