"""RAM版と同じ依存・フラグで任意UART分岐だけを構文検査。リンク／実機確認ではない。"""
import ctypes
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2]
folder=Path(__file__).parent
lines=(folder/'main_compile_command.txt').read_text(encoding='utf-8-sig').splitlines()
command=next(x for x in lines if ' -c ' in x and x.endswith('/main.c"'))
argc=ctypes.c_int()
f=ctypes.windll.shell32.CommandLineToArgvW
f.restype=ctypes.POINTER(ctypes.c_wchar_p)
p=f(command,ctypes.byref(argc))
argv=[p[i] for i in range(argc.value)]
ctypes.windll.kernel32.LocalFree(p)
assert argv[0].endswith('arm-none-eabi-gcc.exe')
args=[]
i=0
while i<len(argv):
    arg=argv[i]
    if arg in ('-o','-MT','-MF'):
        i+=2;continue
    if arg in ('-c','-MD'):
        i+=1;continue
    args.append(arg.replace('-DPROBE_UART_TX_PIN=-1','-DPROBE_UART_TX_PIN=0'))
    i+=1
assert '-DPROBE_UART_TX_PIN=0' in args
args.append('-fsyntax-only')
r=subprocess.run(args,cwd=root/'firmware/usb_submcu_host_probe/build',capture_output=True,text=True)
print(r.stdout,r.stderr)
print('UART GP0 syntax-only exit:',r.returncode)
raise SystemExit(r.returncode)
