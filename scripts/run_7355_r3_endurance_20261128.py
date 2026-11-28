"""400 fixed-wiring CDC trials. Stop at the first communication or logging failure."""

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys
import time

import serial

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'docs/USB_Host_Reset_Study_20261121/Debug_20261125_01'))
from verify_host_after_flash import HOST_INFO, IDN, exchange

sys.path.insert(0, str(ROOT))
from src.external_instrument_contract import format_query_response
from src.external_instrument_link import FrameReader


JST = dt.timezone(dt.timedelta(hours=9))
HOST_FAILURE_CAPTURE_SECONDS = 1.0
DEFAULT_INTER_TRIAL_DELAY_SECONDS = 5


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, choices=(1, 400), default=400)
    parser.add_argument('--host-version', choices=('20261125.1', '20261125.2'), default='20261125.1')
    parser.add_argument('--meter-language', choices=('scpi', 'adc'), default='scpi')
    parser.add_argument('--monitor-port', default='COM23')
    parser.add_argument('--inter-trial-delay-seconds', type=int, default=DEFAULT_INTER_TRIAL_DELAY_SECONDS,
                        help='idle seconds after a completed trial, before the next TEST_START (default: 5)')
    parser.add_argument('--ate-port', default='COM7')
    parser.add_argument('--host-chipid', default='BFCF2EDB84B0B37F')
    parser.add_argument('--range-code', choices=('R3', 'R5'), default='R3')
    parser.add_argument('--input-setpoint-mv', required=True)
    parser.add_argument('--output-root', type=Path, default=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0')
    args = parser.parse_args()
    if args.inter_trial_delay_seconds < 0:
        parser.error('--inter-trial-delay-seconds must be nonnegative')
    count = args.count
    if not re.fullmatch(r'[0-9A-Fa-f]{16}', args.host_chipid):parser.error('invalid HOST chip ID')
    host_pattern = re.compile(HOST_INFO.pattern.replace(r'20261125\.1', re.escape(args.host_version)).replace('BFCF2EDB84B0B37F',args.host_chipid.upper()))
    now = dt.datetime.now(JST)
    deadline = time.monotonic() + 24 * 3600
    out = args.output_root / f'endurance_{now:%Y%m%d_%H%M%S_%f}'
    out.mkdir()
    result = {'started': now.isoformat(), 'planned_trials': count, 'completed_trials': 0,'host_chipid':args.host_chipid.upper(),
              'inter_trial_delay_seconds': args.inter_trial_delay_seconds,
              'meter_language': args.meter_language,
              'ate_selected_range_mV': 200 if args.range_code == 'R3' else 20000,
              'input_setpoint_mV': args.input_setpoint_mv,
              'ate_port': args.ate_port, 'host_rx_only': args.monitor_port, 'host_version': args.host_version, 'status': 'STOPPED',
              'csv_recovery': 'PENDING'}
    print(f'RECORDS: {out}', flush=True)
    trial = 0
    try:
        with (out / 'ate.jsonl').open('x', encoding='utf8') as log, \
                (out / 'host_uart.bin').open('xb') as host_raw, \
                serial.Serial(args.monitor_port, 115200, timeout=0.06) as monitor, \
                serial.Serial(args.ate_port, 57600, timeout=0.05, write_timeout=1) as ate:
            reader = FrameReader()
            session = None
            last_request = None

            def receive_host(grace_seconds=0):
                offset = host_raw.tell()
                capture_until = time.monotonic() + grace_seconds
                frames = []
                while True:
                    raw = monitor.read(4096)
                    host_raw.write(raw)
                    frames.extend(reader.feed(raw))
                    if time.monotonic() >= capture_until:
                        break
                host_raw.flush()
                return frames, offset, host_raw.tell() - offset

            if ate.read(4096) or receive_host()[2]:
                raise RuntimeError('Preexisting serial output')

            def ask(command, kinds=()):
                nonlocal session
                if time.monotonic() >= deadline:
                    raise RuntimeError('24-hour limit reached')
                events = []
                sent_at = dt.datetime.now(JST).isoformat()
                extra = {}
                try:
                    reply = exchange(ate, command, events, verbose=False)
                finally:
                    try:
                        # ATEが先に期限へ達しても、HOSTの診断Eを受信専用で回収する。
                        ate_reply = events[0].get('reply', '') if events else ''
                        grace = HOST_FAILURE_CAPTURE_SECONDS if kinds == ('A', 'T', 'R') and (
                            not ate_reply or ate_reply.startswith('ERR:')) else 0
                        frames, offset, length = receive_host(grace)
                        extra = {'host_offset': offset, 'host_length': length,
                                 'host_frames': [{**f, 'session': f['session'].hex(),
                                                  'payload': f['payload'].hex()} for f in frames]}
                    finally:
                        if events:
                            log.write(json.dumps({'trial': trial, 'at': sent_at, **events[0], **extra}) + '\n')
                            log.flush()
                if reader.errors or reader.buffer or reader.dropping:
                    raise RuntimeError('Invalid or incomplete HOST UART frame')
                if kinds == ('A', 'T', 'R') and reply.startswith('ERR:'):
                    raise RuntimeError(f'{command}: {reply}; HOST frames {tuple(f["kind"] for f in frames)}')
                got = tuple(f['kind'] for f in frames)
                if got != kinds and not (kinds == ('A', 'T', 'R') and got == ('h',) + kinds):
                    raise RuntimeError(f'{command}: unexpected HOST frames {got}; expected {kinds}')
                for frame in frames:
                    if session is None:
                        session = frame['session']
                        result['session'] = session.hex()
                    if frame['session'] != session:
                        raise RuntimeError(f'{command}: parent or HOST nonce changed')
                return reply, frames

            def expect(command, value):
                if ask(command)[0] != value:
                    raise RuntimeError(f'Unexpected response for {command}')

            def host_info():
                reply, frames = ask('HOST_INFO? METER', ('i',))
                if not host_pattern.fullmatch(reply) or reply.split(':')[-2].lower() != frames[0]['session'][8:].hex():
                    raise RuntimeError(f'Expected matching meter HOST {args.host_version} READY')
                return reply

            def meter(command, timeout_ms):
                nonlocal last_request
                reply, frames = ask(f'EXT_QUERY {timeout_ms} {command}', ('A', 'T', 'R'))
                accepted, transmitted, response = frames[-3:]
                key = (response['request'], 1, response['timeout_ms'])
                if (last_request is not None and response['request'] != last_request + 1) or any(
                        (f['request'], f['mode'], f['timeout_ms']) != key for f in frames[-3:]):
                    raise RuntimeError(f'{command}: HOST request correlation mismatch')
                if accepted['payload'] or transmitted['payload'] or reply != format_query_response(response['payload']):
                    raise RuntimeError(f'{command}: HOST and ATE payload mismatch')
                last_request = response['request']
                return response['payload'].decode('ascii')

            expect('*IDN?', 'NF55G_PICO_FIXTURE,Rev.0')
            expect('COMM_STATUS?', 'OK:state=IDLE')
            host = host_info()
            expect('SD_STATUS?', 'OK')
            drops = ask('LOG_DROP_COUNT?')[0]
            if not drops.isdecimal():
                raise RuntimeError('Invalid log drop count')
            if meter('*IDN?', 2000).encode('ascii') != IDN:
                raise RuntimeError('Unexpected 7355 identity')
            read_command, error_command = ':READ?', ':SYST:ERR?'
            if args.meter_language == 'adc':
                expected = {'F?': 'F01', 'INIC?': 'INIC1', 'TRS?': 'TRS0', 'R?': args.range_code, 'H?': 'H0'}
                settings = {command: meter(command, 2500).strip() for command in expected}
                result['adc_settings'] = settings
                if settings != expected:
                    raise RuntimeError(f'Unexpected 7355 ADC settings: {settings}')
                result['conf'] = 'ADC DCV '+args.range_code+', continuous/immediate'
                read_command, error_command = 'MD?', 'ERR?'
            else:
                result['conf'] = meter(':CONF?', 2000)
            print(f'PREFLIGHT OK; CONF={result["conf"].strip()}; '
                  f'inter-trial idle={args.inter_trial_delay_seconds}s', flush=True)

            for trial in range(1, count + 1):
                expect('TEST_START', 'OK')
                read = meter(read_command, 10000)
                meter(error_command, 2500 if args.meter_language == 'adc' else 2000)
                expect('TEST_END', 'OK')
                check = ask('PICO_SELF_CHECK?')[0]
                fields = set(check.split(':', 1)[-1].split(';'))
                if not {'TEST_LOGGER=OK', 'TEST_LOG_DROP=OK'} <= fields:
                    raise RuntimeError('Missing OK logger/drop diagnostics')
                expect('SD_STATUS?', 'OK')
                expect('LOG_DROP_COUNT?', drops)
                expect('COMM_STATUS?', 'OK:state=IDLE')
                result['completed_trials'] = trial
                if trial == 1 or trial % 10 == 0:
                    print(f'{trial}/{count} completed; READ={read.strip()}', flush=True)
                # 終了確認後にだけ待機し、セット内のコマンド間隔は延ばさない。
                if trial < count and args.inter_trial_delay_seconds:
                    time.sleep(args.inter_trial_delay_seconds)

            if host_info() != host:
                raise RuntimeError('Final HOST state or nonce changed')
        result['status'] = 'TRIALS_COMPLETE_CSV_PENDING'
    except (Exception, KeyboardInterrupt) as exc:
        result['error'] = repr(exc)
        result['stopped_trial'] = trial
        print(f'STOPPED at {trial}: {exc}', flush=True)
    finally:
        result['ended'] = dt.datetime.now(JST).isoformat()
        (out / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf8')
        print(f'{result["status"]}: {out}', flush=True)
    return 0 if result['status'] == 'TRIALS_COMPLETE_CSV_PENDING' else 1


if __name__ == '__main__':
    raise SystemExit(main())
