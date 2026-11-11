# 実機RAM専用の受信時間観測。製品用ソース／T2設定を書き換えず、CacheをVALIDにしない。
import time
import json
import binascii
from src.main import create_fixture_app
from src import config
from src.frame import build_frame
from src.nf55_decode import decode_d4

probe_app = create_fixture_app()
assert probe_app.execute_ate_line('COMM_STATUS?') == 'OK:state=IDLE'
assert probe_app.execute_ate_line('SD_STATUS?') == 'OK'
assert probe_app.execute_ate_line('STATUS_REFRESH') == 'OK'
probe_state = {'ps_on': probe_app.execute_ate_line('PS_ON?'),
               'batt_on': probe_app.execute_ate_line('BATT_ON?')}
assert probe_state == {'ps_on': '1', 'batt_on': '0'}
assert probe_app.execute_ate_line('INFO_REFRESH') == 'OK'
probe_state['fw_rev'] = probe_app.execute_ate_line('FW_REV?')

timing_result = {'kind': 'D4_single_shot_observation_no_retry_no_valid_cache',
                 'configured_t2_ms': 100, 'observation_limit_ms': 1000,
                 'ack_timeout_ms': config.T1_ACK_TIMEOUT_MS,
                 'state': probe_state, 'rows': [], 'completed': False}
assert probe_app.execute_ate_line('TEST_START') == 'OK'
probe = probe_app.protocol
original_trace = probe.trace_hook
capture = []

def trace(direction, raw):
    # 本番Loggerと同じRAW記録を維持し、測定分だけRAMへ追加保持する。
    capture.append((direction, binascii.hexlify(raw).decode(), probe.clock.ticks_ms()))
    original_trace(direction, raw)

probe.trace_hook = trace
try:
    for sample in range(1, 11):
        time.sleep_ms(150)
        assert not probe.communication_busy
        probe_app.cache.invalidate('DATA')
        probe_app.cache.invalidate('D4')
        capture = []
        probe.busy = True
        try:
            probe._set_state('TX_COMMAND')
            probe._write(build_frame('D4'))
            probe._set_state('WAIT_ACK')
            ack, reason = probe._wait_ack(config.T1_ACK_TIMEOUT_MS)
            assert ack == 'ACK', 'No ACK; stop without command retry'
            probe._set_state('WAIT_RESPONSE')
            # 100ms時点で再送せず、完全応答の時刻を観測する独立した測定窓。
            response = probe._wait_response_frame(timing_result['observation_limit_ms'])
            assert response is not None, 'Observation limit reached; stop'
            parsed, error = probe._validate_response(response, 'D4', 212)
            assert parsed is not None and parsed.cmd == 'D4' and len(parsed.data) == 212, 'Invalid D4'
            probe._set_state('TX_RESPONSE_ACK')
            probe._write(bytes((config.ACK,)))
        finally:
            probe.busy = False
            probe._set_state('IDLE')
        decode_d4(parsed.data)
        assert len(capture) == 4, 'Unexpected EB or extra raw; preserve and stop'
        sent, ack_row, full, sent_ack = capture
        assert ack_row[1] == '06' and sent_ack[1] == '06'
        row = {'sample_number': sample, 'command_to_ack_ms': ack_row[2] - sent[2],
               'ack_to_full_response_ms': full[2] - ack_row[2],
               'command_to_full_response_ms': full[2] - sent[2],
               'raw': capture, 'data_length': len(parsed.data), 'bcc_ok': True,
               'command_retry': 0, 'response_retry': 0}
        row['within_configured_t2'] = row['ack_to_full_response_ms'] <= 100
        timing_result['rows'].append(row)
        probe_app.logger.log(category='NF55', cmd='D4', event='TIMING_OBSERVATION',
                             result='OBSERVED', cmd_retry=0, rsp_retry=0,
                             detail='sample={};t2_ms=100;ack_to_full_ms={};within_t2={}'.format(
                                 sample, row['ack_to_full_response_ms'], row['within_configured_t2']))
        assert not probe_app.cache.is_valid('DATA') and not probe_app.cache.is_valid('D4')
        probe_app.service_once()
    assert probe_app.execute_ate_line('TEST_END') == 'OK'
    timing_result['self_check'] = probe_app.execute_ate_line('PICO_SELF_CHECK?')
    timing_result['sd_status'] = probe_app.execute_ate_line('SD_STATUS?')
    timing_result['log_drop'] = probe_app.execute_ate_line('LOG_DROP_COUNT?')
    assert timing_result['self_check'].startswith('OK:')
    assert timing_result['sd_status'] == 'OK' and timing_result['log_drop'] == '0'
    assert not probe_app.cache.is_valid('DATA') and not probe_app.cache.is_valid('D4')
    timing_result['completed'] = True
except Exception as exc:
    timing_result['error'] = repr(exc)
    if not probe.communication_busy:
        timing_result['cleanup_test_end'] = probe_app.execute_ate_line('TEST_END')
finally:
    probe.trace_hook = original_trace
    timing_json = json.dumps(timing_result)
print('D4_OBSERVATION_COMPLETE', timing_result['completed'], len(timing_result['rows']))
