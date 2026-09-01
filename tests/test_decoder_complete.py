import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.nf55_decode import (
    DecodeError,
    decode_ar,
    decode_bc,
    decode_d0,
    decode_d1,
    decode_d2,
    decode_d3,
    decode_d4,
    decode_d5,
    decode_el,
    decode_fd,
    decode_manufacturing,
    decode_ol,
    decode_parameter,
    decode_status,
)


def realtime_payload():
    return (
        "2EE0"  # VOUT12 12.000 V
        "03E8"  # IOUT12 1.000 A
        "1770"  # BATT_VOLT
        "1800"  # CHG_VOLT
        "0064"  # CHG_CURR
        "0010"  # BATT_CURR
        "64"  # BATT_SOC_WH
        "FE"  # BATT_SOC_MAH -2
        "19"  # BATT_TEMP 25
        "F6"  # ADU_TEMP -10
        "00"  # BBU_TEMP 0
        "04D2"  # FAN_RPM 1234
        "5"  # FAN_LEVEL
        + "0" * 11
    )


def off_period_payload():
    return "000A" "0014" "F6" "00F" "19" "064" "07B" + "0" * 9


def life_calc_payload():
    return "1" "0" "64" "F6" "07B" + "0" * 11


def life_diag_payload():
    return "3" "2EE0" "2AF8" "0064" "0032" "19" "FE" "07B" + "0" * 6


def accumulated_payload():
    return (
        "000001"
        "0002"
        "003"
        "004"
        "0005"
        "07B"
        "0006"
        "0007"
        "008"
        "000009"
        "00000A"
        "00000B"
        "F6"
        "19"
        "80"
        + "0" * 12
    )


def manufacturing_payload():
    return (
        "FW0001"
        "UR01"
        "UL02"
        "US0003"
        "AR04"
        "AL05"
        "AS0006"
        "BR07"
        "BL08"
        "BS0009"
        "00"
    )


def parameter_payload():
    return (
        "1"
        "0"
        "1"
        "1"
        "9"
        "1E"
        "3C"
        "50"
        "1388"
        "64"
        "07B"
        "28"
        "32"
        "3C"
        "46"
        "04D2"
        + "0" * 18
    )


def d0_payload():
    return (
        "260901123456"
        + realtime_payload()
        + off_period_payload()
        + life_calc_payload()
        + life_diag_payload()
        + accumulated_payload()
        + manufacturing_payload()
        + parameter_payload()
        + "308000000000000"
    )


GOLDEN_D0_TIME = {
    "YEAR2": "26",
    "MONTH2": "09",
    "DAY2": "01",
    "HOUR2": "12",
    "MIN2": "34",
    "SEC2": "56",
    "DATE": "20260901",
    "TIME": "123456",
    "DATETIME": "20260901_123456",
}

GOLDEN_D0_REALTIME = {
    "VOUT12": 12.0,
    "IOUT12": 1.0,
    "BATT_VOLT": 6000,
    "CHG_VOLT": 6144,
    "CHG_CURR": 100,
    "BATT_CURR": 16,
    "BATT_SOC_WH": 100,
    "BATT_SOC_MAH": -2,
    "BATT_TEMP": 25,
    "ADU_TEMP": -10,
    "BBU_TEMP": 0,
    "FAN_RPM": 1234,
    "FAN_LEVEL": 5,
}

GOLDEN_D0_OFF = {
    "AC_OFF_HOUR": 1.0,
    "PS_OFF_HOUR": 2.0,
    "AVE_OFF_TEMP": -10,
    "OFF_CHARGE_HOUR": 1.5,
    "AVE_CHARGE_TEMP": 25,
    "OFF_CHARGE": 100,
    "OFF_BATT_DEG": 12.3,
}

GOLDEN_D0_LIFE_CALC = {
    "CHARGE_DATA": 1,
    "CHARGE_END": 0,
    "LIFE_BATT_CHARGE": 100,
    "LIFE_BATT_TEMP": -10,
    "LIFE_BATT_DEG": 12.3,
}

GOLDEN_D0_LIFE_DIAG = {
    "MODE": 3,
    "V1": 12.0,
    "V2": 11.0,
    "I1": 0.1,
    "I2": 0.05,
    "TEMP": 25,
    "SOC": -2,
    "IR": 123,
}

GOLDEN_D0_ACCUMULATED = {
    "TOTAL_ADU_TEMP": 1,
    "TOTAL_ADU_HOUR": 2,
    "AC_FAIL_COUNT": 3,
    "AC_LOW_COUNT": 4,
    "BACKUP_COUNT": 5,
    "BATT_DEG_TOTAL": 12.3,
    "TOTAL_BATT_HOUR": 6,
    "BATT_DISCHARGE_COUNT": 7,
    "BATT_CHARGE_COUNT": 8,
    "BATT_TTL_DISCHARGE": 9,
    "BATT_TTL_CHARGE": 10,
    "TOTAL_BATT_TEMP": 11,
    "BATT_TEMP_AVE": -10,
    "BATT_TEMP_MAX": 25,
    "BATT_TEMP_MIN": -128,
}

