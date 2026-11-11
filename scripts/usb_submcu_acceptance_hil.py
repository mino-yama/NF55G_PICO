"""USB単体確認FW専用。USB serialで対象を限定し、全送受信をJSONへ残す。"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import serial
from serial.tools import list_ports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', required=True)
    parser.add_argument('--build', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite evidence')
    matches = [p for p in list_ports.comports() if
               (p.serial_number or '').lower() == args.serial.lower() and p.vid == 0x2E8A]
    if len(matches) != 1:
        raise SystemExit('Expected exactly one matching USB serial device: ' + repr(matches))
    evidence = {'started_utc': datetime.now(timezone.utc).isoformat(),
                'usb_serial': args.serial, 'port': matches[0].device,
                'expected_build': args.build, 'events': [], 'checks': 0}
    port = serial.Serial()
    port.port = matches[0].device
    port.baudrate = 115200
    port.timeout = 0.1
    port.write_timeout = 1
    port.dtr = True
    port.rts = False

    def check(ok, detail):
        evidence['checks'] += 1
        if not ok:
            raise AssertionError(detail)

    def receive():
        end = time.monotonic() + 3
        data = bytearray()
        while time.monotonic() < end:
            part = port.read(1)
            if part:
                data.extend(part)
                if data.endswith(b'\r\n'):
                    evidence['events'].append({'rx_hex': data.hex(), 'rx': data.decode('ascii')})
                    return bytes(data[:-2])
        raise AssertionError('Response timeout: ' + data.hex())

    def send(parts):
        for part in parts:
            evidence['events'].append({'tx_hex': part.hex()})
            port.write(part)
            port.flush()
            time.sleep(0.02)

    def exchange(parts, expected):
        send(parts)
        got = receive()
        check(got == expected, repr((got, expected)))

    def settle():
        time.sleep(0.25)
        banner = port.read_all()
        evidence['events'].append({'connection_rx_hex': banner.hex()})
        check(banner in (b'', b'READY:USB_SUBMCU_ACCEPTANCE\r\n'), 'Unexpected connection data')

    try:
        port.open()
        settle()
        send([b'ID?\r\n'])
        identity = receive().decode('ascii')
        fields = dict(item.split('=', 1) for item in identity.split(';'))
        check(fields.get('FW') == 'USB_SUBMCU_ACCEPTANCE', 'Wrong FW')
        check(fields.get('VERSION') == 'dev-20261111.1', 'Wrong version')
        check(fields.get('BUILD') == args.build, 'Wrong build')
        check(fields.get('ID', '').lower() == args.serial.lower(), 'Wrong board ID')
        check(all(fields.get(k) == 'OFF' for k in ('USB_HOST', 'UART', 'PIO')), 'Wrong scope')
        for ending in (b'\r', b'\n', b'\r\n'):
            exchange([b'PING' + ending], b'PONG')
        exchange([b'PI', b'NG\r', b'\n'], b'PONG')
        send([b'PING\r\nUPTIME?\r\n'])
        check(receive() == b'PONG', 'Combined PING')
        first = int(receive().removeprefix(b'UPTIME_MS='))
        time.sleep(0.05)
        send([b'UPTIME?\n'])
        second = int(receive().removeprefix(b'UPTIME_MS='))
        check(second > first, 'Uptime did not advance')
        evidence['uptime_ms'] = [first, second]
        exchange([b'ECHO 00-AbCd-123456\n'], b'ECHO=00-AbCd-123456')
        exchange([b'ECHO ' + b'Z' * 90 + b'\n'], b'ECHO=' + b'Z' * 90)
        exchange([b'X' * 96 + b'\r\n'], b'ERR:LINE_TOO_LONG')
        exchange([b'PING\n'], b'PONG')
        exchange([b'PI\x00NG\n'], b'ERR:ASCII')
        exchange([b'PING\n'], b'PONG')
        exchange([b'FW_UPDATE\n'], b'ERR:UNKNOWN_CMD')
        send([b'\r\n\n\r'])
        time.sleep(0.15)
        check(port.read_all() == b'', 'Empty-line response or duplicate reply')
        for n in range(100):
            value = ('seq-%03d-00aAZz' % n).encode('ascii')
            exchange([b'ECHO ' + value + b'\r\n'], b'ECHO=' + value)
        # 部分行を残して切断し、次の接続が旧行を引き継がないことを実機で確認する。
        send([b'ECHO stale'])
        port.close()
        time.sleep(0.25)
        port.open()
        settle()
        exchange([b'PING\r\n'], b'PONG')
        time.sleep(0.15)
        check(port.read_all() == b'', 'Unexpected trailing response')
        evidence['status'] = 'PASS'
    except Exception as exc:
        evidence['status'] = 'FAIL'
        evidence['error'] = repr(exc)
        raise
    finally:
        port.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as target:
            json.dump(evidence, target, ensure_ascii=False, indent=2)
        print(json.dumps({k: v for k, v in evidence.items() if k != 'events'}, ensure_ascii=True))


if __name__ == '__main__':
    main()
