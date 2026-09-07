"""ATE ASCII command parser and router.

The parser classifies commands only. It does not perform cache updates, product
judgement, or NF55G transmission.
"""


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
    "PARAM_RESET",
    "PARAM_SET",
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
    if name in LOGGER_COMMANDS:
        return ParsedCommand(text, name, payload=payload, category="LOGGER")
    if name in RTC_COMMANDS or name.startswith(RTC_PREFIXES):
        return ParsedCommand(text, name, payload=payload, category="RTC")
    if name in DIAGNOSTIC_COMMANDS:
        return ParsedCommand(text, name, payload=payload, category="DIAGNOSTIC")
    if name in CONTROL_COMMANDS:
        return ParsedCommand(text, name, payload=payload, category="CONTROL")
    return ParsedCommand(text, name, payload=payload, category="UNKNOWN")


def _normalize_line(line):
    if isinstance(line, bytes):
        line = line.decode("ascii")
    return str(line).strip()


def _split_payload(text):
    if " " in text:
        name, payload = text.split(" ", 1)
        return name, payload.strip()
    if "=" in text:
        name, payload = text.split("=", 1)
        return name, payload.strip()
    return text, None

