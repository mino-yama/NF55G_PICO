import json
import sys
import time
from datetime import datetime
from pathlib import Path

import serial

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.qr_reader import decode_nf55g_label
from src.qr_write_session import serial_data_from_qr


seconds = int(sys.argv[1])
case = Path('docs/QR_Hardware_Integration_20261123_01')
output = case / ('QR_Read_20261125_' + datetime.now().strftime('%H%M%S_%f') + '.json')
record = {'port': 'COM5', 'window_ms': seconds * 1000, 'operations': []}

try:
    with serial.Serial('COM5', 57600, timeout=8) as port:
        port.reset_input_buffer()

        def request(command, display=True):
            port.write(command.encode('ascii') + b'\r')
            response = port.read_until(b'\r').rstrip(b'\r').decode('ascii')
            record['operations'].append({'command': command, 'response': response})
            if display:
                print(command, '->', response, flush=True)
            return response

        assert request('COMM_STATUS?') == 'OK:state=IDLE'
        assert request('SD_STATUS?') == 'OK'
        assert request('TEST_START') == 'OK'
        try:
            reply = request(f'QR_SCAN {seconds * 1000}')
            if not reply.startswith('OK:QR_ARMED:'):
                raise RuntimeError(reply)
            token = reply.split(':')[-1]
            print('QR_ARMED', flush=True)
            until = time.monotonic() + seconds + 2
            while time.monotonic() < until:
                reply = request('QR_GET? ' + token, display=False)
                if reply != 'ERR:QR_READING':
                    break
                time.sleep(.5)
            print('QR_GET?', '->', reply, flush=True)
            if reply.startswith('OK:QR_GET:' + token + ':'):
                raw = reply.split(':', 3)[3]
                record['fields'] = decode_nf55g_label(raw)
                assert request('QR_DATA? ' + token) == 'OK:QR_DATA:' + token + ':' + serial_data_from_qr(raw).hex()
                record['result'] = 'QR_READ_AND_DATA_CONFIRMED'
            elif reply == 'ERR:QR_TIMEOUT':
                record['result'] = 'TIMEOUT_CONFIRMED'
            else:
                raise RuntimeError(reply)
        finally:
            assert request('TEST_END') == 'OK'
        assert request('QR_GET? ' + token) == 'ERR:QR_STALE_ID'
        assert request('LOG_DROP_COUNT?') == '0'
except Exception as error:
    record['error'] = repr(error)
    raise
finally:
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(output, flush=True)
