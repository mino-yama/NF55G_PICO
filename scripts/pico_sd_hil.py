"""Run Pico 2 microSD HIL checks through a MicroPython REPL.

This script is intentionally a debug aid, not fixture firmware. It uploads a
temporary SD block driver and executes non-NF55G SD checks on the connected
Pico MicroPython REPL.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import textwrap
import time

import serial


ROOT = pathlib.Path(__file__).resolve().parents[1]
LOGGER_SOURCE = ROOT / "src" / "logger.py"


MICROPYTHON_TEST = r'''
import os
import sys
import time
from machine import Pin, SPI


class SDCard:
    CMD_TIMEOUT = 100
    R1_IDLE_STATE = 1
    R1_ILLEGAL_COMMAND = 4
    TOKEN_CMD25 = 0xfc
    TOKEN_STOP_TRAN = 0xfd
    TOKEN_DATA = 0xfe

    def __init__(self, spi, cs, baudrate=1320000):
        self.spi = spi
        self.cs = cs
        self.cmdbuf = bytearray(6)
        self.dummybuf = bytearray(512)
        self.tokenbuf = bytearray(1)
        self.cs.init(self.cs.OUT, value=1)
        self.init_spi(baudrate)
        for _ in range(16):
            self.spi.write(b"\xff")
        r = self.cmd(0, 0, 0x95)
        if r != self.R1_IDLE_STATE:
            raise OSError("CMD0 failed: {}".format(r))
        r = self.cmd(8, 0x01AA, 0x87, 4)
        if r == self.R1_IDLE_STATE:
            self.init_card_v2()
        elif r == (self.R1_IDLE_STATE | self.R1_ILLEGAL_COMMAND):
            self.init_card_v1()
        else:
            raise OSError("unsupported SD card")
        self.cmd(16, 512, 0x15)
        self.init_spi(25000000)

    def init_spi(self, baudrate):
        self.spi.init(baudrate=baudrate, phase=0, polarity=0)

    def init_card_v1(self):
        for _ in range(self.CMD_TIMEOUT):
            self.cmd(55, 0, 0)
            if self.cmd(41, 0, 0) == 0:
                self.cdv = 512
                return
        raise OSError("timeout waiting for v1 card")

    def init_card_v2(self):
        for _ in range(self.CMD_TIMEOUT):
            time.sleep_ms(50)
            self.cmd(58, 0, 0, 4)
            self.cmd(55, 0, 0)
            if self.cmd(41, 0x40000000, 0) == 0:
                self.cmd(58, 0, 0, 4)
                self.cdv = 1
                return
        raise OSError("timeout waiting for v2 card")

    def cmd(self, cmd, arg, crc, final=0, release=True, skip1=False):
        self.cs(0)
        self.cmdbuf[0] = 0x40 | cmd
        self.cmdbuf[1] = (arg >> 24) & 0xff
        self.cmdbuf[2] = (arg >> 16) & 0xff
        self.cmdbuf[3] = (arg >> 8) & 0xff
        self.cmdbuf[4] = arg & 0xff
        self.cmdbuf[5] = crc
        self.spi.write(b"\xff")
        self.spi.write(self.cmdbuf)
        if skip1:
            self.spi.readinto(self.tokenbuf, 0xff)
        for _ in range(self.CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xff)
            response = self.tokenbuf[0]
            if not (response & 0x80):
                for _ in range(final):
                    self.spi.readinto(self.tokenbuf, 0xff)
                if release:
                    self.cs(1)
                    self.spi.write(b"\xff")
                return response
        self.cs(1)
        self.spi.write(b"\xff")
        return -1

    def readinto(self, buf):
        self.cs(0)
        for _ in range(self.CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xff)
            if self.tokenbuf[0] == self.TOKEN_DATA:
                break
        else:
            self.cs(1)
            raise OSError("timeout waiting for data token")
        self.spi.readinto(buf, 0xff)
        self.spi.write(b"\xff\xff")
        self.cs(1)
        self.spi.write(b"\xff")

    def write(self, token, buf):
        self.cs(0)
        self.spi.write(bytes([token]))
        self.spi.write(buf)
        self.spi.write(b"\xff\xff")
        if (self.spi.read(1, 0xff)[0] & 0x1f) != 0x05:
            self.cs(1)
            raise OSError("write rejected")
        while self.spi.read(1, 0xff)[0] == 0:
            pass
        self.cs(1)
        self.spi.write(b"\xff")

    def readblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        assert nblocks and not len(buf) % 512
        if nblocks == 1:
            if self.cmd(17, block_num * self.cdv, 0, release=False) != 0:
                raise OSError("read failed")
            self.readinto(buf)
        else:
            if self.cmd(18, block_num * self.cdv, 0, release=False) != 0:
                raise OSError("multi-read failed")
            offset = 0
            while nblocks:
                self.readinto(memoryview(buf)[offset : offset + 512])
                offset += 512
                nblocks -= 1
            self.cmd(12, 0, 0xff, skip1=True)

    def writeblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        assert nblocks and not len(buf) % 512
        if nblocks == 1:
            if self.cmd(24, block_num * self.cdv, 0) != 0:
                raise OSError("write setup failed")
            self.write(self.TOKEN_DATA, buf)
        else:
            if self.cmd(25, block_num * self.cdv, 0) != 0:
                raise OSError("multi-write setup failed")
            offset = 0
            while nblocks:
                self.write(self.TOKEN_CMD25, memoryview(buf)[offset : offset + 512])
                offset += 512
                nblocks -= 1
            self.write(self.TOKEN_STOP_TRAN, b"")

    def ioctl(self, op, arg):
        if op == 4:
            return 0
        if op == 5:
            return 0
        if op == 6:
            return 512
        return 0


class PicoClock:
    def ticks_ms(self):
        return time.ticks_ms()


class PicoSDSink:
    def __init__(self, mount_point="/sd"):
        self.mount_point = mount_point
        self.status = "OK"
        self.open_filename = None
        self.file = None
        self.write_count = 0
        self.flush_count = 0
        self.close_count = 0
        self.reinit_count = 0
        self.capacity_bytes = 0

    def mount(self):
        try:
            os.umount(self.mount_point)
        except Exception:
            pass
        spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
        self.sd = SDCard(spi, Pin(17))
        try:
            vfs = os.VfsFat(self.sd)
            os.mount(vfs, self.mount_point)
        except AttributeError:
            os.mount(self.sd, self.mount_point)
        self.status = "OK"

    def open(self, filename):
        if self.status != "OK":
            raise LoggerError(self.status)
        if not filename.startswith("/"):
            filename = self.mount_point + "/" + filename
        self.open_filename = filename
        self.file = open(filename, "w")
        self.file.write(",".join(CSV_FIELDS) + "\n")

    def write_record(self, row):
        if self.status != "OK":
            raise LoggerError(self.status)
        if self.file is None:
            raise LoggerError("OPEN_ERR")
        self.file.write(",".join(row) + "\n")
        self.write_count += 1

    def flush(self):
        if self.status != "OK":
            raise LoggerError(self.status)
        if self.file is None:
            raise LoggerError("OPEN_ERR")
        self.file.flush()
        self.flush_count += 1

    def close(self):
        if self.file is not None:
            self.file.close()
            self.close_count += 1
        self.file = None

    def reinit(self):
        self.close()
        self.mount()
        self.reinit_count += 1

    def usage(self):
        return {"used_bytes": 0, "capacity_bytes": self.capacity_bytes, "used_percent": 0.0}


def remove_if_exists(path):
    try:
        os.remove(path)
    except OSError:
        pass


def run_checks():
    results = []
    sink = PicoSDSink()
    sink.mount()
    results.append(("mount", "PASS", repr(os.listdir("/sd"))))

    path = "/sd/CODEX_SD_HIL.CSV"
    remove_if_exists(path)
    f = open(path, "w")
    f.write("seq,value\n")
    f.write("1,abc\n")
    f.flush()
    f.close()
    data = open(path, "r").read()
    results.append(("csv_create_write_flush_close_readback", "PASS" if data == "seq,value\n1,abc\n" else "FAIL", repr(data)))
    remove_if_exists(path)

    logger_source = __LOGGER_SOURCE__
    ns = globals()
    exec(logger_source, ns)
    logger = ns["Logger"](sd_sink=sink, clock=PicoClock(), queue_limit=512, flush_interval_ms=1000, flush_record_count=32)
    ok_start = logger.test_start()
    record_count = __RECORD_COUNT__
    for i in range(record_count):
        logger.log(category="CONT", event="SAMPLE", result="OK", detail=i)
        logger.service(protocol_busy=(i % 17 == 0))
    time.sleep_ms(1100)
    logger.service(protocol_busy=False)
    ok_end = logger.test_end()
    log_path = sink.open_filename or ""
    # test_end clears current_filename, so derive from the last open path before close count.
    # PicoSDSink keeps open_filename after close to support readback in this HIL script.
    lines = open(log_path, "r").read().splitlines()
    expected_rows = 1 + record_count
    queue_ok = ok_start and ok_end and len(lines) == expected_rows and logger.drop_count == 0
    detail = "lines={}, writes={}, flushes={}, closes={}, drops={}".format(len(lines), sink.write_count, sink.flush_count, sink.close_count, logger.drop_count)
    results.append(("logger_queue_flush_close_readback", "PASS" if queue_ok else "FAIL", detail))
    remove_if_exists(log_path)

    sink.reinit()
    results.append(("sd_reinit_after_clean_cycle", "PASS" if sink.status == "OK" and sink.reinit_count == 1 else "FAIL", "status={}".format(sink.status)))
    os.umount("/sd")
    return results


def run_mount_probe():
    try:
        sink = PicoSDSink()
        sink.mount()
        listing = repr(os.listdir("/sd"))
        os.umount("/sd")
        return [("mount_probe", "PASS", listing)]
    except Exception as exc:
        return [("mount_probe", "FAIL", "{}: {}".format(type(exc).__name__, exc))]


def run_write_error_probe():
    results = []
    sink = PicoSDSink()
    sink.mount()
    path = "/sd/CODEX_WRERR.CSV"
    remove_if_exists(path)
    logger_source = __LOGGER_SOURCE__
    ns = globals()
    exec(logger_source, ns)
    logger = ns["Logger"](sd_sink=sink, clock=PicoClock(), queue_limit=8, flush_interval_ms=0, flush_record_count=1)
    ok_start = logger.test_start()
    logger.log(category="WRERR", event="AFTER_REMOVAL", result="EXPECT_ERROR")
    written = logger.force_drain()
    status = logger.status()
    close_ok = True
    try:
        logger.test_end()
    except Exception as exc:
        close_ok = False
        results.append(("write_error_close_exception", "PASS", "{}: {}".format(type(exc).__name__, exc)))
    detected = (not ok_start) or status != "OK" or written == 0
    detail = "start={}, written={}, status={}, drops={}, close_ok={}".format(ok_start, written, status, logger.drop_count, close_ok)
    results.append(("write_error_after_removal", "PASS" if detected else "FAIL", detail))
    return results


def run_delayed_write_error_probe():
    results = []
    sink = PicoSDSink()
    sink.mount()
    logger_source = __LOGGER_SOURCE__
    ns = globals()
    exec(logger_source, ns)
    logger = ns["Logger"](sd_sink=sink, clock=PicoClock(), queue_limit=8, flush_interval_ms=0, flush_record_count=1)
    ok_start = logger.test_start()
    print("CODEX_REMOVE_CARD_NOW")
    time.sleep_ms(__DELAY_MS__)
    written = 0
    for i in range(256):
        logger.log(category="WRERR", event="AFTER_REMOVAL", result="EXPECT_ERROR", detail=("X" * 96) + str(i))
        written += logger.force_drain()
        if logger.status() != "OK":
            break
    status = logger.status()
    close_ok = True
    try:
        sink.close()
    except Exception as exc:
        close_ok = False
        results.append(("write_error_close_exception", "PASS", "{}: {}".format(type(exc).__name__, exc)))
    detected = ok_start and status != "OK"
    detail = "start={}, written={}, status={}, drops={}, close_ok={}".format(ok_start, written, status, logger.drop_count, close_ok)
    results.append(("write_error_during_open_file", "PASS" if detected else "FAIL", detail))
    return results


print("CODEX_SD_HIL_BEGIN")
try:
    if "__MODE__" == "probe":
        rows = run_mount_probe()
    elif "__MODE__" == "write_error":
        rows = run_write_error_probe()
    elif "__MODE__" == "delayed_write_error":
        rows = run_delayed_write_error_probe()
    else:
        rows = run_checks()
    for name, result, detail in rows:
        print("{}|{}|{}".format(name, result, detail))
except Exception as exc:
    print("EXCEPTION|FAIL|{}: {}".format(type(exc).__name__, exc))
print("CODEX_SD_HIL_END")
'''


def build_payload(record_count: int, mode: str = "basic", delay_ms: int = 5000) -> str:
    logger_source = LOGGER_SOURCE.read_text(encoding="utf-8")
    payload = MICROPYTHON_TEST.replace("__LOGGER_SOURCE__", repr(logger_source))
    payload = payload.replace("__RECORD_COUNT__", str(int(record_count)))
    payload = payload.replace("__DELAY_MS__", str(int(delay_ms)))
    return payload.replace("__MODE__", mode)


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


def execute_payload(port_name: str, baudrate: int, payload: str, read_seconds: float = 20) -> tuple[int, str]:
    with serial.Serial(port_name, baudrate=baudrate, timeout=0.2, write_timeout=5) as port:
        port.write(b"\x03\x03")
        read_available(port, 0.5)
        port.write(b"\x01")
        read_available(port, 0.5)
        port.write(("exec(" + repr(payload) + ")\r\n").encode("utf-8"))
        port.write(b"\x04")
        output = read_available(port, read_seconds)
    text = output.decode("utf-8", errors="replace")
    print(text)
    if "CODEX_SD_HIL_BEGIN" not in text or "CODEX_SD_HIL_END" not in text:
        print("Missing SD HIL result markers", file=sys.stderr)
        return 2, text
    if "|FAIL|" in text or "EXCEPTION|FAIL|" in text:
        return 1, text
    return 0, text


def run(port_name: str, baudrate: int, record_count: int) -> int:
    code, _text = execute_payload(port_name, baudrate, build_payload(record_count))
    return code


def run_interactive_removal(port_name: str, baudrate: int) -> int:
    print("Step 1/3: checking card is present.")
    present_code, _present_text = execute_payload(port_name, baudrate, build_payload(0, "probe"))
    if present_code != 0:
        print("Initial card-present probe failed; insert/mount state is not ready.", file=sys.stderr)
        return present_code

    input("Step 2/3: remove the microSD card, then press Enter here.")
    removed_code, _removed_text = execute_payload(port_name, baudrate, build_payload(0, "probe"))
    if removed_code == 0:
        print("Removal probe unexpectedly mounted the card.", file=sys.stderr)
        return 1
    print("Removal probe failed to mount as expected.")

    input("Step 3/3: reinsert the microSD card, wait a few seconds, then press Enter here.")
    reinsert_code, _reinsert_text = execute_payload(port_name, baudrate, build_payload(0, "probe"))
    if reinsert_code != 0:
        print("Reinsert probe failed; SD reinitialization did not recover.", file=sys.stderr)
        return reinsert_code
    print("Interactive removal/reinsert check passed.")
    return 0


def run_interactive_write_error(port_name: str, baudrate: int) -> int:
    print("Step 1/3: checking card is present.")
    present_code, _present_text = execute_payload(port_name, baudrate, build_payload(0, "probe"))
    if present_code != 0:
        print("Initial card-present probe failed; insert/mount state is not ready.", file=sys.stderr)
        return present_code

    print("Step 2/3: the Pico will print CODEX_REMOVE_CARD_NOW, then wait 20 seconds before write/flush.")
    print("Remove the microSD as soon as CODEX_REMOVE_CARD_NOW appears.")
    wr_code, _wr_text = execute_payload(port_name, baudrate, build_payload(0, "delayed_write_error", delay_ms=20000), read_seconds=45)
    if wr_code != 0:
        print("Write-error probe command returned a failing status.", file=sys.stderr)
        return wr_code

    input("Step 3/3: reinsert the microSD card, wait a few seconds, then press Enter here.")
    reinsert_code, _reinsert_text = execute_payload(port_name, baudrate, build_payload(0, "probe"))
    if reinsert_code != 0:
        print("Reinsert probe failed after write-error probe.", file=sys.stderr)
        return reinsert_code
    print("Interactive write-error/reinsert check passed.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run Pico SD HIL checks over MicroPython REPL.")
    parser.add_argument("--port", default="COM14", help="Serial port, e.g. COM14")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--records", type=int, default=160, help="Logger records to write in the queue-path check")
    parser.add_argument("--probe", action="store_true", help="Run one SD mount probe only")
    parser.add_argument("--interactive-removal", action="store_true", help="Run card removal/reinsert mount probes with operator prompts")
    parser.add_argument("--interactive-write-error", action="store_true", help="Run a write/flush error probe after operator removes the card")
    args = parser.parse_args(argv)
    if args.probe:
        return execute_payload(args.port, args.baudrate, build_payload(0, "probe"))[0]
    if args.interactive_removal:
        return run_interactive_removal(args.port, args.baudrate)
    if args.interactive_write_error:
        return run_interactive_write_error(args.port, args.baudrate)
    return run(args.port, args.baudrate, args.records)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
