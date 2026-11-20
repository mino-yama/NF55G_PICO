"""親単独USBで起動ログとcreate_fixture_appの実初期化を確認する診断。"""
from pathlib import Path
import os
import json
import time
from mpremote.transport_serial import SerialTransport

BASE=Path(__file__).resolve().parent
PREFIX=chr(92)*2+'?'+chr(92)
OUT=Path(PREFIX+str(BASE)) if os.name=='nt' and not str(BASE).startswith(PREFIX) else BASE


def main():
    if (OUT/'Startup_Result.json').exists():
        raise RuntimeError('Preserve previous investigation')
    result={'port':'COM6','expected_unique_id':'69f7d45962cfdfad','date_jst':'2026-11-20',
            'firmware_files_written':False,'normal_main_started':False,'queries_sent':False}
    transport=SerialTransport('COM6',wait=2)
    try:
        time.sleep(.2)
        startup=transport.serial.read(transport.serial.in_waiting or 0)
        (OUT/'passive_startup.raw').write_bytes(startup)
        transport.enter_raw_repl(soft_reset=False)
        uid=transport.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()")
        if uid!=result['expected_unique_id']:
            raise RuntimeError('Wrong parent')
        result['unique_id']=uid
        stdout,stderr=transport.exec_raw("import sys,rp2; print('VERSION='+sys.version); print('SM4_BEFORE_RESET='+str(rp2.StateMachine(4).active())); print('SM5_BEFORE_RESET='+str(rp2.StateMachine(5).active()))")
        (OUT/'Before_Raw_Reset.log').write_bytes(stdout+b'\nSTDERR\n'+stderr)
        transport.enter_raw_repl(soft_reset=True)
        code="""
import sys,rp2
print('FACTORY_DIAGNOSTIC_BEGIN')
try:
 from src.main import create_fixture_app
 print('IMPORT_OK')
 _startup_app=create_fixture_app(enable_hardware=True)
 print('FACTORY_OK')
 print('EXTERNAL_ERROR='+repr(_startup_app.external_error))
 print('EXTERNAL_LINK_PRESENT='+str(_startup_app.external_link is not None))
 print('ATE_UART='+repr(_startup_app.ate_uart.uart))
 import src.main as _startup_module
 print('SD_DIAGNOSTIC='+repr(_startup_module.startup_sd_diagnostic))
 print('SM4_ACTIVE='+str(rp2.StateMachine(4).active()))
 print('SM5_ACTIVE='+str(rp2.StateMachine(5).active()))
except Exception as error:
 print('FACTORY_FAILED')
 sys.print_exception(error)
print('FACTORY_DIAGNOSTIC_END')
"""
        stdout,stderr=transport.exec_raw(code,timeout=30)
        (OUT/'Factory_Diagnostic.log').write_bytes(stdout+b'\nSTDERR\n'+stderr)
        result['factory_stdout']=stdout.decode()
        result['factory_stderr']=stderr.decode()
        result['factory_ok']=b'FACTORY_OK' in stdout and not stderr
        print(stdout.decode(),flush=True)
        if stderr:
            print(stderr.decode(),flush=True)
        # 通信ループを実行せず、初期化したGPIO/UARTもraw soft resetで終了する。
        transport.enter_raw_repl(soft_reset=True)
        result['final_state']='raw soft reset; then friendly REPL stopped'
    finally:
        (OUT/'Startup_Result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        transport.exit_raw_repl()
        transport.close()


if __name__=='__main__':
    main()
