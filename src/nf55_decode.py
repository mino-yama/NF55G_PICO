"""Pure NF55G response decoders.

Decode functions return dictionaries only. They never update cache and never
perform NF55G communication.
"""


class DecodeError(ValueError):
    pass


def _ascii(data):
    if isinstance(data, bytes):
        return data.decode("ascii")
    if isinstance(data, bytearray):
        return bytes(data).decode("ascii")
    return str(data)


def _require_len(text, length, label):
    if len(text) != length:
        raise DecodeError("{} length must be {}, got {}".format(label, length, len(text)))


def _num(text):
    try:
        return int(text, 16)
    except ValueError:
        raise DecodeError("not ASCII HEX: {}".format(text))


def _signed8(text):
    value = _num(text)
    if len(text) != 2 or value > 0xFF:
        raise DecodeError("signed8 field must be 2 ASCII HEX chars")
    if value & 0x80:
        return value - 0x100
    return value


def _fixed(text, divisor):
    return _num(text) / divisor


def _slice(text, start, length):
    return text[start : start + length]


def decode_time(data):
    text = _ascii(data)
    _require_len(text, 12, "TIME")
    year = "20" + text[0:2]
    return {
        "YEAR2": text[0:2],
        "MONTH2": text[2:4],
        "DAY2": text[4:6],
        "HOUR2": text[6:8],
        "MIN2": text[8:10],
        "SEC2": text[10:12],
        "DATE": year + text[2:6],
        "TIME": text[6:12],
        "DATETIME": year + text[2:6] + "_" + text[6:12],
    }


def decode_realtime(data):
    text = _ascii(data)
    _require_len(text, 50, "REALTIME")
    return {
        "VOUT12": _fixed(_slice(text, 0, 4), 1000),
        "IOUT12": _fixed(_slice(text, 4, 4), 1000),
        "BATT_VOLT": _num(_slice(text, 8, 4)),
        "CHG_VOLT": _num(_slice(text, 12, 4)),
        "CHG_CURR": _num(_slice(text, 16, 4)),
        "BATT_CURR": _num(_slice(text, 20, 4)),
        "BATT_SOC_WH": _signed8(_slice(text, 24, 2)),
        "BATT_SOC_MAH": _signed8(_slice(text, 26, 2)),
        "BATT_TEMP": _signed8(_slice(text, 28, 2)),
        "ADU_TEMP": _signed8(_slice(text, 30, 2)),
        "BBU_TEMP": _signed8(_slice(text, 32, 2)),
        "FAN_RPM": _num(_slice(text, 34, 4)),
        "FAN_LEVEL": _num(_slice(text, 38, 1)),
    }


def decode_off_period(data):
    text = _ascii(data)
    _require_len(text, 30, "OFF_PERIOD")
    return {
        "AC_OFF_HOUR": _fixed(_slice(text, 0, 4), 10),
        "PS_OFF_HOUR": _fixed(_slice(text, 4, 4), 10),
        "AVE_OFF_TEMP": _signed8(_slice(text, 8, 2)),
        "OFF_CHARGE_HOUR": _fixed(_slice(text, 10, 3), 10),
        "AVE_CHARGE_TEMP": _signed8(_slice(text, 13, 2)),
        "OFF_CHARGE": _num(_slice(text, 15, 3)),
        "OFF_BATT_DEG": _fixed(_slice(text, 18, 3), 10),
    }


def decode_life_calc(data):
    text = _ascii(data)
    _require_len(text, 20, "LIFE_CALC")
    return {
        "CHARGE_DATA": _num(_slice(text, 0, 1)),
        "CHARGE_END": _num(_slice(text, 1, 1)),
        "LIFE_BATT_CHARGE": _num(_slice(text, 2, 2)),
        "LIFE_BATT_TEMP": _signed8(_slice(text, 4, 2)),
        "LIFE_BATT_DEG": _fixed(_slice(text, 6, 3), 10),
    }


def decode_life_diag(data, prefix=""):
    text = _ascii(data)
    _require_len(text, 30, "LIFE_DIAG")
    p = prefix
    return {
        p + "MODE": _num(_slice(text, 0, 1)),
        p + "V1": _fixed(_slice(text, 1, 4), 1000),
        p + "V2": _fixed(_slice(text, 5, 4), 1000),
        p + "I1": _fixed(_slice(text, 9, 4), 1000),
        p + "I2": _fixed(_slice(text, 13, 4), 1000),
        p + "TEMP": _signed8(_slice(text, 17, 2)),
        p + "SOC": _signed8(_slice(text, 19, 2)),
        p + "IR": _num(_slice(text, 21, 3)),
    }


