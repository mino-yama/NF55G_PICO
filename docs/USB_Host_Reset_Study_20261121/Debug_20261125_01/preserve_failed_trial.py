"""Close the stopped trial for SD evidence. Never send a meter command."""
import json
from pathlib import Path
import sys

import serial

from verify_host_after_flash import exchange


def main(out):
    result = json.loads((out / 'result.json').read_text(encoding='utf8'))
    assert result['status'] == 'STOPPED' and result['stopped_trial'] == result['completed_trials'] + 1
    samples = (out / 'ate.jsonl').read_text(encoding='utf8').splitlines()
    last = json.loads(samples[-1])
    assert last['trial'] == result['stopped_trial']
    assert last['command'] in ('EXT_QUERY 10000 :READ?', 'EXT_QUERY 2000 :SYST:ERR?',
                               'EXT_QUERY 10000 MD?', 'EXT_QUERY 2500 ERR?')
    assert last['reply'] == 'ERR:EXT_TIMEOUT:AMBIGUOUS=1'
    events = []
    with (out / 'failed_trial_close.json').open('x', encoding='utf8') as log:
        try:
            with serial.Serial('COM5', 57600, timeout=0.05, write_timeout=1) as ate:
                assert not ate.read(4096), 'Unexpected input before preservation'
                assert exchange(ate, 'COMM_STATUS?', events) == 'OK:state=IDLE'
                assert exchange(ate, 'SD_STATUS?', events) == 'OK'
                info = exchange(ate, 'HOST_INFO? METER', events)
                prefix = f"OK:HOST_INFO:BFCF2EDB84B0B37F:meter-host-relay-{result['host_version']}:"
                assert info.lower() == (prefix + result['session'][16:] + ':FAULT').lower()
                assert exchange(ate, 'TEST_END', events) == 'OK'
        finally:
            json.dump({'purpose': 'failed trial evidence only', 'events': events}, log, indent=2)


if __name__ == '__main__':
    main(Path(__file__).resolve().parent / sys.argv[1])
