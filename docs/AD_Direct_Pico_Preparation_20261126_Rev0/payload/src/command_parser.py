# ATEの1行をコマンド名・引数に分け、Refresh／Query／Control等に分類する。
# ここでは送信やCache更新を行わず、FW_UPDATEは送信禁止の分類にする。

"""ATE ASCII command parser and router.

The parser classifies commands only. It does not perform cache updates, product
judgement, or NF55G transmission.
"""


try:
    from .calibration_write import parse_direct_ad
    from .calibration_acquisition import parse_measure_request, parse_acquisition_id, MeasurementError
    from .external_instrument_contract import ContractError, parse_monitor_request
    from .nf55_command import CommandError, resolve_read_command, CACHE_QUERY_COMMANDS
    from .nf55_command import build_item_parameter_command, build_life_command
except ImportError:  # pragma: no cover
    from calibration_write import parse_direct_ad
    from calibration_acquisition import parse_measure_request, parse_acquisition_id, MeasurementError
    from external_instrument_contract import ContractError, parse_monitor_request
    from nf55_command import CommandError, resolve_read_command, CACHE_QUERY_COMMANDS
    from nf55_command import build_item_parameter_command, build_life_command


LOGGER_COMMANDS = (
    "TEST_START",
    "TEST_END",
    "LOG_CONT_START",
    "LOG_CONT_STOP",
    "SD_STATUS?",
    "SD_USAGE?",
    "LOG_DROP_COUNT?",
    "SD_REINIT",
)

RTC_PREFIXES = ("RTC_SET_",)
RTC_COMMANDS = ("RTC_DATE?", "RTC_TIME?", "RTC_DATETIME?", "RTC_CHECK?")

DIAGNOSTIC_COMMANDS = (
    "*IDN?",
    "PICO_SELF_CHECK?",
    "NF_COMM_CHECK?",
    "COMM_STATUS?",
    "RETRY_COUNT?",
)

CONTROL_COMMANDS = (
    "CHARGE_ON",
    "CHARGE_ON_STOP",
    "CHARGE_OFF",
    "CHARGE_OFF_CLEAR",
    "BACKUP_ENABLE",
    "BACKUP_OFF",
    "OUTPUT_RESTART",
    "BATT_CHECK_START",
    "BATT_CHECK_STOP",
    "PARAM_RESET",
    "CLEAR_ALL",
    "CLEAR_POWER",
    "CLEAR_BATT",
    "CLEAR_LOG",
    "PARAM_SET",
    "CLOCK_SYNC",
    "ERP_SET_1_0",
    "ERP_SET_0_0",
    "ERP_SET_0_1",
    "ERP_SET_1_1",
)


class ParsedCommand:
    __slots__ = ("raw", "name", "payload", "category")

    def __init__(self, raw, name, payload=None, category="UNKNOWN"):
        self.raw = raw
        self.name = name
        self.payload = payload
        self.category = category


class ParseError(ValueError):
    pass


