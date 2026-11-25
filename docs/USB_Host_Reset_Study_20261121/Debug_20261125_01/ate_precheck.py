"""ユーザー確認済みCOM5で読取専用事前照会。異常後の再送・resetなし。"""
import datetime
import json
from pathlib import Path
import time
import serial

OUT = Path(__file__).resolve().parent

if __name__ == '__main__':
    path = OUT / 'ate_precheck.json'
    if path.exists():
        raise SystemExit('Existing evidence retained; choose a new run file')
    result = {'started': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
              'port': 'COM5', 'baud': 57600, 'events': [], 'status': 'INCOMPLETE'}
    try:
        with serial.Serial('COM5', 57600, timeout=0.05) as ate:
            initial = ate.read(4096)
            result['initial_hex'] = initial.hex()
            if initial:
                raise RuntimeError('Preexisting ATE output; stop without sending')
            for command in ('*IDN?', 'COMM_STATUS?', 'HOST_INFO? METER', 'SD_STATUS?', 'LOG_DROP_COUNT?'):
                begin = time.monotonic()
                ate.write(command.encode('ascii') + b'\r')
                raw = bytearray()
                while time.monotonic() - begin < 12:
                    raw.extend(ate.read(4096))
                    if b'\r' in raw:
                        break
                event = {'command': command, 'raw_hex': raw.hex(),
                         'elapsed_ms': round((time.monotonic() - begin) * 1000, 3)}
                result['events'].append(event)
                print(json.dumps(event), flush=True)
                if not raw.endswith(b'\r') or raw.count(b'\r') != 1:
                    raise RuntimeError('Missing or extra response; stop without retry')
                reply = raw[:-1].decode('ascii')
                event['reply'] = reply
                if command == '*IDN?' and not reply.startswith('NF55G_PICO_FIXTURE,'):
                    raise RuntimeError('Unexpected fixture identity')
                if command == 'COMM_STATUS?' and reply != 'OK:state=IDLE':
                    raise RuntimeError('Fixture not IDLE')
                if command == 'HOST_INFO? METER' and not reply.startswith('OK:HOST_INFO:BFCF2EDB84B0B37F:'):
                    raise RuntimeError('Unexpected or unavailable meter HOST')
                if command == 'SD_STATUS?' and reply != 'OK':
                    raise RuntimeError('SD not ready')
            result['status'] = 'SUCCESS'
    except Exception as exc:
        result['status'] = 'STOPPED'
        result['error'] = repr(exc)
        print(result['error'], flush=True)
    finally:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    raise SystemExit(0 if result['status'] == 'SUCCESS' else 1)