GOLDEN_D0_MFG = {
    "FW_REV": "FW0001",
    "UNIT_REV": "UR01",
    "UNIT_LOT": "UL02",
    "UNIT_SERIAL": "US0003",
    "ADU_REV": "AR04",
    "ADU_LOT": "AL05",
    "ADU_SERIAL": "AS0006",
    "BBU_REV": "BR07",
    "BBU_LOT": "BL08",
    "BBU_SERIAL": "BS0009",
}

GOLDEN_D0_PARAM = {
    "PS_ON_BACKUP": 1,
    "AC_LINK": 0,
    "AUTO_CHARGE": 1,
    "EVENT_ENABLE": 1,
    "MAX_BACKUP_TIME": 9,
    "MIN_BACKUP_TIME": 30,
    "RESTART_TIME": 60,
    "BATT_LOW_THD": 80,
    "BATT_CAP_MAH": 5000,
    "BATT_CAP_WH": 100,
    "CHG_IR_THD": 123,
    "BATT_WNG_THD": 40,
    "BATT_ALM_THD": 50,
    "ADU_TEMP_THD": 60,
    "BBU_TEMP_THD": 70,
    "FAN_WNG_THD": 1234,
}

GOLDEN_D0_STATUS_TRUE = ("PS_ON", "BURST_ON", "CHARGE_READY")


