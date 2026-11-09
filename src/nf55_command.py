# ATE名とNF55Gコマンド・DATA・応答条件・Cache操作の対応表。
# RefreshはD0-D5のうち定義済みの読出しコマンドを実装。

"""NF55G command definitions and wire DATA builders."""

try:
    from . import config
    from .rtc_driver import RTCDateTime, RTCError
except ImportError:  # pragma: no cover
    import config
    from rtc_driver import RTCDateTime, RTCError


class CommandError(ValueError):
    pass


# Explicit allowlists from ATE_Command_Master sections 2, 5, and 6.
# Reserved decoder fields are deliberately not ATE commands.
READ_REFRESH_COMMANDS = {
    "DATA_REFRESH": ("D0", "DATA", config.T2_D0_MS, 327),
    "STATUS_REFRESH": ("D1", "STATUS", 100, 15),
    "INFO_REFRESH": ("D5", "INFO", 100, 100),
    "D2_REFRESH": ("D2", "D2", 100, 30),
    "D3_REFRESH": ("D3", "D3", 200, 21),
    "D4_MAINT_READ": ("D4", "D4", 100, 212),
}
DATA_QUERY_FIELDS = {
    "NF55_DATE?": "DATE",
    "NF55_TIME?": "TIME",
    "NF55_DATETIME?": "DATETIME",
    "VOUT12?": "VOUT12",
    "IOUT12?": "IOUT12",
    "BATT_VOLT?": "BATT_VOLT",
    "CHG_VOLT?": "CHG_VOLT",
    "CHG_CURR?": "CHG_CURR",
    "BATT_CURR?": "BATT_CURR",
    "BATT_SOC_WH?": "BATT_SOC_WH",
    "BATT_SOC_MAH?": "BATT_SOC_MAH",
    "BATT_TEMP?": "BATT_TEMP",
    "ADU_TEMP?": "ADU_TEMP",
    "BBU_TEMP?": "BBU_TEMP",
    "FAN_RPM?": "FAN_RPM",
    "FAN_LEVEL?": "FAN_LEVEL",
    "AC_OFF_HOUR?": "AC_OFF_HOUR",
    "PS_OFF_HOUR?": "PS_OFF_HOUR",
    "AVE_OFF_TEMP?": "AVE_OFF_TEMP",
    "OFF_CHARGE_HOUR?": "OFF_CHARGE_HOUR",
    "AVE_CHARGE_TEMP?": "AVE_CHARGE_TEMP",
    "OFF_CHARGE?": "OFF_CHARGE",
    "OFF_BATT_DEG?": "OFF_BATT_DEG",
    "CHARGE_DATA?": "CHARGE_DATA",
    "CHARGE_END?": "CHARGE_END",
    "LIFE_BATT_CHARGE?": "LIFE_BATT_CHARGE",
    "LIFE_BATT_TEMP?": "LIFE_BATT_TEMP",
    "LIFE_BATT_DEG?": "LIFE_BATT_DEG",
    "TOTAL_ADU_TEMP?": "TOTAL_ADU_TEMP",
    "TOTAL_ADU_HOUR?": "TOTAL_ADU_HOUR",
    "AC_FAIL_COUNT?": "AC_FAIL_COUNT",
    "AC_LOW_COUNT?": "AC_LOW_COUNT",
    "BACKUP_COUNT?": "BACKUP_COUNT",
    "BATT_DEG_TOTAL?": "BATT_DEG_TOTAL",
    "TOTAL_BATT_HOUR?": "TOTAL_BATT_HOUR",
    "BATT_DISCHARGE_COUNT?": "BATT_DISCHARGE_COUNT",
    "BATT_CHARGE_COUNT?": "BATT_CHARGE_COUNT",
    "BATT_TTL_DISCHARGE?": "BATT_TTL_DISCHARGE",
    "BATT_TTL_CHARGE?": "BATT_TTL_CHARGE",
    "TOTAL_BATT_TEMP?": "TOTAL_BATT_TEMP",
    "BATT_TEMP_AVE?": "BATT_TEMP_AVE",
    "BATT_TEMP_MAX?": "BATT_TEMP_MAX",
    "BATT_TEMP_MIN?": "BATT_TEMP_MIN",
}
STATUS_QUERY_FIELDS = (
    "PS_ON", "BURST_ON", "BURST", "PS_OFF_CHARGE", "RESTART_READY",
    "BACKUP_READY", "CHARGE_READY", "BATT_CHECK_RUN", "CHARGE_OFF_STATUS",
    "CHARGE_ON_STATUS", "BATT_ON", "BATT_LOW", "S_CHARGE_ON", "CHARGE_OK",
    "CHARGER_ON", "FAN_WNG", "ADU_TEMP_WNG", "OC_OFF_H", "PFC_OV",
    "FAN_FAIL", "BBU_TEMP_WNG", "BBU_FAIL", "CHG_LV", "CHG_OV", "CHG_OC",
    "BATT_TEMP_WNG", "BATT_TEMP_ALM", "BATT_LV", "BATT_OV", "BATT_LIFE",
    "BATT_MCN", "BATT_P_FAIL", "BATT_DCN", "12V_OV", "12V_LV", "12V_OC",
    "12V_OC_OFF_L",
)
INFO_QUERY_FIELDS = (
    "FW_REV", "UNIT_REV", "UNIT_LOT", "UNIT_SERIAL", "ADU_REV", "ADU_LOT",
    "ADU_SERIAL", "BBU_REV", "BBU_LOT", "BBU_SERIAL", "PS_ON_BACKUP",
    "AC_LINK", "AUTO_CHARGE", "EVENT_ENABLE", "MAX_BACKUP_TIME",
    "MIN_BACKUP_TIME", "RESTART_TIME", "BATT_LOW_THD", "BATT_CAP_MAH",
    "BATT_CAP_WH", "CHG_IR_THD", "BATT_WNG_THD", "BATT_ALM_THD",
    "ADU_TEMP_THD", "BBU_TEMP_THD", "FAN_WNG_THD",
)
CACHE_QUERY_COMMANDS = {}
for _command, _field in DATA_QUERY_FIELDS.items():
    CACHE_QUERY_COMMANDS[_command] = ("DATA", _field)
