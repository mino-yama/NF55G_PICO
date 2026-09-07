"""Run Pico 2 DS3231 RTC HIL checks through a MicroPython REPL."""

from __future__ import annotations

import argparse
import pathlib
import sys
import time

import serial


ROOT = pathlib.Path(__file__).resolve().parents[1]
RTC_SOURCE = ROOT / "src" / "rtc_driver.py"


MICROPYTHON_TEST = r'''
import os
import sys
import time
from machine import I2C, Pin


rtc_source = __RTC_SOURCE__
ns = globals()
exec(rtc_source, ns)


print("CODEX_RTC_HIL_BEGIN")
try:
    print("micropython_identity|PASS|{}; {}; {}".format(sys.implementation.name, sys.platform, os.uname().machine))
    i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=100000)
    scan = i2c.scan()
    print("i2c0_gp20_gp21_scan|{}|{}".format("PASS" if 0x68 in scan else "FAIL", repr(["0x{:02x}".format(x) for x in scan])))
    device = DS3231I2CDevice(i2c=i2c)
    check = device.check()
    print("ds3231_check|{}|{}".format("PASS" if check else "FAIL", check))
    before = device.read_datetime()
    status = device.read_status()
    print("ds3231_read_datetime|PASS|{}, status=0x{:02x}".format(before.datetime(), status))
except Exception as exc:
    print("EXCEPTION|FAIL|{}: {}".format(type(exc).__name__, exc))
print("CODEX_RTC_HIL_END")
'''


def read_available(port: serial.Serial, seconds: float) -> bytes:
    end = time.time() + seconds
    chunks = []
    while time.time() < end:
        data = port.read(port.in_waiting or 1)
        if data:
            chunks.append(data)
        else:
            time.sleep(0.05)
    return b"".join(chunks)


def run(port_name: str, baudrate: int) -> int:
    source = RTC_SOURCE.read_text(encoding="utf-8")
    payload = MICROPYTHON_TEST.replace("__RTC_SOURCE__", repr(source))
    with serial.Serial(port_name, baudrate=baudrate, timeout=0.2, write_timeout=5) as port:
        port.write(b"\x03\x03")
        read_available(port, 0.5)
        port.write(b"\x01")
        read_available(port, 0.5)
        port.write(("exec(" + repr(payload) + ")\r\n").encode("utf-8"))
        port.write(b"\x04")
        output = read_available(port, 15)
    text = output.decode("utf-8", errors="replace")
    print(text)
    if "CODEX_RTC_HIL_BEGIN" not in text or "CODEX_RTC_HIL_END" not in text:
        print("Missing RTC HIL result markers", file=sys.stderr)
        return 2
    if "|FAIL|" in text or "EXCEPTION|FAIL|" in text:
        return 1
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run Pico RTC HIL checks over MicroPython REPL.")
    parser.add_argument("--port", default="COM14", help="Serial port, e.g. COM14")
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args(argv)
    return run(args.port, args.baudrate)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
