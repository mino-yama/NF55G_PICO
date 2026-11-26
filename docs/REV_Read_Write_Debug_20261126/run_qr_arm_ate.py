"""Read-only QR HIL through COM5, with the parent candidate loaded in RAM via COM6."""
import ast
import json
from pathlib import Path
from queue import Empty, Queue
import re
import subprocess
import sys
from threading import Thread
import time

import serial


case = Path(__file__).resolve().parent
root = case.parents[1]
run_dir = Path(sys.argv[1]).resolve()
assert run_dir.parent == case
late_only = sys.argv[2:] == ['--late-only']
assert not sys.argv[2:] or late_only
run_dir.mkdir(exist_ok=True)
label_file = case.parent / 'QR_Hardware_Integration_20261123_01/Production_Label_Retest_20261125/expected.json'
sample = json.loads(label_file.read_text(encoding='utf8'))['B']
source = run_dir / 'parent_ate_ram.py'
with source.open('x', encoding='utf8') as file:
    file.write('import gc, sys\n')
    code = (root / 'src/qr_write_session.py').read_text(encoding='utf8')
    code = re.sub(r'from \.(\w+) import', r'from src.\1 import', code)
    file.write(f'qr_write_session_ns={{"__name__": "src.qr_write_session"}}\n'
               f'exec({code!r}, qr_write_session_ns)\ngc.collect()\n')
    port_text = (root / 'src/qr_pio_rx.py').read_text(encoding='utf8')
    port_class = next(node for node in ast.parse(port_text).body
                      if isinstance(node, ast.ClassDef) and node.name == 'QRPioUART')
    port_code = ast.get_source_segment(port_text, port_class)
    port_code = re.sub(r'from \.(\w+) import', r'from src.\1 import', port_code)
    # Reuse the copy of the RX program already allocated to the live Pico's PIO.
    file.write('qr_pio_rx_ns=dict(sys.modules["src.qr_pio_rx"].__dict__)\n'
               f'exec({port_code!r}, qr_pio_rx_ns)\ngc.collect()\n')
    main_text = (root / 'src/main.py').read_text(encoding='utf8')
    fixture_class = next(node for node in ast.parse(main_text).body
                         if isinstance(node, ast.ClassDef) and node.name == 'FixtureApp')
    main_lines = main_text.splitlines(keepends=True)
    hooks = 'class CandidateApp(FixtureApp):\n' + '\n'.join(
        ''.join(main_lines[node.lineno-1:node.end_lineno]) for node in fixture_class.body
        if isinstance(node, ast.FunctionDef) and node.name in ('service_once', '_execute_qr'))
    file.write('main_ns=dict(sys.modules["src.main"].__dict__)\n'
               'main_ns["QRWriteError"]=qr_write_session_ns["QRWriteError"]\n'
               f'exec({hooks!r}, main_ns)\ngc.collect()\n'
               'QR_SESSION=qr_write_session_ns["QRWriteSession"]\n'
               'QR_PORT=qr_pio_rx_ns["QRPioUART"]\nCANDIDATE_APP=main_ns["CandidateApp"]\n')
    file.write((case / 'qr_arm_ate_ram_parent.py').read_text(encoding='utf8'))

lines = Queue()
base = [sys.executable, '-u', '-m', 'mpremote', 'connect', 'COM6', 'resume']


def trace(stream, log):
    for line in stream:
        log.write(line)
        log.flush()
        if line.startswith('QR_ATE_'):
            lines.put(line.rstrip())
    lines.put(None)


def wait_record(timeout, predicate):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            line = lines.get(timeout=max(.01, deadline - time.monotonic()))
        except Empty:
            break
        if line is None:
            raise RuntimeError('Parent ended; see parent_wire.log')
        if predicate(line):
            return line
    raise TimeoutError('Expected QR HOST record not received; see parent_wire.log')


def unpack_health(line):
    return tuple(map(int, line.split('|')[1:]))


