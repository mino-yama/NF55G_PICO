# ATEの1行をコマンド名・引数に分け、Refresh／Query／Control等に分類する。
# ここでは送信やCache更新を行わず、FW_UPDATEは送信禁止の分類にする。

"""ATE ASCII command parser and router.

The parser classifies commands only. It does not perform cache updates, product
judgement, or NF55G transmission.
"""


try:
    from .nf55_command import CommandError, resolve_read_command, CACHE_QUERY_COMMANDS
    from .nf55_command import build_item_parameter_command, build_life_command
except ImportError:  # pragma: no cover
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
    text = _normalize_line(line)
    if not text:
        raise ParseError("EMPTY_COMMAND")

    name, payload = _split_payload(text)

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
