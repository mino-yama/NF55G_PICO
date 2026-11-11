"""任意の診断UARTを受信して保存する。実行時のみポートを開く。機器へ送信しない。"""
import argparse
import time
from pathlib import Path
import serial

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',required=True)
    p.add_argument('--seconds',type=float,default=20)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if not 0<args.seconds<=120:
        p.error('seconds must be 0..120')
    # 接続前から待受が必要。サブMCU TX→変換器RX／GNDのみ、VCCと変換器TXは接続しない。
    # ポート名だけでは対象を判別できないため、実行前に変換器の型番とCOMを照合する。
    with args.output.open('xb') as f:
        with serial.Serial(args.port,115200,timeout=0.1) as port:
            deadline=time.monotonic()+args.seconds
            while time.monotonic()<deadline:
                chunk=port.read(4096)
                if chunk:f.write(chunk)
