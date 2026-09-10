"""NF55G command definitions and wire DATA builders."""

try:
    from . import config
except ImportError:  # pragma: no cover
    import config


class CommandError(ValueError):
    pass


# Explicit allowlists from ATE_Command_Master sections 2, 5, and 6.
# Reserved decoder fields are deliberately not ATE commands.
READ_REFRESH_COMMANDS = {
    "STATUS_REFRESH": ("D1", "STATUS", 100, 15),
    "INFO_REFRESH": ("D5", "INFO", 100, 100),
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
for _cache, _fields in (("STATUS", STATUS_QUERY_FIELDS), ("INFO", INFO_QUERY_FIELDS)):
    for _field in _fields:
        CACHE_QUERY_COMMANDS[_field + "?"] = (_cache, _field)


class NF55CommandSpec:
    __slots__ = ("ate_name", "nf_cmd", "data", "t2_ms", "cache_action")

    def __init__(self, ate_name, nf_cmd, data=b"", t2_ms=None, cache_action=None):
        self.ate_name = ate_name
        self.nf_cmd = nf_cmd
        self.data = data
        self.t2_ms = config.T2_DEFAULT_MS if t2_ms is None else int(t2_ms)
        self.cache_action = cache_action or nf_cmd


CONTROL_COMMANDS = {
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
