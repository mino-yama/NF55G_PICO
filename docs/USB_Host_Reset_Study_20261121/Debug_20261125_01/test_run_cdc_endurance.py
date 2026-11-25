"""Exercise HOST error capture and inter-trial pacing without hardware."""

from collections import deque
from contextlib import nullcontext, redirect_stdout
import io
from itertools import count
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import run_cdc_endurance as runner
from src.external_instrument_contract import encode_frame, format_query_response


class EnduranceRunnerTest(unittest.TestCase):
    def run_simulation(self, trial_count, diagnostic=None):
        session = bytes.fromhex('b3a22bbe4d66e8604a7326ac8de43546')
        chunks = deque()
        commands = []
        waits = []
        requests = count(1)

        class Monitor:
            def read(self, _size):
                return chunks.popleft() if chunks else b''

        def exchange(_ate, command, events, **_kwargs):
            commands.append(command)
            replies = {
                '*IDN?': 'NF55G_PICO_FIXTURE,Rev.0',
                'COMM_STATUS?': 'OK:state=IDLE',
                'SD_STATUS?': 'OK',
                'LOG_DROP_COUNT?': '0',
                'TEST_START': 'OK',
                'TEST_END': 'OK',
                'PICO_SELF_CHECK?': 'OK:TEST_LOGGER=OK;TEST_LOG_DROP=OK',
            }
            if command == 'HOST_INFO? METER':
                reply = f'OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-20261125.2:{session[8:].hex()}:READY'
                chunks.append(encode_frame(session, 1, 'i', 0, 1000, b''))
            elif command.startswith('EXT_QUERY '):
                _, timeout, query = command.split(' ', 2)
                request = next(requests)
                timeout = int(timeout)
                initial = b''.join(encode_frame(session, request, kind, 1, timeout, b'') for kind in 'AT')
                if query == ':READ?' and diagnostic is not None:
                    error = encode_frame(session, request, 'E', 1, timeout, diagnostic)
                    chunks.extend((initial, b'', error[:40], error[40:]))
                    reply = 'ERR:EXT_TIMEOUT:AMBIGUOUS=1'
                else:
                    payload = {
                        '*IDN?': runner.IDN,
                        ':CONF?': b'VOLT\r\n',
                        ':READ?': b'+0040.407E-03\r\n',
                        ':SYST:ERR?': b'+0,"No error"\r\n',
                    }[query]
                    chunks.append(initial + encode_frame(session, request, 'R', 1, timeout, payload))
                    reply = format_query_response(payload)
            else:
                reply = replies[command]
            events.append({'command': command, 'reply': reply})
            return reply

        ticks = count(step=0.2)
        with TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()), \
                patch.object(sys, 'argv', ['runner', '--count', str(trial_count), '--host-version', '20261125.2']), \
                patch.object(runner, '__file__', str(Path(tmp) / 'runner.py')), \
                patch.object(runner.time, 'monotonic', side_effect=lambda: next(ticks)), \
                patch.object(runner.time, 'sleep', side_effect=lambda delay: waits.append((len(commands), delay))), \
                patch.object(runner.serial, 'Serial', side_effect=lambda *_a, **_kw: nullcontext(Monitor())), \
                patch.object(runner, 'exchange', side_effect=exchange):
            exit_code = runner.main()
            trial_path, = Path(tmp).iterdir()
            records = (trial_path / 'ate.jsonl').read_text(encoding='utf8').splitlines()
            last = json.loads(records[-1])
            result = json.loads((trial_path / 'result.json').read_text(encoding='utf8'))
        return exit_code, result, last, commands, waits

    def test_delayed_split_error_is_recorded_without_resending_read(self):
        diagnostic = b'TIMEOUT_RX0_T1_C0_XNONE_I9999_N9999_D0_S80_P5A_EP81_H1_K0_L0/64_OA1_ON0_OX0_OPD2_OE02|1'
        exit_code, result, last, commands, waits = self.run_simulation(1, diagnostic)
        self.assertEqual(exit_code, 1)
        self.assertEqual(result['status'], 'STOPPED')
        self.assertEqual(result['completed_trials'], 0)
        self.assertEqual(result['stopped_trial'], 1)
        self.assertIn(last['reply'], result['error'])
        self.assertEqual([f['kind'] for f in last['host_frames']], ['A', 'T', 'E'])
        self.assertEqual(last['host_frames'][-1]['payload'], diagnostic.hex())
        self.assertEqual(commands[-2:], ['TEST_START', 'EXT_QUERY 10000 :READ?'])
        self.assertEqual(commands.count('EXT_QUERY 10000 :READ?'), 1)
        self.assertEqual(waits, [])

    def test_five_second_wait_is_only_between_completed_trials(self):
        exit_code, result, _, commands, waits = self.run_simulation(400)
        self.assertEqual(exit_code, 0)
        self.assertEqual(result['completed_trials'], 400)
        self.assertEqual(result['inter_trial_delay_seconds'], 5)
        starts = [index for index, command in enumerate(commands) if command == 'TEST_START']
        self.assertEqual(len(starts), 400)
        self.assertEqual(waits, [(index, 5) for index in starts[1:]])
        for index, _ in waits:
            self.assertEqual(commands[index - 1], 'COMM_STATUS?')

    def test_single_successful_trial_does_not_wait(self):
        exit_code, result, _, _, waits = self.run_simulation(1)
        self.assertEqual(exit_code, 0)
        self.assertEqual(result['completed_trials'], 1)
        self.assertEqual(waits, [])


if __name__ == '__main__':
    unittest.main()