def decode_accumulated(data):
    text = _ascii(data)
    _require_len(text, 70, "ACCUMULATED")
    return {
        "TOTAL_ADU_TEMP": _num(_slice(text, 0, 6)),
        "TOTAL_ADU_HOUR": _num(_slice(text, 6, 4)),
        "AC_FAIL_COUNT": _num(_slice(text, 10, 3)),
        "AC_LOW_COUNT": _num(_slice(text, 13, 3)),
        "BACKUP_COUNT": _num(_slice(text, 16, 4)),
        "BATT_DEG_TOTAL": _fixed(_slice(text, 20, 3), 10),
        "TOTAL_BATT_HOUR": _num(_slice(text, 23, 4)),
        "BATT_DISCHARGE_COUNT": _num(_slice(text, 27, 4)),
        "BATT_CHARGE_COUNT": _num(_slice(text, 31, 3)),
        "BATT_TTL_DISCHARGE": _num(_slice(text, 34, 6)),
        "BATT_TTL_CHARGE": _num(_slice(text, 40, 6)),
        "TOTAL_BATT_TEMP": _num(_slice(text, 46, 6)),
        "BATT_TEMP_AVE": _signed8(_slice(text, 52, 2)),
        "BATT_TEMP_MAX": _signed8(_slice(text, 54, 2)),
        "BATT_TEMP_MIN": _signed8(_slice(text, 56, 2)),
    }


def decode_manufacturing(data):
    text = _ascii(data)
    _require_len(text, 50, "MANUFACTURING")
    return {
        "FW_REV": _slice(text, 0, 6),
        "UNIT_REV": _slice(text, 6, 4),
        "UNIT_LOT": _slice(text, 10, 4),
        "UNIT_SERIAL": _slice(text, 14, 6),
        "ADU_REV": _slice(text, 20, 4),
        "ADU_LOT": _slice(text, 24, 4),
        "ADU_SERIAL": _slice(text, 28, 6),
        "BBU_REV": _slice(text, 34, 4),
        "BBU_LOT": _slice(text, 38, 4),
        "BBU_SERIAL": _slice(text, 42, 6),
    }


def decode_parameter(data):
    text = _ascii(data)
    _require_len(text, 50, "PARAMETER")
    return {
        "PS_ON_BACKUP": _num(_slice(text, 0, 1)),
        "AC_LINK": _num(_slice(text, 1, 1)),
        "AUTO_CHARGE": _num(_slice(text, 2, 1)),
        "EVENT_ENABLE": _num(_slice(text, 3, 1)),
        "MAX_BACKUP_TIME": _num(_slice(text, 4, 1)),
        "MIN_BACKUP_TIME": _num(_slice(text, 5, 2)),
        "RESTART_TIME": _num(_slice(text, 7, 2)),
        "BATT_LOW_THD": _num(_slice(text, 9, 2)),
        "BATT_CAP_MAH": _num(_slice(text, 11, 4)),
        "BATT_CAP_WH": _num(_slice(text, 15, 2)),
        "CHG_IR_THD": _num(_slice(text, 17, 3)),
        "BATT_WNG_THD": _num(_slice(text, 20, 2)),
        "BATT_ALM_THD": _num(_slice(text, 22, 2)),
        "ADU_TEMP_THD": _num(_slice(text, 24, 2)),
        "BBU_TEMP_THD": _num(_slice(text, 26, 2)),
        "FAN_WNG_THD": _num(_slice(text, 28, 4)),
    }


STATUS_BITS = (
    ("R0_3", "R0_2", "PS_ON", "BURST_ON"),
    ("BURST", "PS_OFF_CHARGE", "RESTART_READY", "BACKUP_READY"),
    ("CHARGE_READY", "BATT_CHECK_RUN", "CHARGE_OFF_STATUS", "CHARGE_ON_STATUS"),
    ("R3_3", "R3_2", "BATT_ON", "BATT_LOW"),
    ("R4_3", "S_CHARGE_ON", "CHARGE_OK", "CHARGER_ON"),
    ("R5_3", "FAN_WNG", "ADU_TEMP_WNG", "R5_0"),
    ("R6_3", "OC_OFF_H", "PFC_OV", "FAN_FAIL"),
    ("R7_3", "R7_2", "R7_1", "BBU_TEMP_WNG"),
    ("BBU_FAIL", "CHG_LV", "CHG_OV", "CHG_OC"),
    ("R9_3", "R9_2", "R9_1", "BATT_TEMP_WNG"),
    ("R10_3", "BATT_TEMP_ALM", "BATT_LV", "BATT_OV"),
    ("BATT_LIFE", "BATT_MCN", "BATT_P_FAIL", "BATT_DCN"),
    ("12V_OV", "12V_LV", "12V_OC", "12V_OC_OFF_L"),
    ("R13_3", "R13_2", "R13_1", "R13_0"),
    ("R14_3", "R14_2", "R14_1", "R14_0"),
)


