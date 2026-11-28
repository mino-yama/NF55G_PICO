"""既知HOSTだけに入力／戻り診断候補を一時配置し、全Flash復元も同じ手順で行う。"""
from pathlib import Path
base=Path(__file__).with_name('flash_meter_uart_diag_20261128.py')
code=base.read_text(encoding='utf-8')
assert "OUT=CASE/'uart_diagnostic'" in code
code=code.replace("OUT=CASE/'uart_diagnostic'","OUT=CASE/'uart_diagnostic_v2'")
code=code.replace('uartdiag-20261128.1','uartdiag-20261128.2')
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
