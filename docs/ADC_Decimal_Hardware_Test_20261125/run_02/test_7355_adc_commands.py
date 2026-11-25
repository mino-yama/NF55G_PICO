"""7355 USB CDCのADCコマンド実機確認。NF55Gの校正値は操作しない。"""
import argparse
from contextlib import ExitStack
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import time

import serial


def run(port, monitor, record, options):
    def ate(command):
        started = time.monotonic()
        port.write(command.encode('ascii') + b'\r')
        raw = port.read_until(b'\r')
        row = {'command': command, 'elapsed_ms': round((time.monotonic() - started) * 1000),
               'ate_raw_hex': raw.hex()}
        record['operations'].append(row)
        if monitor is not None:
            row['monitor_hex'] = monitor.read_all().hex()
        if not raw.endswith(b'\r'):
            raise TimeoutError(command)
        response = raw[:-1].decode('ascii')
        row['response'] = response
        return response

    def query(command):
        time.sleep(.025)
        reply = ate('EXT_QUERY 2500 ' + command)
        parts = reply.split(':', 3)
        if len(parts) != 4 or parts[:2] != ['OK', 'EXT_RX']:
            raise RuntimeError((command, reply))
        raw = bytes.fromhex(parts[3])
        if int(parts[2]) != len(raw) or not raw.endswith(b'\r\n'):
            raise RuntimeError((command, raw))
        record['operations'][-1]['instrument_raw_hex'] = raw.hex()
        print(command, '->', repr(raw), flush=True)
        return raw[:-2].decode('ascii')

    def send(command):
        time.sleep(.025)
        reply = ate('EXT_SEND 2500 ' + command)
        if reply != 'OK:EXT_TX':
            raise RuntimeError((command, reply))

    def check(actual, expected):
        if actual != expected:
            raise RuntimeError((actual, expected))

    def configure(setting, verification, expected=None):
        send(setting)
        value = query(verification)
        if expected is not None:
            check(value, expected)
        return value

    check(ate('COMM_STATUS?'), 'OK:state=IDLE')
    host = ate('HOST_INFO? METER')
    if not host.startswith('OK:HOST_INFO:') or not host.endswith(':READY'):
        raise RuntimeError(host)
    identity = query('*IDN?')
    if identity.split(',')[1:2] != ['7355']:
        raise RuntimeError(identity)
    if configure('F1', 'F?') not in ('F1', 'F01'):
        raise RuntimeError('DCV function not confirmed')
    for command in ('R?', 'INIC?', 'TRS?', 'H?', 'CMP?'):
        query(command)
    configure('H0', 'H?', 'H0')
    continuation = 'INIC1' if options.continuous else 'INIC0'
    configure(continuation, 'INIC?', continuation)
    trigger = 'TRS0' if options.immediate or options.continuous else 'TRS3'
    configure(trigger, 'TRS?', trigger)
    configure('SPN1', 'SPN?', 'SPN00001')
    configure('TRN1', 'TRN?', 'TRN00001')
    configure('TRD0', 'TRD?')
    configure('ST0', 'ST?', 'ST0')
    configure('RN0', 'RN?')
    if options.continuous:
        configure('PR4', 'PR?', 'PR4')
    for range_code in options.ranges:
        configure(range_code, 'R?', range_code)
        for _ in range(options.samples):
            query('MSR?')
            if not options.continuous:
                send('ABO,INI')
            if trigger == 'TRS3':
                send('*TRG')
            deadline = time.monotonic() + 4
            while not int(query('MSR?')) & 256:
                if time.monotonic() >= deadline:
                    raise TimeoutError('measurement completion')
            data = query('MD?')
            value = Decimal(data)
            if not value.is_finite():
                raise ValueError(data)
            if value.copy_abs() < Decimal('1E+35'):
                record['samples'].append({'range': range_code, 'raw': data, 'value_v': str(value)})
            else:
                record['samples'].append({'range': range_code, 'raw': data, 'status': 'OUT_OF_RANGE'})
    query('ERR?')
    if options.check_cal_cache:
        check(ate('SD_STATUS?'), 'OK')
        check(ate('TEST_START'), 'OK')
        try:
            for range_code in ('R5', 'R3', 'R5'):
                configure(range_code, 'R?', range_code)
                measurement = ate('CAL_MEASURE_BATT_V A 4000 MD?')
                cached = ate('CAL_MEASUREMENT_BATT_V? A')
                if range_code == 'R3':
                    check(measurement, 'ERR:CAL_MEASUREMENT_OVERRANGE')
                    check(cached, 'ERR:CAL_MEASUREMENT_INVALID')
                else:
                    if not measurement.startswith('OK:CAL_MEASURE:'):
                        raise RuntimeError(measurement)
                    fields = cached.split(':')
                    token = measurement.split(':')[-1]
                    check(fields[:5], ['OK', 'CAL_MEASUREMENT', token, 'BATT_V', 'A'])
                    check(fields[6:9], ['V', fields[5], 'V'])
                    check(bytes.fromhex(fields[9]), fields[5].encode('ascii') + b'\r\n')
                print(measurement, cached, flush=True)
        finally:
            check(ate('TEST_END'), 'OK')
        check(ate('LOG_DROP_COUNT?'), '0')
    check(ate('COMM_STATUS?'), 'OK:state=IDLE')
    record['result'] = 'COMPLETE'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default='COM5')
    parser.add_argument('--ranges', nargs='+', choices=('R0', 'R3', 'R5'), default=['R5', 'R3'])
    parser.add_argument('--samples', type=int, choices=range(1, 11), default=3)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--immediate', action='store_true')
    mode.add_argument('--continuous', action='store_true')
    parser.add_argument('--monitor-port')
    parser.add_argument('--check-cal-cache', action='store_true',
                        help='実入力が200 mV超、20 V未満のときBATT_Vキャッシュを試験')
    options = parser.parse_args()
    if options.check_cal_cache and not options.continuous:
        parser.error('--check-cal-cache requires --continuous')
    output = Path(__file__).with_name(f'ADC_Command_HIL_{datetime.now():%Y%m%d_%H%M%S_%f}.json')
    record = {'port': options.port, 'monitor_port': options.monitor_port,
              'trigger': ('CONTINUOUS' if options.continuous else
                          'IMMEDIATE' if options.immediate else 'BUS'),
              'operations': [], 'samples': []}
    try:
        with ExitStack() as stack:
            port = stack.enter_context(serial.Serial(options.port, 57600, timeout=6))
            port.reset_input_buffer()
            monitor = None
            if options.monitor_port:
                monitor = serial.Serial(baudrate=115200, timeout=0)
                monitor.dtr = monitor.rts = False
                monitor.port = options.monitor_port
                monitor.open()
                stack.callback(monitor.close)
                monitor.reset_input_buffer()
            run(port, monitor, record, options)
    except Exception as error:
        record['result'] = 'STOPPED'
        record['error'] = repr(error)
        raise
    finally:
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(output, flush=True)


if __name__ == '__main__':
    main()