class DecoderCompleteTests(unittest.TestCase):
    def test_decode_d0_327_chars(self):
        decoded = decode_d0(d0_payload())
        self.assertEqual(len(d0_payload()), 327)
        self.assertEqual(decoded["MANUFACTURING_RAW"], manufacturing_payload())
        self.assertEqual(decoded["PARAMETER_RAW"], parameter_payload())
        self.assertEqual(decoded["STATUS_RAW"], "308000000000000")
        self.assertNotIn("FW_REV", decoded)
        self.assertNotIn("PS_ON", decoded)

    def test_decode_d0_all_sections_against_golden_data(self):
        decoded = decode_d0(d0_payload())

        for section in (
            GOLDEN_D0_TIME,
            GOLDEN_D0_REALTIME,
            GOLDEN_D0_OFF,
            GOLDEN_D0_LIFE_CALC,
            GOLDEN_D0_LIFE_DIAG,
            GOLDEN_D0_ACCUMULATED,
        ):
            for key, expected in section.items():
                with self.subTest(section_key=key):
                    self.assertEqual(decoded[key], expected)

        self.assertEqual(decoded["MANUFACTURING_RAW"], manufacturing_payload())
        self.assertEqual(decode_manufacturing(decoded["MANUFACTURING_RAW"]), GOLDEN_D0_MFG)

        self.assertEqual(decoded["PARAMETER_RAW"], parameter_payload())
        self.assertEqual(decode_parameter(decoded["PARAMETER_RAW"]), GOLDEN_D0_PARAM)

        self.assertEqual(decoded["STATUS_RAW"], "308000000000000")
        status = decode_status(decoded["STATUS_RAW"])
        for key, value in status.items():
            with self.subTest(status_key=key):
                self.assertEqual(value, key in GOLDEN_D0_STATUS_TRUE)

    def test_decode_d1_15_chars(self):
        decoded = decode_d1("FFFFFFFFFFFFFFF")
        self.assertEqual(len(decoded), 60)
        self.assertTrue(decoded["PS_ON"])
        self.assertTrue(decoded["12V_OC_OFF_L"])
        self.assertTrue(decoded["BATT_TEMP_ALM"])

    def test_decode_d2_30_chars(self):
        decoded = decode_d2(off_period_payload())
        self.assertEqual(decoded["AC_OFF_HOUR"], 1.0)
        self.assertEqual(decoded["PS_OFF_HOUR"], 2.0)
        self.assertEqual(decoded["AVE_OFF_TEMP"], -10)
        self.assertEqual(decoded["OFF_CHARGE_HOUR"], 1.5)
        self.assertEqual(decoded["OFF_CHARGE"], 100)
        self.assertEqual(decoded["OFF_BATT_DEG"], 12.3)

    def test_decode_d3_21_chars(self):
        decoded = decode_d3(life_calc_payload() + "A")
        self.assertEqual(decoded["CHARGE_DATA"], 1)
        self.assertEqual(decoded["LIFE_BATT_CHARGE"], 100)
        self.assertEqual(decoded["LIFE_BATT_DEG"], 12.3)
        self.assertEqual(decoded["EVENT_LOST"], 10)

    def test_decode_d4_212_chars(self):
        payload = (
            "260901123456"
            + realtime_payload()
            + life_diag_payload()
            + accumulated_payload()
            + manufacturing_payload()
        )
        decoded = decode_d4(payload)
        self.assertEqual(len(payload), 212)
        self.assertEqual(decoded["DATETIME"], "20260901_123456")
        self.assertEqual(decoded["FAN_RPM"], 1234)
        self.assertEqual(decoded["IR"], 123)
        self.assertEqual(decoded["FW_REV"], "FW0001")
        self.assertEqual(decoded["BBU_SERIAL"], "BS0009")

    def test_decode_d5_100_chars(self):
        payload = manufacturing_payload() + parameter_payload()
        decoded = decode_d5(payload)
        self.assertEqual(len(payload), 100)
        self.assertEqual(decoded["UNIT_SERIAL"], "US0003")
        self.assertEqual(decoded["PS_ON_BACKUP"], 1)
        self.assertEqual(decoded["MIN_BACKUP_TIME"], 30)
        self.assertEqual(decoded["FAN_WNG_THD"], 1234)

    def test_decode_bc_30_chars(self):
        decoded = decode_bc(life_diag_payload())
        self.assertEqual(decoded["BC_MODE"], 3)
        self.assertEqual(decoded["BC_V1"], 12.0)
        self.assertEqual(decoded["BC_SOC"], -2)
        self.assertEqual(decoded["BC_IR"], 123)

    def test_decode_ar_140_chars(self):
        point = "00000A" "12345678"
        payload = point * 10
        decoded = decode_ar(payload)
        self.assertEqual(len(payload), 140)
        self.assertEqual(decoded["AR_DISCHG_I_P1_ADC"], 10)
        self.assertEqual(decoded["AR_DISCHG_I_P1_REF_RAW"], "12345678")
        self.assertEqual(decoded["AR_12VOUT_V_P2_ADC"], 10)
        self.assertEqual(decoded["AR_12VOUT_V_P2_REF_RAW"], "12345678")

    def test_decode_el_ol_82_chars(self):
        record = "26090112" "09"
        payload = "01" + record * 8
        decoded_el = decode_el(payload, expected_start=1)
        decoded_ol = decode_ol(payload, expected_start=1)
        self.assertEqual(len(payload), 82)
        self.assertEqual(decoded_el["START_NO"], 1)
        self.assertEqual(decoded_el["RECORDS"][0]["DATEHOUR"], "26090112")
        self.assertEqual(decoded_el["RECORDS"][0]["ID"], 9)
        self.assertEqual(decoded_ol["RECORDS"][7]["ID"], 9)

    def test_decode_fd_64_chars(self):
        payload = "0123456789ABCDEF" * 4
        decoded = decode_fd(payload)
        self.assertEqual(len(payload), 64)
        self.assertEqual(decoded["FD_RAW"], payload)

    def test_all_top_level_decoders_reject_wrong_lengths(self):
        cases = (
            (decode_d0, "0" * 326),
            (decode_d0, "0" * 328),
            (decode_d1, "0" * 14),
            (decode_d1, "0" * 16),
            (decode_d2, "0" * 29),
            (decode_d2, "0" * 31),
            (decode_d3, "0" * 20),
            (decode_d3, "0" * 22),
            (decode_d4, "0" * 211),
            (decode_d4, "0" * 213),
            (decode_d5, "0" * 99),
            (decode_d5, "0" * 101),
            (decode_bc, "0" * 29),
            (decode_bc, "0" * 31),
            (decode_ar, "0" * 139),
            (decode_ar, "0" * 141),
            (decode_el, "0" * 81),
            (decode_el, "0" * 83),
            (decode_ol, "0" * 81),
            (decode_ol, "0" * 83),
            (decode_fd, "0" * 63),
            (decode_fd, "0" * 65),
        )
        for decoder, payload in cases:
            with self.subTest(decoder=decoder.__name__, length=len(payload)):
                with self.assertRaises(DecodeError):
                    decoder(payload)

    def test_hex_decoders_reject_non_hex_payloads(self):
        with self.assertRaises(DecodeError):
            decode_d1("G" + "0" * 14)
        with self.assertRaises(DecodeError):
            decode_fd("Z" + "0" * 63)
        with self.assertRaises(DecodeError):
            decode_ar("Z" + "0" * 139)

    def test_log_start_must_match_requested_block(self):
        payload = "01" + ("00000000FF" * 8)
        decoded = decode_el(payload, expected_start=1)
        self.assertEqual(decoded["RECORDS"][0]["ID"], 255)
        with self.assertRaises(DecodeError):
            decode_el(payload, expected_start=9)


if __name__ == "__main__":
    unittest.main()