def parse_ate_command(line):
    # 中継本文の空白を一般コマンド用stripで失わせない。
    raw = line.encode('ascii') if isinstance(line, str) else line
    head = raw.split(b' ', 1)[0].rstrip(b'\r\n') if isinstance(raw, bytes) else b''
    if head == b'CAL_MEASURE' or head.startswith(b'CAL_MEASURE_'):
        try:
            request_raw = raw if head == b'CAL_MEASURE' else b'CAL_MEASURE ' + head[12:] + raw[len(head):]
            request = parse_measure_request(request_raw)
        except MeasurementError as exc:
            raise ParseError('CAL_' + str(exc))
        return ParsedCommand(raw.decode('ascii'), head.decode('ascii'), payload=request, category='CALIBRATION_ACQUIRE')
    if isinstance(raw, bytes) and raw.split(b' ', 1)[0].rstrip(b'\r\n') in (b'EXT_QUERY', b'EXT_SEND'):
        try:
            request = parse_monitor_request(raw)
        except ContractError as exc:
            raise ParseError('EXT_' + str(exc) + ':AMBIGUOUS=0')
        return ParsedCommand(raw.decode('ascii'), raw.split(b' ', 1)[0].decode('ascii'),
                             payload=request, category='EXTERNAL')
    text = _normalize_line(line)
    if not text:
        raise ParseError("EMPTY_COMMAND")

    if text == "HOST_INFO? METER":
        return ParsedCommand(text, "HOST_INFO?", payload="INFO", category="HOST_MANAGEMENT")
    if text == "HOST_RESET METER":
        return ParsedCommand(text, "HOST_RESET", payload="RESET", category="HOST_MANAGEMENT")

    name, payload = _split_payload(text)

    if name in ('QR_SCAN', 'QR_GET?', 'QR_DATA?', 'QR_WRITE', 'QR_CANCEL'):
        if name == 'QR_CANCEL':
            if payload is not None:
                raise ParseError('UNEXPECTED_PAYLOAD')
        elif name == 'QR_SCAN':
            if not payload or any(c not in '0123456789' for c in payload) or not 100 <= int(payload) <= 60000:
                raise ParseError('QR_TIMEOUT_RANGE')
            payload = int(payload)
        elif not payload or len(payload) > 80 or any(c not in '0123456789abcdefABCDEFQ-' for c in payload):
            raise ParseError('QR_ID')
        return ParsedCommand(text, name, payload=payload, category='QR_WRITE_SESSION')

    if name == 'CAL_MEASUREMENT?':
        try:
            token = parse_acquisition_id(payload)
        except MeasurementError as exc:
            raise ParseError('CAL_' + str(exc))
        return ParsedCommand(text, name, payload=token, category='CALIBRATION_QUERY')

    if name.startswith('CAL_MEASUREMENT_') and name.endswith('?'):
        if payload not in ('A', 'B'):
            raise ParseError('CAL_POINT')
        return ParsedCommand(text, name, payload=(name[16:-1], payload), category='CALIBRATION_LATEST')

    if name.startswith('CAL_WRITE_'):
        parts = (payload or '').split()
        if len(parts) != 2 or parts[0] not in ('A', 'B') or parts[1] not in ('P1', 'P2'):
            raise ParseError('CAL_WRITE_ARGUMENTS')
        return ParsedCommand(text, 'CAL_WRITE_LATEST', payload=(name[10:], parts[0], parts[1]),
                             category='CALIBRATION_WRITE')

    if name.startswith('AD_VERIFY_'):
        if payload not in ('P1', 'P2'):
            raise ParseError('AD_VERIFY_ARGUMENTS')
        return ParsedCommand(text, 'AD_VERIFY_READBACK', payload=(name[10:], payload), category='CALIBRATION_WRITE')

    if name in ('CAL_WRITE', 'AD_VERIFY'):
        parts = (payload or '').split()
        if len(parts) != 2 or parts[1] not in ('P1', 'P2'):
            raise ParseError(name + '_ARGUMENTS')
        if name == 'CAL_WRITE':
            try:
                parts[0] = parse_acquisition_id(parts[0])
            except MeasurementError as exc:
                raise ParseError('CAL_' + str(exc))
        return ParsedCommand(text, name, payload=tuple(parts), category='CALIBRATION_WRITE')

    if name.startswith('AD_'):
        try:
            request = parse_direct_ad(name, payload)
        except MeasurementError as exc:
            raise ParseError(str(exc))
        return ParsedCommand(text, 'AD_DIRECT', payload=request, category='CALIBRATION_WRITE')

    if name == "FW_UPDATE":
        return ParsedCommand(text, name, payload=payload, category="FORBIDDEN")
    try:
        read_spec = resolve_read_command(name)
    except CommandError as exc:
        raise ParseError(str(exc))
    if read_spec is not None or name in CACHE_QUERY_COMMANDS:
        if payload is not None:
            raise ParseError("UNEXPECTED_PAYLOAD")
        category = "REFRESH" if read_spec is not None else "QUERY"
        return ParsedCommand(text, name, category=category)
    if name in LOGGER_COMMANDS:
        return ParsedCommand(text, name, payload=payload, category="LOGGER")
    if name in RTC_COMMANDS or name.startswith(RTC_PREFIXES):
        return ParsedCommand(text, name, payload=payload, category="RTC")
    if name in DIAGNOSTIC_COMMANDS:
        return ParsedCommand(text, name, payload=payload, category="DIAGNOSTIC")
    if name in CONTROL_COMMANDS:
        return ParsedCommand(text, name, payload=payload, category="CONTROL")
    if name.startswith("LIFE_SET_"):
        try:
            build_life_command(name, payload)
        except CommandError as exc:
            raise ParseError(str(exc))
        return ParsedCommand(text, name, payload=payload, category="CONTROL")
    if name.startswith("PARAM_"):
        # 項目・10進値・余分な引数を、Cache操作や接続確認より先に検証する。
        try:
            build_item_parameter_command(name, payload)
        except CommandError as exc:
            raise ParseError(str(exc))
        return ParsedCommand(text, name, category="CONTROL")
    return ParsedCommand(text, name, payload=payload, category="UNKNOWN")


def _normalize_line(line):
    if isinstance(line, bytes):
        line = line.decode("ascii")
    return str(line).strip()


def _split_payload(text):
    # RAWのDATA内の空白を、コマンド名との区切りとして再解釈しない。
    if text.startswith("LIFE_SET_RAW="):
        return "LIFE_SET_RAW", text[len("LIFE_SET_RAW="):]
    if " " in text:
        name, payload = text.split(" ", 1)
        return name, payload.strip()
    if "=" in text:
        name, payload = text.split("=", 1)
        return name, payload.strip()
    return text, None
