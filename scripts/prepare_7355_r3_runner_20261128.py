"""受入済みADC耐久ランナーを別案件用へ複製し、明示レンジ・保存先に対応する。"""
from pathlib import Path
import py_compile

ROOT=Path(__file__).resolve().parents[1]
LEGACY=ROOT/'docs/USB_Host_Reset_Study_20261121/Debug_20261125_01'
target=ROOT/'scripts/run_7355_r3_endurance_20261128.py'
source=(LEGACY/'run_cdc_endurance.py').read_text(encoding='utf-8')
def replace(old,new):
    global source
    assert old in source,old
    source=source.replace(old,new)
replace('from verify_host_after_flash import HOST_INFO, IDN, exchange',
        "ROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT/'docs/USB_Host_Reset_Study_20261121/Debug_20261125_01'))\nfrom verify_host_after_flash import HOST_INFO, IDN, exchange")
replace("str(Path(__file__).resolve().parents[3])","str(ROOT)")
replace("args = parser.parse_args()", "parser.add_argument('--ate-port', default='COM7')\n    parser.add_argument('--range-code', choices=('R3', 'R5'), default='R3')\n    parser.add_argument('--input-setpoint-mv', required=True)\n    parser.add_argument('--output-root', type=Path, default=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0')\n    args = parser.parse_args()")
replace("out = Path(__file__).with_name(f'endurance_{now:%Y%m%d_%H%M%S_%f}')", "out = args.output_root / f'endurance_{now:%Y%m%d_%H%M%S_%f}'")
replace("'ate_selected_range_mV': 200 if args.meter_language == 'scpi' else None", "'ate_selected_range_mV': 200 if args.range_code == 'R3' else 20000")
replace("'input_setpoint_mV': 40 if args.meter_language == 'scpi' else None", "'input_setpoint_mV': args.input_setpoint_mv")
replace("'ate_port': 'COM5'", "'ate_port': args.ate_port")
replace("serial.Serial('COM5',", "serial.Serial(args.ate_port,")
replace("'R?': 'R5'", "'R?': args.range_code")
replace("result['conf'] = 'ADC DCV R5 (20 V), continuous/immediate'", "result['conf'] = 'ADC DCV '+args.range_code+', continuous/immediate'")
with target.open('x',encoding='utf-8') as f:f.write(source)
py_compile.compile(str(target),doraise=True)
print(target)
