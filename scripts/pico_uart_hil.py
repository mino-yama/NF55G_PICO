"""Run Pico 2 UART/RS232C loopback HIL checks through a MicroPython REPL.

This script is a debug aid, not fixture firmware. It verifies the planned
Pico-2CH-RS232 channels without sending any NF55G command to a product.
"""

from __future__ import annotations

import argparse
import sys
import time

import serial


MICROPYTHON_TEST = r'''
import os
import sys
import time
from machine import Pin, UART


def drain(uart, duration_ms=100):
    end = time.ticks_add(time.ticks_ms(), duration_ms)
    data = b""
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        n = uart.any()
        if n:
            data += uart.read(n)
        time.sleep_ms(2)
    return data


def read_exact(uart, expected_len, timeout_ms=1000):
    end = time.ticks_add(time.ticks_ms(), timeout_ms)
    data = b""
    while len(data) < expected_len and time.ticks_diff(end, time.ticks_ms()) > 0:
        n = uart.any()
        if n:
            data += uart.read(n)
        time.sleep_ms(1)
    return data


def make_pattern(label, repeat):
    base = (label + ":0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\r\n").encode()
    return (base * repeat)[:__BYTES__]


def init_uart0():
    return UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))


def init_uart1():
    return UART(1, baudrate=38400, bits=8, parity=0, stop=1, tx=Pin(4), rx=Pin(5))


def loopback_check(name, uart, peer_uart, pattern, timeout_ms):
    drain(uart, 100)
    drain(peer_uart, 100)
    uart.write(pattern)
    received = read_exact(uart, len(pattern), timeout_ms)
    crosstalk = drain(peer_uart, 200)
    ok = received == pattern and len(crosstalk) == 0
    detail = "tx={}, rx={}, mismatch={}, crosstalk={}".format(
        len(pattern),
        len(received),
        0 if received == pattern else 1,
        len(crosstalk),
    )
    return (name, "PASS" if ok else "FAIL", detail)


def run_checks():
    results = []
    info = "{}; {}; {}".format(sys.implementation.name, sys.platform, os.uname().machine)
    results.append(("micropython_identity", "PASS", info))

    try:
        uart0 = init_uart0()
        results.append(("uart0_init_115200_8n1", "PASS", "GP0=TX, GP1=RX"))
    except Exception as exc:
        results.append(("uart0_init_115200_8n1", "FAIL", "{}: {}".format(type(exc).__name__, exc)))
        return results

    try:
        uart1 = init_uart1()
        results.append(("uart1_init_38400_8e1", "PASS", "GP4=TX, GP5=RX"))
    except Exception as exc:
        results.append(("uart1_init_38400_8e1", "FAIL", "{}: {}".format(type(exc).__name__, exc)))
        return results

    p0 = make_pattern("UART0_CH0", 64)
    p1 = make_pattern("UART1_CH1", 64)
    results.append(loopback_check("uart0_ch0_loopback", uart0, uart1, p0, 1000))
    results.append(loopback_check("uart1_ch1_loopback", uart1, uart0, p1, 2000))

    stress_ok = True
    tx_total0 = 0
    tx_total1 = 0
    failures = []
    for i in range(__FRAMES__):
        p0i = ("CH0#{:04d}:{}\r\n".format(i, "A" * 24)).encode()
        p1i = ("CH1#{:04d}:{}\r\n".format(i, "B" * 24)).encode()
        r0 = loopback_check("uart0_stress_frame", uart0, uart1, p0i, 500)
        r1 = loopback_check("uart1_stress_frame", uart1, uart0, p1i, 800)
        if r0[1] != "PASS" or r1[1] != "PASS":
            stress_ok = False
            failures.append("frame={}, ch0={}, ch1={}".format(i, r0[2], r1[2]))
            break
        tx_total0 += len(p0i)
        tx_total1 += len(p1i)
        if (i + 1) % 10 == 0:
            print("stress_progress|INFO|frames_done={}".format(i + 1))
            try:
                sys.stdout.flush()
            except Exception:
                pass
    if failures:
        results.append(("stress_first_failure", "FAIL", failures[0]))
    results.append(("dual_channel_stress", "PASS" if stress_ok else "FAIL", "frames={}, ch0_bytes={}, ch1_bytes={}".format(__FRAMES__ if stress_ok else i, tx_total0, tx_total1)))

    try:
        uart0.deinit()
    except Exception:
        pass
    try:
        uart1.deinit()
    except Exception:
        pass
    return results


print("CODEX_UART_HIL_BEGIN")
try:
    for name, result, detail in run_checks():
        print("{}|{}|{}".format(name, result, detail))
        try:
            sys.stdout.flush()
        except Exception:
            pass
except Exception as exc:
    print("EXCEPTION|FAIL|{}: {}".format(type(exc).__name__, exc))
print("CODEX_UART_HIL_END")
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


def read_until_marker(port: serial.Serial, marker: bytes, seconds: float) -> bytes:
    end = time.time() + seconds
    data = b""
    while time.time() < end:
        chunk = port.read(port.in_waiting or 1)
        if chunk:
            data += chunk
            if marker in data:
                time.sleep(0.2)
                data += port.read(port.in_waiting or 1)
                return data
        else:
            time.sleep(0.05)
    return data


def build_payload(byte_count: int, frames: int) -> str:
    payload = MICROPYTHON_TEST.replace("__BYTES__", str(int(byte_count)))
    return payload.replace("__FRAMES__", str(int(frames)))


def run(port_name: str, baudrate: int, byte_count: int, frames: int) -> int:
    payload = build_payload(byte_count, frames)
    with serial.Serial(port_name, baudrate=baudrate, timeout=0.2, write_timeout=5) as port:
        port.write(b"\x03\x03")
        read_available(port, 0.5)
        port.write(b"\x01")
        read_available(port, 0.5)
        port.write(("exec(" + repr(payload) + ")\r\n").encode("utf-8"))
        port.write(b"\x04")
        output = read_until_marker(port, b"CODEX_UART_HIL_END", max(40, frames * 2 + 20))
    text = output.decode("utf-8", errors="replace")
    print(text)
    if "CODEX_UART_HIL_BEGIN" not in text or "CODEX_UART_HIL_END" not in text:
        print("Missing UART HIL result markers", file=sys.stderr)
        return 2
    if "|FAIL|" in text or "EXCEPTION|FAIL|" in text:
        return 1
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run Pico UART/RS232C loopback HIL checks over MicroPython REPL.")
    parser.add_argument("--port", default="COM14", help="Serial port, e.g. COM14")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--bytes", type=int, default=256, help="Bytes per initial channel pattern")
    parser.add_argument("--frames", type=int, default=100, help="Stress frames per channel")
    args = parser.parse_args(argv)
    return run(args.port, args.baudrate, args.bytes, args.frames)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
