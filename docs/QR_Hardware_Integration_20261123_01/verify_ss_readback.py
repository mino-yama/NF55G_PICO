"""保存済み製品応答のBCCと全100文字を比較する。機器送信なし。"""
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent/'SS_HIL_01'
sys.path.insert(0,str(OUT.parents[2]))
from src.frame import parse_frame

result=json.loads((OUT/'result.json').read_text(encoding='utf-8'))
raw=bytes.fromhex(result['parent']['rx_hex'])
frames=[];offset=0
while True:
    start=raw.find(b'\x02',offset)
    if start<0:
        break
    end=raw.index(b'\x03',start)+3
    frames.append(parse_frame(raw[start:end]))
    offset=end
assert [frame.cmd for frame in frames]==['D5','SS','D5']
before,after=frames[0].data,frames[2].data
assert len(before)==len(after)==100 and frames[1].data==b''
assert before[:6]==after[:6] and before[20:]==after[20:]
assert after[6:20]==b'A1. 2601000001'
comparison=dict(response_commands=['D5','SS','D5'],all_bcc_valid=True,
    d5_before_hex=before.hex(),d5_after_hex=after.hex(),
    changed_positions_1based=[i+1 for i,(a,b) in enumerate(zip(before,after)) if a!=b],
    unit_expected_match=True,fw_adu_bbu_reserve_parameter_unchanged=True)
(OUT/'readback_comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
print(json.dumps(comparison,indent=2))