for _cache, _fields in (("STATUS", STATUS_QUERY_FIELDS), ("INFO", INFO_QUERY_FIELDS)):
    for _field in _fields:
        CACHE_QUERY_COMMANDS[_field + "?"] = (_cache, _field)

REFRESH_REQUIRED_FIELDS = {
    "D2": (
        "AC_OFF_HOUR", "PS_OFF_HOUR", "AVE_OFF_TEMP", "OFF_CHARGE_HOUR",
        "AVE_CHARGE_TEMP", "OFF_CHARGE", "OFF_BATT_DEG",
    ),
    "D3": (
        "CHARGE_DATA", "CHARGE_END", "LIFE_BATT_CHARGE", "LIFE_BATT_TEMP",
        "LIFE_BATT_DEG", "EVENT_LOST",
    ),
    "D4": (
        "YEAR2", "MONTH2", "DAY2", "HOUR2", "MIN2", "SEC2", "DATE", "TIME",
        "DATETIME", "VOUT12", "IOUT12", "BATT_VOLT", "CHG_VOLT", "CHG_CURR",
        "BATT_CURR", "BATT_SOC_WH", "BATT_SOC_MAH", "BATT_TEMP", "ADU_TEMP",
        "BBU_TEMP", "FAN_RPM", "FAN_LEVEL", "MODE", "V1", "V2", "I1", "I2",
        "TEMP", "SOC", "IR", "TOTAL_ADU_TEMP", "TOTAL_ADU_HOUR", "AC_FAIL_COUNT",
        "AC_LOW_COUNT", "BACKUP_COUNT", "BATT_DEG_TOTAL", "TOTAL_BATT_HOUR",
        "BATT_DISCHARGE_COUNT", "BATT_CHARGE_COUNT", "BATT_TTL_DISCHARGE",
        "BATT_TTL_CHARGE", "TOTAL_BATT_TEMP", "BATT_TEMP_AVE", "BATT_TEMP_MAX",
        "BATT_TEMP_MIN", "FW_REV", "UNIT_REV", "UNIT_LOT", "UNIT_SERIAL", "ADU_REV",
        "ADU_LOT", "ADU_SERIAL", "BBU_REV", "BBU_LOT", "BBU_SERIAL",
    ),
}


