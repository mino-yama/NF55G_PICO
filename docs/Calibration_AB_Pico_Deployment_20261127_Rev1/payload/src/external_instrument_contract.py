# 2026-11-20ユーザー承認の開発用中継契約。I/Oを持たず受付とフレーム検証だけを行う。
# ATE本文をstripせず保持し、親子フレームは長さ/CRCを照合してから返す。

"""Approved development contract; not yet connected to FixtureApp or Host FW."""
import binascii

ATE_BAUDRATE = 57600
LINK_BAUDRATE = 115200
PARENT_TX_PIN = 12
PARENT_RX_PIN = 13
HOST_TX_PIN = 0
HOST_RX_PIN = 1
MAX_COMMAND_BYTES = 192
MAX_RESPONSE_BYTES = 192
MAX_FRAME_BYTES = 512
MAX_TIMEOUT_MS = 10000
DEVICE_ENDING = b"\r\n"
FRAME_KINDS = ("H", "h", "Q", "A", "T", "R", "E", "I", "i", "S", "K")


class ContractError(ValueError):
    pass


def _uint(value, maximum):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= maximum


def parse_monitor_request(line):
    if not isinstance(line, bytes):
        raise ContractError("REQUEST_BYTES")
    if line.endswith(b"\r\n"):
        line = line[:-2]
    elif line.endswith((b"\r", b"\n")):
        line = line[:-1]
    parts = line.split(b" ", 2)
    if len(parts) != 3 or parts[0] not in (b"EXT_QUERY", b"EXT_SEND"):
        raise ContractError("REQUEST_FORMAT")
    name, timeout, command = parts
    if not timeout or any(c < 48 or c > 57 for c in timeout) or len(timeout) > 5:
        raise ContractError("TIMEOUT")
    timeout_ms = int(timeout)
    if not 1 <= timeout_ms <= MAX_TIMEOUT_MS:
        raise ContractError("TIMEOUT")
    if not command or len(command) > MAX_COMMAND_BYTES:
        raise ContractError("COMMAND_LENGTH")
    if any(c < 32 or c > 126 for c in command):
        raise ContractError("COMMAND_ASCII")
    query = name == b"EXT_QUERY"
    return {"command": command, "expects_response": query, "timeout_ms": timeout_ms,
            "response_ending": DEVICE_ENDING if query else None}


def encode_frame(session, request, kind, mode, timeout_ms, payload):
    # sessionは親nonce8byte+Host nonce8byte。nonce生成・接続照合の意味検証はadapter担当。
    if not isinstance(session, bytes) or len(session) != 16:
        raise ContractError("SESSION")
    if not _uint(request, 0xffffffff) or kind not in FRAME_KINDS:
        raise ContractError("HEADER")
    if not _uint(mode, 1) or not _uint(timeout_ms, MAX_TIMEOUT_MS):
        raise ContractError("HEADER")
    if not isinstance(payload, bytes) or len(payload) > MAX_COMMAND_BYTES:
        raise ContractError("PAYLOAD_LENGTH")
    prefix = ("@X1,{},{:08X},{},{},{:08X},{:04X},{},".format(
        binascii.hexlify(session).decode("ascii").upper(), request, kind, mode,
        timeout_ms, len(payload), binascii.hexlify(payload).decode("ascii").upper())).encode("ascii")
    frame = prefix + ("{:08X}".format(binascii.crc32(prefix) & 0xffffffff)).encode("ascii") + DEVICE_ENDING
    if len(frame) > MAX_FRAME_BYTES:
        raise ContractError("FRAME_LENGTH")
    return frame


def _hex_number(text, width):
    if len(text) != width or any(c not in "0123456789abcdefABCDEF" for c in text):
        raise ContractError("HEX")
    return int(text, 16)


def decode_frame(frame):
    if not isinstance(frame, bytes) or len(frame) > MAX_FRAME_BYTES:
        raise ContractError("FRAME_LENGTH")
    if not frame.endswith(DEVICE_ENDING):
        raise ContractError("FRAME_ENDING")
    try:
        text = frame[:-2].decode("ascii")
    except UnicodeError:
        raise ContractError("FRAME_ASCII")
    fields = text.split(",")
    if len(fields) != 9 or fields[0] != "@X1":
        raise ContractError("FRAME_FORMAT")
    _, session_hex, request_hex, kind, mode_text, timeout_hex, length_hex, payload_hex, crc_hex = fields
    crc = _hex_number(crc_hex, 8)
    prefix = frame[:-(8 + len(DEVICE_ENDING))]
    if binascii.crc32(prefix) & 0xffffffff != crc:
        raise ContractError("CRC")
    if len(session_hex) != 32:
        raise ContractError("SESSION")
    _hex_number(session_hex, 32)
    request = _hex_number(request_hex, 8)
    timeout_ms = _hex_number(timeout_hex, 8)
    length = _hex_number(length_hex, 4)
    if kind not in FRAME_KINDS or mode_text not in ("0", "1") or timeout_ms > MAX_TIMEOUT_MS:
        raise ContractError("HEADER")
    if length > MAX_COMMAND_BYTES or len(payload_hex) != length * 2:
        raise ContractError("PAYLOAD_LENGTH")
    if payload_hex:
        _hex_number(payload_hex, length * 2)
    return {"session": binascii.unhexlify(session_hex), "request": request,
            "kind": kind, "mode": int(mode_text), "timeout_ms": timeout_ms,
            "payload": binascii.unhexlify(payload_hex)}


def format_query_response(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise ContractError("RESPONSE_LENGTH")
    if not raw.endswith(DEVICE_ENDING) or raw.find(DEVICE_ENDING) != len(raw) - 2:
        raise ContractError("RESPONSE_ENDING")
    return "OK:EXT_RX:{}:{}".format(len(raw), binascii.hexlify(raw).decode("ascii").upper())


def format_error(reason, ambiguous):
    if (not isinstance(reason, str) or not reason or
            any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for c in reason) or
            not isinstance(ambiguous, bool)):
        raise ContractError("ERROR_FORMAT")
    return "ERR:EXT_{}:AMBIGUOUS={}".format(reason, 1 if ambiguous else 0)


SEND_COMPLETE_REPLY = "OK:EXT_TX"
