"""終了済みD0試験CSVを256byteずつ回収し、hash・通信・受信時間を検証する。"""
import csv
import hashlib
import io
import json
from pathlib import Path
import statistics
import sys
import time

import serial
from mpremote.transport_serial import SerialTransport


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from src.frame import parse_frame


def main():
    sequence = json.loads((OUT / "ate_sequence.json").read_text(encoding="utf-8"))
    assert sequence["completed"], "ATE sequence was not completed"
    report = dict(completed=False, files=[], normal_app_restarted=False)

    def save():
        (OUT / "csv_analysis.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    repl = SerialTransport("COM6", wait=2)
    try:
        repl.enter_raw_repl(soft_reset=False)
        assert repl.eval("__import__('binascii').hexlify(__import__('machine').unique_id()).decode()") == "69f7d45962cfdfad"
        report["runtime_d0_t2_ms"] = repl.eval("__import__('sys').modules['src.config'].T2_D0_MS")
        report["runtime_read_contract"] = repl.eval("__import__('sys').modules['src.nf55_command'].READ_REFRESH_COMMANDS['DATA_REFRESH']")
        assert report["runtime_d0_t2_ms"] == 300
        assert report["runtime_read_contract"] == ("D0", "DATA", 300, 327)
        raw, err = repl.exec_raw("""
import os, json, binascii, hashlib
_paths = []
for _bank in ('BANK_A', 'BANK_B'):
    for _name in os.listdir('/sd/' + _bank):
        if _name.endswith('.csv') and '_T' in _name:
            _paths.append('/sd/' + _bank + '/' + _name)
print(json.dumps(_paths))
""")
        assert not err, err
        paths = json.loads(raw.decode())
        report["sd_trial_paths"] = paths
        path = max(paths, key=lambda p: int(p.rsplit("_T", 1)[1][:-4]))
        assert Path(path).name[:15] >= sequence["rtc_before"], "Latest CSV predates this test"
        raw, err = repl.exec_raw("_data=open(" + repr(path) + ",'rb').read(); print(json.dumps({'size':len(_data),'sha256':binascii.hexlify(hashlib.sha256(_data).digest()).decode()}))")
        assert not err, err
        meta = json.loads(raw.decode())
        data = bytearray()
        for offset in range(0, meta["size"], 256):
            raw, err = repl.exec_raw("print(binascii.hexlify(_data[" + str(offset) + ":" + str(offset + 256) + "]).decode())")
            assert not err, err
            chunk = bytes.fromhex(raw.decode().strip())
            assert len(chunk) == min(256, meta["size"] - offset)
            data.extend(chunk)
        assert hashlib.sha256(data).hexdigest() == meta["sha256"]
        target = OUT / Path(path).name
        with target.open("xb") as stream:
            stream.write(data)
        rows = list(csv.DictReader(io.StringIO(data.decode())))
        column_counts = sorted(set(len(r) for r in csv.reader(io.StringIO(data.decode()))))
        assert column_counts == [14]
        starts = [r for r in rows if r["event"] == "TRIAL_START"]
        endings = [r for r in rows if r["event"] == "TRIAL_END_REQUEST"]
        assert len(starts) == len(endings) == 1
        trial_id = starts[0]["detail"].split("trial_id=")[1]
        assert path.endswith("_" + trial_id + ".csv")
        assert endings[0]["detail"] == "trial_id=" + trial_id + ";reason=TEST_END"
        frames = []
        transactions = []
        d0_timings = []
        pending = []
        for row in rows:
            if row["category"] == "NF55" and row["event"] == "RAW":
                raw = bytes.fromhex(row["raw_hex"])
                tick = int(row["detail"].split("ticks_ms=")[1])
                pending.append((row["direction"], raw, tick))
                if raw.startswith(b"\x02"):
                    frame = parse_frame(raw)
                    frames.append(dict(direction=row["direction"], cmd=frame.cmd,
                                       data_length=len(frame.data), bcc_ok=True, ticks_ms=tick))
            if row["category"] == "NF55" and row["event"] == "TRANSACTION":
                detail = dict(part.split("=", 1) for part in row["detail"].split(";"))
                tx = dict(cmd=row["cmd"], result=row["result"], command_retry=int(row["cmd_retry"]),
                          response_retry=int(row["rsp_retry"]), elapsed_ms=int(detail["elapsed_ms"]),
                          ambiguous=detail["ambiguous"])
                transactions.append(tx)
                assert tx["result"] == "OK" and tx["ambiguous"] == "False"
                assert tx["command_retry"] == tx["response_retry"] == 0
                if row["cmd"] == "D0":
                    assert len(pending) == 4, "Unexpected D0 raw sequence"
                    command, ack, response, final_ack = pending
                    assert command[0] == "TX" and parse_frame(command[1]).cmd == "D0"
                    assert ack[0] == "RX" and ack[1] == b"\x06"
                    frame = parse_frame(response[1])
                    assert response[0] == "RX" and frame.cmd == "D0" and len(frame.data) == 327
                    assert final_ack[0] == "TX" and final_ack[1] == b"\x06"
                    timing = dict(sample_number=len(d0_timings) + 1,
                                  command_to_ack_ms=ack[2] - command[2],
                                  ack_to_full_response_ms=response[2] - ack[2],
                                  response_to_final_ack_ms=final_ack[2] - response[2],
                                  transaction_elapsed_ms=tx["elapsed_ms"])
                    assert 0 <= timing["ack_to_full_response_ms"] <= 300
                    d0_timings.append(timing)
                pending = []
        assert [t["cmd"] for t in transactions] == ["D1", "D5"] + ["D0"] * 10
        assert len(frames) == 24
        assert all(f["data_length"] == 327 for f in frames if f["cmd"] == "D0" and f["direction"] == "RX")
        values = [t["ack_to_full_response_ms"] for t in d0_timings]
        tx_values = [t["transaction_elapsed_ms"] for t in d0_timings]
        report.update(files=[dict(sd_path=path, local=target.name, size=len(data),
                                  sha256=meta["sha256"], sd_pc_hash_match=True, trial_id=trial_id,
                                  data_rows=len(rows), column_counts=column_counts)],
                      frames=frames, transactions=transactions, d0_timings=d0_timings,
                      d0_summary=dict(count=len(values), ack_to_full_response_min_ms=min(values),
                                      ack_to_full_response_max_ms=max(values),
                                      ack_to_full_response_mean_ms=statistics.mean(values),
                                      observed_margin_to_300ms_min_ms=300-max(values),
                                      transaction_min_ms=min(tx_values), transaction_max_ms=max(tx_values)),
                      ate_min_start_gap_ms=min((b["sent_elapsed_s"]-a["sent_elapsed_s"])*1000
                                               for a,b in zip(sequence["commands"],sequence["commands"][1:])))
        report["completed"] = True
    except Exception as exc:
        report["error"] = repr(exc)
        raise
    finally:
        save()
        repl.exit_raw_repl()
        repl.serial.write(b"\x04")
        time.sleep(2)
        repl.close()

    with serial.Serial("COM20",115200,timeout=2,write_timeout=2) as port:
        for command in ("*IDN?","COMM_STATUS?","SD_STATUS?","PICO_SELF_CHECK?","LOG_DROP_COUNT?"):
            time.sleep(0.15)
            port.write((command + "\r\n").encode())
            raw = port.read_until(b"\n")
            answer = raw.decode("ascii").rstrip("\r\n")
            report.setdefault("after_restart",[]).append(dict(command=command,response=answer,raw_hex=raw.hex()))
            save()
            assert raw.endswith(b"\r\n")
            if command == "*IDN?":
                assert answer.startswith("NF55G_PICO_FIXTURE,")
            elif command == "COMM_STATUS?":
                assert answer == "OK:state=IDLE"
            elif command == "PICO_SELF_CHECK?":
                assert answer.startswith("OK:")
            elif command == "LOG_DROP_COUNT?":
                assert answer == "0"
            else:
                assert answer == "OK"
            print(command,"=>",answer,flush=True)
    report["normal_app_restarted"] = True
    save()
    print(json.dumps(report["d0_summary"],indent=2),flush=True)
    print("Verified CSV:",report["files"],flush=True)


if __name__ == "__main__":
    main()
