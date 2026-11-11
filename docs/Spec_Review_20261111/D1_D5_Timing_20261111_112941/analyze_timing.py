"""SD原本とhash一致したCSVのRAW時刻から、各10回の時間とT2余裕を再計算する。"""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from src.frame import parse_frame

EXPECTED = {'D1': (100,15), 'D2': (100,30), 'D3': (200,21),
            'D4': (100,212), 'D5': (100,100)}


def main():
    recovery=json.loads((OUT/'recovery.json').read_text(encoding='utf-8'))
    assert recovery['completed'] and recovery['normal_app_restarted']
    ram=json.loads((OUT/'d4_observation.json').read_text(encoding='utf-8'))
    observations={cmd:[] for cmd in EXPECTED}
    checks=[]
    for entry in recovery['files']:
        path=OUT/entry['local']; data=path.read_bytes()
        assert hashlib.sha256(data).hexdigest()==entry['sha256']
        rows=list(csv.DictReader(data.decode().splitlines()))
        assert set(len(r) for r in csv.reader(data.decode().splitlines()))=={14}
        frames=[]; pending=[]; count=0; all_tx=[]
        for row in rows:
            if row['category']=='NF55' and row['event']=='RAW':
                wire=bytes.fromhex(row['raw_hex']); tick=int(row['detail'].split('ticks_ms=')[1])
                pending.append((row['direction'],wire,tick))
                if wire.startswith(b'\x02'):
                    frame=parse_frame(wire)
                    frames.append({'cmd':frame.cmd,'direction':row['direction'],'data_length':len(frame.data)})
            if row['event'] not in ('TRANSACTION','TIMING_OBSERVATION'):continue
            cmd=row['cmd']; all_tx.append(cmd)
            assert len(pending)==4,(cmd,pending)
            sent,ack,full,last=pending;pending=[]
            tx_frame=parse_frame(sent[1]);rx_frame=parse_frame(full[1])
            assert sent[0]=='TX' and full[0]=='RX' and tx_frame.cmd==rx_frame.cmd==cmd
            assert ack[:2]==('RX',b'\x06') and last[:2]==('TX',b'\x06')
            assert row['cmd_retry']==row['rsp_retry']=='0'
            if row['event']=='TRANSACTION':
                assert row['result']=='OK' and 'ambiguous=False' in row['detail']
            else: assert cmd=='D4' and row['result']=='OBSERVED'
            if cmd not in EXPECTED: continue  # SCはD2の受付準備であり測定10回へ含めない。
            t2,length=EXPECTED[cmd]
            assert len(rx_frame.data)==length
            record={'sample_number':len(observations[cmd])+1,'command_to_ack_ms':ack[2]-sent[2],
                    'ack_to_full_response_ms':full[2]-ack[2],
                    'command_to_full_response_ms':full[2]-sent[2],
                    'response_to_ack_ms':last[2]-full[2], 'source_csv':entry['local'],
                    'tx_tick':sent[2],'ack_tick':ack[2],'full_tick':full[2]}
            assert record['command_to_full_response_ms']==record['command_to_ack_ms']+record['ack_to_full_response_ms']
            assert record['command_to_ack_ms']>=0 and record['ack_to_full_response_ms']>=0
            observations[cmd].append(record);count+=1
        if entry['kind']=='ATE_D1_D2_D3_D5':
            assert all_tx==['D1']*10+['SC']+['D2']*10+['D3']*10+['D5']*10
            assert len(frames)==82
        else:
            assert all_tx==['D4']*10 and len(frames)==20
        checks.append(dict(local=entry['local'],sha256=entry['sha256'],sd_pc_hash_match=True,
                           data_rows=len(rows),csv_columns=14,bcc_valid_frames=len(frames),timed_samples=count))
    summary=[]
    for cmd in EXPECTED:
        rows=observations[cmd];assert len(rows)==10,(cmd,len(rows))
        t2,length=EXPECTED[cmd];values=[r['ack_to_full_response_ms'] for r in rows]
        means={key:statistics.mean(r[key] for r in rows) for key in (
            'command_to_ack_ms','ack_to_full_response_ms','command_to_full_response_ms')}
        summary.append(dict(cmd=cmd,count=len(rows),configured_t2_ms=t2,response_data_chars=length,
                            **{key.replace('_ms','_mean_ms'):value for key,value in means.items()},
                            ack_to_full_response_min_ms=min(values),ack_to_full_response_max_ms=max(values),
                            margin_vs_observed_max_ms=t2-max(values),within_t2_count=sum(v<=t2 for v in values),
                            mode='RAM single-shot observation' if cmd=='D4' else 'production ATE refresh'))
    # CSVと別にRAM保存したD4計時で、同じ10フレーム・標本順序を照合する。
    assert len(ram['rows'])==10
    differences=[a['ack_to_full_response_ms']-b['ack_to_full_response_ms']
                 for a,b in zip(observations['D4'],ram['rows'])]
    assert all(abs(d)<=1 for d in differences),differences
    result={'summary':summary,'observations':observations,'source_checks':checks,
            'd4_ram_vs_csv_delta_ms':differences,'metric_source':'Pico production RAW Logger ticks_ms',
            'definition':'TX RAW recorded after UART write; ACK RX RAW; BCC-complete frame RX RAW',
            'source_code_changed':False,'production_t2_changed':False,
            'normal_app_restarted':recovery['normal_app_restarted']}
    (OUT/'timing_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('Source checks:',checks)
    print('D4 RAM minus CSV crosscheck:',differences)


if __name__=='__main__':main()
