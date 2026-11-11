"""D1/D2/D3/D5を各10回、既存のT2・再送・Cache契約のままATE経路で測定する。"""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import time
import serial

OUT = Path(__file__).resolve().parent
JST = timezone(timedelta(hours=9))


def main():
    evidence = dict(started_jst=datetime.now(JST).isoformat(), commands=[], completed=False,
                    note="D4 is measured separately without automatic command retry or cache validation")
    started = time.perf_counter()
    def save():
        (OUT / "ate_sequence.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    with serial.Serial("COM20",115200,timeout=0.1,write_timeout=2) as port:
        def query(command):
            time.sleep(0.15)
            sent = time.perf_counter()
            row = dict(command=command,sent_jst=datetime.now(JST).isoformat(),sent_s=sent-started)
            evidence["commands"].append(row)
            port.write((command+"\r\n").encode("ascii")); port.flush()
            data=bytearray()
            while time.perf_counter()-sent<3:
                data.extend(port.read(1))
                if data.endswith(b"\n"): break
            answer=bytes(data).decode("ascii",errors="backslashreplace").rstrip("\r\n")
            row.update(response=answer,raw_hex=data.hex(),response_ms=(time.perf_counter()-sent)*1000)
            save()
            print(command,"=>",answer,flush=True)
            assert data.endswith(b"\r\n"),"ATE timeout; do not resend automatically"
            return answer
        recording=False
        try:
            assert query("*IDN?").startswith("NF55G_PICO_FIXTURE,")
            assert query("COMM_STATUS?")=="OK:state=IDLE"
            assert query("SD_STATUS?")=="OK"
            assert query("PICO_SELF_CHECK?").startswith("OK:")
            assert query("LOG_DROP_COUNT?")=="0"
            evidence["rtc_before"]=query("RTC_DATETIME?")
            assert query("TEST_START")=="OK"; recording=True
            for number in range(1,11):
                assert query("STATUS_REFRESH")=="OK"
                evidence["commands"][-1]["sample_number"]=number
            evidence["ps_on"]=query("PS_ON?")
            evidence["batt_on"]=query("BATT_ON?")
            evidence["restart_ready"]=query("RESTART_READY?")
            assert evidence["ps_on"]=="1" and evidence["batt_on"]=="0"
            # D2の受付に必要なSCを、送信時点の日本時間で1回だけ明示実行する。
            assert query("CLOCK_SYNC "+datetime.now(JST).strftime("%y%m%d%H%M%S"))=="OK"
            for command in ("D2_REFRESH","D3_REFRESH","INFO_REFRESH"):
                for number in range(1,11):
                    assert query(command)=="OK",command+" failed; stop subsequent product commands"
                    evidence["commands"][-1]["sample_number"]=number
                assert query("LOG_DROP_COUNT?")=="0"
            evidence["fw_rev"]=query("FW_REV?")
            assert query("TEST_END")=="OK"; recording=False
            for command in ("PICO_SELF_CHECK?","SD_STATUS?","LOG_DROP_COUNT?","COMM_STATUS?"):
                answer=query(command)
                if command=="PICO_SELF_CHECK?": assert answer.startswith("OK:") and "TEST_LOGGER=OK" in answer
                elif command=="LOG_DROP_COUNT?": assert answer=="0"
                elif command=="COMM_STATUS?": assert answer=="OK:state=IDLE"
                else: assert answer=="OK"
            evidence["completed"]=True
        except Exception as exc:
            evidence["error"]=repr(exc)
            if recording:
                try:
                    if query("COMM_STATUS?")=="OK:state=IDLE": evidence["cleanup_test_end"]=query("TEST_END")
                except Exception as cleanup: evidence["cleanup_error"]=repr(cleanup)
            raise
        finally:
            evidence["finished_jst"]=datetime.now(JST).isoformat(); save()


if __name__=="__main__": main()
