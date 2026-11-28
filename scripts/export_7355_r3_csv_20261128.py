"""現案件の耐久CSVを既存照合処理で回収し、必ず元の常駐処理を再開する。"""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
LEGACY=ROOT/'docs/USB_Host_Reset_Study_20261121/Debug_20261125_01'
p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args()
assert args.run.replace('_','').isalnum()
out=CASE/args.run;assert out.is_dir()
source=(LEGACY/'export_endurance_csv.py').read_text(encoding='utf-8')
assert 'timeout=300)' in source
source=source.replace('timeout=300)','timeout=900)')
sys.path.insert(0,str(LEGACY))
namespace={'__name__':'r3_csv_export_driver','__file__':str(LEGACY/'export_endurance_csv.py')}
exec(compile(source,str(LEGACY/'export_endurance_csv.py'),'exec'),namespace)
try:
    namespace['main'](out)
finally:
    subprocess.run(namespace['BASE']+['exec','--no-follow',"import sys;sys.modules['src.main'].active_app.run()"],cwd=ROOT,timeout=30,check=True)
