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
# 履歴開始番号のATE表記は10進、NF55Gへはルール②の2桁ASCII HEXで送る。
READ_REQUEST_DATA = {}
for _kind, _starts in (("EL", (1, 9, 17, 25)),
                       ("OL", (1, 9, 17, 25, 33, 41, 49, 57))):
    for _start in _starts:
        _name = "{}_REFRESH_{:02d}".format(_kind, _start)
        READ_REFRESH_COMMANDS[_name] = (_kind, "{}_{:02d}".format(_kind, _start), 100, 82)
        READ_REQUEST_DATA[_name] = "{:02X}".format(_start).encode("ascii")


def resolve_read_command(ate_name):
    if ate_name in READ_REFRESH_COMMANDS:
        return READ_REFRESH_COMMANDS[ate_name] + (READ_REQUEST_DATA.get(ate_name, b""),)
    if ate_name.startswith("FD_READ_"):
        address = ate_name[len("FD_READ_"):]
        if len(address) != 6 or any(c not in "0123456789ABCDEFabcdef" for c in address):
            raise CommandError("FD address must be 6 ASCII HEX chars")
        # アドレスは既にASCII HEX。範囲外の製品応答を推測・FF補完しない。
        return ("FD", "FD", 100, 64, address.encode("ascii"))
    return None


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

# 各履歴Queryは対応する8件ブロックだけを参照する。Queryで通信しない。
for _kind, _limit in (("EL", 32), ("OL", 64)):
    for _number in range(1, _limit + 1):
        _block = "{}_{:02d}".format(_kind, ((_number - 1) // 8) * 8 + 1)
        for _field in ("DATEHOUR", "ID"):
            _key = "{}_{:02d}_{}".format(_kind, _number, _field)
            CACHE_QUERY_COMMANDS[_key + "?"] = (_block, _key)
CACHE_QUERY_COMMANDS["FD_DATA?"] = ("FD", "FD_RAW")

BC_QUERY_FIELDS = ("BC_MODE", "BC_V1", "BC_V2", "BC_I1", "BC_I2", "BC_TEMP", "BC_SOC", "BC_IR")
for _field in BC_QUERY_FIELDS:
    CACHE_QUERY_COMMANDS[_field + "?"] = ("BC", _field)

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
    # BCは開始・停止とも寿命診断DATA30文字、T2=6秒。Cache操作は別管理する。
    "BATT_CHECK_START": NF55CommandSpec("BATT_CHECK_START", "BC", b"1", config.T2_BC_MS, "BC_START"),
    "BATT_CHECK_STOP": NF55CommandSpec("BATT_CHECK_STOP", "BC", b"0", config.T2_BC_MS, "BC_STOP"),
    # SET ERPはBURST／PS_OFF_CHARGE／予約00の4文字。両設定を毎回明示する。
    "ERP_SET_1_0": NF55CommandSpec("ERP_SET_1_0", "SE", b"1000", 100, "SE"),
    "ERP_SET_0_0": NF55CommandSpec("ERP_SET_0_0", "SE", b"0000", 100, "SE"),
    "ERP_SET_0_1": NF55CommandSpec("ERP_SET_0_1", "SE", b"0100", 100, "SE"),
    "ERP_SET_1_1": NF55CommandSpec("ERP_SET_1_1", "SE", b"1100", 100, "SE"),
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


# 項目別SPは未指定項目を最大HEX値（変更なし）、予約18文字を0で生成する。
# 保護設定と意味未確定のCHG_IR_THDは、この入口から変更しない。
PARAMETER_ITEMS = {
    "PS_ON_BACKUP": (0, 1, 1),
    "AC_LINK": (1, 1, 1),
    "AUTO_CHARGE": (2, 1, 3),
    "EVENT_ENABLE": (3, 1, 1),
    "MAX_BACKUP_TIME": (4, 1, 14),
    "MIN_BACKUP_TIME": (5, 2, 254),
    "RESTART_TIME": (7, 2, 254),
    "BATT_LOW_THD": (9, 2, 100),
    "BATT_CAP_MAH": (11, 4, 65534),
    "BATT_CAP_WH": (15, 2, 254),
}
PROTECTED_PARAMETER_ITEMS = (
    "BATT_WNG_THD", "BATT_ALM_THD", "ADU_TEMP_THD", "BBU_TEMP_THD", "FAN_WNG_THD",
)


def build_item_parameter_command(ate_name, payload=None):
    if payload is not None:
        raise CommandError("UNEXPECTED_PAYLOAD")
    fields = ate_name[len("PARAM_"):].rsplit("_", 1)
    if len(fields) != 2:
        raise CommandError("PARAMETER_FORMAT")
    item, value_text = fields
    if item in PROTECTED_PARAMETER_ITEMS:
        raise CommandError("PARAMETER_PROTECTED")
    if item == "CHG_IR_THD":
        raise CommandError("PARAMETER_UNCONFIRMED")
    if item not in PARAMETER_ITEMS:
        raise CommandError("PARAMETER_UNKNOWN_ITEM")
    if not value_text or any(c not in "0123456789" for c in value_text):
        raise CommandError("PARAMETER_VALUE")
    value = int(value_text)
    offset, width, maximum = PARAMETER_ITEMS[item]
    if value > maximum:
        raise CommandError("PARAMETER_RANGE")
    encoded = ("{:0" + str(width) + "X}").format(value)
    data = ("F" * offset + encoded + "F" * (32 - offset - width) + "0" * 18).encode("ascii")
    return NF55CommandSpec(ate_name, "SP", data, 100, "SP")


# SLの通常入口は10進整数を最小3桁HEXへ変換し、予約5文字を0で付加する。
# OI-08実機試験のため範囲外を拒否・丸め・切捨てしない。RAWはASCII DATAを保持する。
def build_life_command(ate_name, payload=None):
    if ate_name == "LIFE_SET_RAW":
        if payload is None:
            raise CommandError("LIFE_RAW_PAYLOAD_REQUIRED")
        try:
            data = _ascii_bytes(payload)
        except UnicodeError:
            raise CommandError("LIFE_RAW_ASCII")
        # ATEの1行とNFフレームの区切りは維持し、DATAのHEX・値・長さは検査しない。
        if any(value < 32 or value > 126 for value in data):
            raise CommandError("LIFE_RAW_PRINTABLE_ASCII")
    else:
        if payload is not None:
            raise CommandError("UNEXPECTED_PAYLOAD")
        value_text = ate_name[len("LIFE_SET_"):]
        digits = value_text[1:] if value_text[:1] in ("+", "-") else value_text
        if not digits or any(c not in "0123456789" for c in digits):
            raise CommandError("LIFE_VALUE_INTEGER")
        data = ("{:03X}".format(int(value_text)) + "00000").encode("ascii")
    return NF55CommandSpec(ate_name, "SL", data, 100, "SL")


def build_control_command(ate_name, payload=None):
    if ate_name.startswith("LIFE_SET_"):
        return build_life_command(ate_name, payload)

    if ate_name.startswith("PARAM_") and ate_name not in ("PARAM_SET", "PARAM_RESET"):
        return build_item_parameter_command(ate_name, payload)

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
    if spec.nf_cmd == "BC" and payload is not None:
        raise CommandError("UNEXPECTED_PAYLOAD")
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
