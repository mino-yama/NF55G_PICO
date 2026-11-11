"""配置済みD0 T2=300msの正常系10回をATE経路で確認し、送受信を保存する。"""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import time

import serial


OUT = Path(__file__).resolve().parent
JST = timezone(timedelta(hours=9))


def main():
    evidence = dict(started_jst=datetime.now(JST).isoformat(), port="COM20",
                    baudrate=115200, commands=[], completed=False,
                    scope="D1/D5 read, D0 ten times; no SC/SET/CLEAR/FU")
    start_time = time.perf_counter()

    def save():
        (OUT / "ate_sequence.json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

    with serial.Serial("COM20", 115200, timeout=0.1, write_timeout=2) as port:
        def query(command):
            time.sleep(0.15)
            sent = time.perf_counter()
            row = dict(command=command, sent_jst=datetime.now(JST).isoformat(),
                       sent_elapsed_s=sent - start_time)
            evidence["commands"].append(row)
            port.write((command + "\r\n").encode("ascii"))
            port.flush()
            raw = bytearray()
            deadline = sent + 3
            while time.perf_counter() < deadline:
                raw.extend(port.read(1))
                if raw.endswith(b"\n"):
                    break
            row.update(response=bytes(raw).decode("ascii", errors="backslashreplace").rstrip("\r\n"),
                       raw_hex=raw.hex(), received_elapsed_s=time.perf_counter() - start_time,
                       response_ms=(time.perf_counter() - sent) * 1000)
            save()
            print(command, "=>", row["response"], flush=True)
            if not raw.endswith(b"\r\n"):
                raise RuntimeError("ATE response timeout; no automatic ATE retry")
            return row["response"]

        recording = False
        try:
            assert query("*IDN?").startswith("NF55G_PICO_FIXTURE,")
            assert query("COMM_STATUS?") == "OK:state=IDLE"
            assert query("SD_STATUS?") == "OK"
            evidence["rtc_before"] = query("RTC_DATETIME?")
            assert query("LOG_DROP_COUNT?") == "0"
            assert query("TEST_START") == "OK"
            recording = True
            assert query("VOUT12?") == "ERR:CACHE_INVALID"
            assert query("STATUS_REFRESH") == "OK"
            evidence["ps_on"] = query("PS_ON?")
            evidence["batt_on"] = query("BATT_ON?")
            assert query("INFO_REFRESH") == "OK"
            evidence["product_fw"] = query("FW_REV?")
            for number in range(1, 11):
                assert query("DATA_REFRESH") == "OK", "D0 failed; stop product commands"
                evidence["commands"][-1]["sample_number"] = number
                for command in ("NF55_DATETIME?", "VOUT12?", "IOUT12?", "BATT_VOLT?"):
                    assert not query(command).startswith("ERR:"), "DATA query failed"
                assert query("LOG_DROP_COUNT?") == "0"
            # D0内のStatus/INFOを各Cacheへ昇格させていないことはCSVとも照合する。
            assert query("FW_REV?") == evidence["product_fw"]
            assert query("TEST_END") == "OK"
            recording = False
            for command in ("PICO_SELF_CHECK?", "SD_STATUS?", "LOG_DROP_COUNT?", "COMM_STATUS?"):
                answer = query(command)
                if command == "PICO_SELF_CHECK?":
                    assert answer.startswith("OK:") and "TEST_LOGGER=OK" in answer
                elif command == "LOG_DROP_COUNT?":
                    assert answer == "0"
                elif command == "COMM_STATUS?":
                    assert answer == "OK:state=IDLE"
                else:
                    assert answer == "OK"
            evidence["completed"] = True
        except Exception as exc:
            evidence["error"] = repr(exc)
            if recording:
                # 製品への追加操作はせず、待機確認後に試験ログだけを閉じる。
                try:
                    if query("COMM_STATUS?") == "OK:state=IDLE":
                        evidence["cleanup_test_end"] = query("TEST_END")
                except Exception as cleanup:
                    evidence["cleanup_error"] = repr(cleanup)
            raise
        finally:
            evidence["finished_jst"] = datetime.now(JST).isoformat()
            save()


if __name__ == "__main__":
    main()