with (run_dir / 'parent_wire.log').open('x', encoding='utf8') as parent_log, \
        (run_dir / 'ate_wire.jsonl').open('x', encoding='utf8') as ate_log:
    parent = subprocess.Popen(base + ['run', str(source)], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, encoding='utf8', errors='replace')
    reader = Thread(target=trace, args=(parent.stdout, parent_log), daemon=True)
    reader.start()
    try:
        wait_record(35, lambda line: line == 'QR_ATE_PARENT_READY')
        wait_record(12, lambda line: line.startswith('QR_ATE_HEALTH|') and unpack_health(line)[-1] & 1)
        with serial.Serial('COM5', 57600, timeout=3) as port:
            port.reset_input_buffer()

            def ask(command):
                port.write(command.encode('ascii') + b'\r')
                raw = port.read_until(b'\r')
                reply = raw.decode('ascii').rstrip('\r')
                event = {'command': command, 'reply': reply, 'time': time.time()}
                ate_log.write(json.dumps(event) + '\n')
                ate_log.flush()
                if not raw.endswith(b'\r'):
                    raise TimeoutError(command)
                return reply

            def pending(timeout):
                reply = ask(f'QR_SCAN {timeout}')
                assert reply.startswith('OK:QR_PENDING:'), reply
                return reply.split(':')[-1]

            def arm(token, discard):
                host_id = token[1:17].upper() + token[-8:]
                ack = wait_record(8, lambda line: line.startswith('QR_ATE_ACK|') and line.split('|')[3] == host_id)
                assert int(ack.rsplit('|', 1)[1]) == discard, ack
                assert ask('QR_GET? ' + token) == 'ERR:QR_READING'
                print('ATE_HIL_SCAN_B|', discard, token, flush=True)
                wait_record(60, lambda line: line.startswith('QR_ATE_TEXT|') and line.rsplit('|', 1)[1] == host_id)
                reply = ask('QR_GET? ' + token)
                assert reply == 'OK:QR_GET:' + token + ':' + sample['payload'], reply
                expected = 'OK:QR_DATA:' + token + ':' + sample['ss_data_hex'].lower()
                assert ask('QR_DATA? ' + token) == expected
                assert ask('QR_WRITE ' + token) == 'ERR:NF55G_NOT_CONNECTED'
                print('ATE_HIL_B_VERIFIED|', discard, token, flush=True)

            assert ask('*IDN?') == 'NF55G_PICO_FIXTURE,Rev.0'
            assert ask('COMM_STATUS?') == 'NG:NO_PROTOCOL'
            assert ask('SD_STATUS?') == 'OK'
            assert ask('TEST_START') == 'OK'
            try:
                if not late_only:
                    cancelled = pending(60000)
                    assert ask('QR_CANCEL') == 'OK'
                    assert ask('QR_DATA? ' + cancelled) == 'ERR:QR_STALE_ID'
                    timed_out = pending(300)
                    time.sleep(.4)
                    assert ask('QR_GET? ' + timed_out) == 'ERR:QR_TIMEOUT'
                    print('ATE_HIL_CANCEL_TIMEOUT_OK', flush=True)
                    arm(pending(60000), 0)
                while not lines.empty():
                    lines.get_nowait()
                health = wait_record(5, lambda line: line.startswith('QR_ATE_HEALTH|'))
                _, _, _, completed, hid, _ = unpack_health(health)

                def a_in_progress(line):
                    global completed, hid
                    if not line.startswith('QR_ATE_HEALTH|'):
                        return False
                    _, _, drops, reads, reports, flags = unpack_health(line)
                    assert not drops and flags & 1, line
                    if reads != completed:
                        completed, hid = reads, reports
                        print('ATE_HIL_A_COMPLETED_BEFORE_REQUEST', flush=True)
                        return False
                    return reports > hid

                print('ATE_HIL_SCAN_A', flush=True)
                wait_record(90, a_in_progress)
                arm(pending(60000), 1)
            finally:
                port.timeout = 15
                assert ask('TEST_END') == 'OK'
                print('ATE_HIL_TEST_END_OK', flush=True)
        assert parent.wait(timeout=15) == 0
        print('ATE_HIL_COMPLETE', flush=True)
    finally:
        if parent.poll() is None:
            parent.terminate()
            parent.wait(timeout=10)
        reader.join(timeout=5)
        subprocess.run(base + ['exec', '--no-follow', "import sys; sys.modules['src.main'].active_app.run()"],
                       timeout=15, check=True)