class NF55CommandSpec:
    __slots__ = ("ate_name", "nf_cmd", "data", "t2_ms", "cache_action")

    def __init__(self, ate_name, nf_cmd, data=b"", t2_ms=None, cache_action=None):
        self.ate_name = ate_name
        self.nf_cmd = nf_cmd
        self.data = data
        self.t2_ms = config.T2_DEFAULT_MS if t2_ms is None else int(t2_ms)
        self.cache_action = cache_action or nf_cmd


CONTROL_COMMANDS = {
    # CLEARはr1 p.35の既定データとT2を使用し、送信後に関連Cacheを無効化する。
    "CLEAR_ALL": NF55CommandSpec("CLEAR_ALL", "CD", b"0", 500, "CD"),
    "CLEAR_POWER": NF55CommandSpec("CLEAR_POWER", "CD", b"1", 500, "CD"),
    "CLEAR_BATT": NF55CommandSpec("CLEAR_BATT", "CD", b"2", 500, "CD"),
    "CLEAR_LOG": NF55CommandSpec("CLEAR_LOG", "CL", b"", 1000, "CL"),
    "CHARGE_ON": NF55CommandSpec("CHARGE_ON", "CN", b"1", cache_action="CN"),
    "CHARGE_ON_STOP": NF55CommandSpec("CHARGE_ON_STOP", "CN", b"0", cache_action="CN"),
    "CHARGE_OFF": NF55CommandSpec("CHARGE_OFF", "CF", b"1", cache_action="CF"),
    "CHARGE_OFF_CLEAR": NF55CommandSpec("CHARGE_OFF_CLEAR", "CF", b"0", cache_action="CF"),
    "BACKUP_ENABLE": NF55CommandSpec("BACKUP_ENABLE", "BE", b"", cache_action="BE"),
    "BACKUP_OFF": NF55CommandSpec("BACKUP_OFF", "BF", b"", cache_action="BF"),
    "OUTPUT_RESTART": NF55CommandSpec("OUTPUT_RESTART", "OR", b"", cache_action="OR"),
    "PARAM_RESET": NF55CommandSpec("PARAM_RESET", "RP", b"", cache_action="RP"),
}


def build_control_command(ate_name, payload=None):
    if ate_name == "CLOCK_SYNC":
        try:
            data = _ascii_bytes(payload)
        except UnicodeError:
            raise CommandError("CLOCK_SYNC payload must be 12 ASCII digits")
        if len(data) != 12 or not all(48 <= value <= 57 for value in data):
            raise CommandError("CLOCK_SYNC payload must be 12 ASCII digits")
        text = data.decode("ascii")
        try:
            timestamp = RTCDateTime.parse_ate("20" + text[:6] + "_" + text[6:])
        except RTCError:
            raise CommandError("CLOCK_SYNC payload is not a valid datetime")
        encoded = "{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}".format(
            timestamp.year - 2000, timestamp.month, timestamp.day,
            timestamp.hour, timestamp.minute, timestamp.second,
        ).encode("ascii")
        return NF55CommandSpec("CLOCK_SYNC", "SC", encoded, cache_action="SC")

    if ate_name == "PARAM_SET":
        data = _ascii_bytes(payload)
        if len(data) != 50:
            raise CommandError("PARAM_SET payload must be exactly 50 ASCII chars")
        return NF55CommandSpec("PARAM_SET", "SP", data, cache_action="SP")

    if ate_name not in CONTROL_COMMANDS:
        raise CommandError("unsupported control command: {}".format(ate_name))

    spec = CONTROL_COMMANDS[ate_name]
    if payload not in (None, b"", ""):
        raise CommandError("{} does not accept payload".format(ate_name))
    return spec


def _ascii_bytes(value):
    if value is None:
        return b""
    if isinstance(value, bytes):
        value.decode("ascii")
        return value
    if isinstance(value, bytearray):
        data = bytes(value)
        data.decode("ascii")
        return data
    return str(value).encode("ascii")
