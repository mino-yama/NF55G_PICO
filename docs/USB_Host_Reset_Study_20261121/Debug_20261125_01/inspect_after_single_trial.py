"""停止後のATE状態だけを照会する。測定・自己診断の再送やリセットはしない。"""

import datetime as dt
import json
from pathlib import Path

import serial

from verify_host_after_flash import exchange


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    path = Path(__file__).with_name(f'ate_stop_inspection_{now:%Y%m%d_%H%M%S_%f}.json')
    result = {'started': now.isoformat(), 'events': [], 'status': 'STOPPED'}
    try:
        with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
            # 遅延応答が残っていたら、新しい要求と混同せず保存して終了する。
            initial = ate.read(4096)
            result['initial_hex'] = initial.hex()
            if initial:
                raise RuntimeError('Preexisting ATE output; no new commands sent')
            for command in ('COMM_STATUS?', 'SD_STATUS?', 'LOG_DROP_COUNT?', 'HOST_INFO? METER'):
                reply = exchange(ate, command, result['events'])
                if reply.startswith(('ERR:', 'NG:')):
                    raise RuntimeError(f'Diagnostic error: {reply}')
        result['status'] = 'COMPLETED'
    except Exception as exc:
        result['error'] = repr(exc)
    finally:
        with path.open('x', encoding='utf8') as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
        print(f"{result['status']}: {path}", flush=True)
    return 0 if result['status'] == 'COMPLETED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
