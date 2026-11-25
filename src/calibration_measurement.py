# DMM測定値を対象・A/B点・試行・取得要求に結び付けて保持するRAM専用の基盤。
# 電流校正は50A/50mVシャントのmV値を同じ数値のA値へ変換する。
# CDC応答の完成判定・ATE判定・AD送信は呼出し側の責務で、自動実行しない。

"""Internal measurement cache; not an ATE command or CDC wire protocol."""

CALIBRATION_TARGETS = ("DISCHG_I", "BATT_CHG", "BATT_V")
CALIBRATION_POINTS = ("A", "B")


class MeasurementError(ValueError):
    pass


def _decimal_text(value):
    # floatに変換せず元の桁を保持する。OL/NaN/Infや複数値は採用しない。
    if not isinstance(value, str) or not value:
        return False
    parts = value.lower().split("e")
    if len(parts) > 2:
        return False
    mantissa = parts[0]
    if mantissa[:1] in ("+", "-"):
        mantissa = mantissa[1:]
    digits = mantissa.replace(".", "", 1)
    if not digits or any(c not in "0123456789" for c in digits):
        return False
    if len(parts) == 2:
        exponent = parts[1]
        if exponent[:1] in ("+", "-"):
            exponent = exponent[1:]
        if not exponent or any(c not in "0123456789" for c in exponent):
            return False
    return True


class CalibrationMeasurements:
    """Six slots, with opaque acquisition tokens scoped to one active trial.

    complete() accepts a complete, decoded single measurement from a future
    DMM adapter, never arbitrary SCPI replies. Numeric syntax is checked here;
    instrument overrange limits remain adapter contracts. get_calibration()
    applies the user-specified 50 A / 50 mV conversion on the parent Pico.
    No transport, clock, logger, product judgement or NF55G access is performed.
    """

    def __init__(self):
        self._generation = 0
        self._sequence = 0
        self._active = False
        self._pending = None
        self._values = {}

    def start_trial(self):
        # 同じ外部試行名でも世代を更新し、前試行の遅着を識別する。
        self.end_trial()
        self._generation += 1
        self._active = True

    def end_trial(self):
        self._active = False
        self._pending = None
        self._values.clear()

    def begin(self, target, point):
        if not self._active:
            raise MeasurementError("NO_ACTIVE_TRIAL")
        if target not in CALIBRATION_TARGETS or point not in CALIBRATION_POINTS:
            raise MeasurementError("MEASUREMENT_TARGET")
        if self._pending is not None:
            raise MeasurementError("MEASUREMENT_BUSY")
        # 取得前に旧値を破棄する。失敗・切断・取消後も旧値へ戻さない。
        self._values.pop((target, point), None)
        self._sequence += 1
        token = (self._generation, self._sequence, target, point)
        self._pending = token
        return token

    def complete(self, token, raw, value_text, unit):
        if not self._active or self._pending is None or token != self._pending:
            return False
        # 完成応答の検証失敗も要求の終了とし、同じ要求への後続応答で復活させない。
        self._pending = None
        if not isinstance(raw, (str, bytes)) or not raw:
            raise MeasurementError("MEASUREMENT_RAW")
        try:
            if isinstance(raw, bytes):
                raw.decode("ascii")
            else:
                raw.encode("ascii")
        except UnicodeError:
            raise MeasurementError("MEASUREMENT_RAW")
        if not _decimal_text(value_text) or unit not in ("V", "mV", "A"):
            raise MeasurementError("MEASUREMENT_VALUE")
        self._values[(token[2], token[3])] = {
            "token": token, "target": token[2], "point": token[3],
            "raw": raw, "value_text": value_text, "unit": unit,
        }
        return True

    def fail(self, token):
        # timeout/切断/取消の通知も要求照合し、別取得の結果を消さない。
        if self._pending is None or token != self._pending:
            return False
        self._pending = None
        return True

    def pending_matches(self, token):
        # 試行終了/再START後に、取得側が残りの機器要求を出さないための照合口。
        return self._active and self._pending is not None and token == self._pending

    def get(self, token):
        if not self._active:
            raise MeasurementError("MEASUREMENT_INVALID")
        for value in self._values.values():
            if token == value["token"]:
                # 呼出し側の変更でATE確認済み値が置き換わることを防ぐ。
                return dict(value)
        raise MeasurementError("MEASUREMENT_INVALID")

    def latest_token(self, target, point):
        # ATEは取得IDを指定せず、現試行の指定回路・補正点だけを参照できる。
        value = self._values.get((target, point)) if self._active else None
        if value is None:
            raise MeasurementError("MEASUREMENT_INVALID")
        return value['token']

    def discard(self, token):
        # 書込み完了/成否不明時の失効口。送信bufferへの投入時には呼ばない。
        for key, value in self._values.items():
            if token == value["token"]:
                del self._values[key]
                return True
        return False

    def get_calibration(self, token):
        """Return a calibration candidate; no ATE approval or AD transmission.

        Current channels require an explicitly decoded mV measurement. Never
        relabel an instrument's V response as mV. The adapter must establish
        the response unit before completing the acquisition.
        """
        value = self.get(token)
        expected_unit = "V" if value["target"] == "BATT_V" else "mV"
        if value["unit"] != expected_unit:
            raise MeasurementError("CALIBRATION_UNIT")
        value["measurement_value_text"] = value["value_text"]
        value["measurement_unit"] = value["unit"]
        # 50mV/50A=1mΩ。I[A]=U[mV]なので数値文字列を保持し、丸めを加えない。
        value["unit"] = "V" if value["target"] == "BATT_V" else "A"
        return value