def decode_status(data):
    text = _ascii(data)
    _require_len(text, 15, "STATUS")
    decoded = {}
    for index, char in enumerate(text):
        value = _num(char)
        names = STATUS_BITS[index]
        decoded[names[0]] = bool(value & 0x8)
        decoded[names[1]] = bool(value & 0x4)
        decoded[names[2]] = bool(value & 0x2)
        decoded[names[3]] = bool(value & 0x1)
    return decoded


def decode_d0(data):
    text = _ascii(data)
    _require_len(text, 327, "D0")
    result = {}
    result.update(decode_time(_slice(text, 0, 12)))
    result.update(decode_realtime(_slice(text, 12, 50)))
    result.update(decode_off_period(_slice(text, 62, 30)))
    result.update(decode_life_calc(_slice(text, 92, 20)))
    result.update(decode_life_diag(_slice(text, 112, 30)))
    result.update(decode_accumulated(_slice(text, 142, 70)))
    result["MANUFACTURING_RAW"] = _slice(text, 212, 50)
    result["PARAMETER_RAW"] = _slice(text, 262, 50)
    result["STATUS_RAW"] = _slice(text, 312, 15)
    return result


def decode_d1(data):
    return decode_status(data)


def decode_d2(data):
    return decode_off_period(data)


def decode_d3(data):
    text = _ascii(data)
    _require_len(text, 21, "D3")
    result = decode_life_calc(_slice(text, 0, 20))
    result["EVENT_LOST"] = _num(_slice(text, 20, 1))
    return result


def decode_d4(data):
    text = _ascii(data)
    _require_len(text, 212, "D4")
    result = {}
    result.update(decode_time(_slice(text, 0, 12)))
    result.update(decode_realtime(_slice(text, 12, 50)))
    result.update(decode_life_diag(_slice(text, 62, 30)))
    result.update(decode_accumulated(_slice(text, 92, 70)))
    result.update(decode_manufacturing(_slice(text, 162, 50)))
    return result


def decode_d5(data):
    text = _ascii(data)
    _require_len(text, 100, "D5")
    result = {}
    result.update(decode_manufacturing(_slice(text, 0, 50)))
    result.update(decode_parameter(_slice(text, 50, 50)))
    return result


def decode_bc(data):
    return decode_life_diag(data, prefix="BC_")


def decode_eb(data):
    text = _ascii(data)
    _require_len(text, 20, "EB")
    return {
        "CURRENT_RAW": _slice(text, 0, 10),
        "CHANGE_RAW": _slice(text, 10, 10),
    }


def decode_log_block(data, expected_start=None):
    text = _ascii(data)
    _require_len(text, 82, "EL/OL")
    start_no = _num(_slice(text, 0, 2))
    if expected_start is not None and start_no != expected_start:
        raise DecodeError("log START_NO mismatch")
    records = []
    offset = 2
    for _ in range(8):
        rec = _slice(text, offset, 10)
        datehour = rec[0:8]
        event_id = _num(rec[8:10])
        records.append({"DATEHOUR": datehour, "ID": event_id})
        offset += 10
    return {"START_NO": start_no, "RECORDS": records}


def decode_el(data, expected_start=None):
    return decode_log_block(data, expected_start=expected_start)


def decode_ol(data, expected_start=None):
    return decode_log_block(data, expected_start=expected_start)


def decode_ar(data):
    text = _ascii(data)
    _require_len(text, 140, "AR")
    systems = ("DISCHG_I", "BATT_V", "ACDC12V_V", "BATT_CHG", "12VOUT_V")
    result = {}
    offset = 0
    for system in systems:
        for point in ("P1", "P2"):
            adc = _slice(text, offset, 6)
            ref = _slice(text, offset + 6, 8)
            result["AR_{}_{}_ADC".format(system, point)] = _num(adc)
            result["AR_{}_{}_REF_RAW".format(system, point)] = ref
            offset += 14
    return result


def decode_fd(data):
    text = _ascii(data)
    _require_len(text, 64, "FD")
    for char in text:
        _num(char)
    return {"FD_RAW": text}
