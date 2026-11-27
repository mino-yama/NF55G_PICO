# 校正値を送信する直前の共通保護。設定不良時は必須6点すべてを無送信にする。
import struct

try:
    import calibration_limits as settings
except Exception:  # ファイル欠落・構文不良でも治具の他機能は起動させる。
    settings = None

TARGETS = ('DISCHG_I', 'BATT_CHG', 'BATT_V')


def _decimal_key(text):
    # 10進入力をfloat化せず比較し、境界外の微小差が丸めで許可されるのを防ぐ。
    text = text.lower()
    sign = -1 if text.startswith('-') else 1
    text = text.lstrip('+-')
    parts = text.split('e')
    mantissa = parts[0]
    exponent = int(parts[1]) if len(parts) == 2 else 0
    fraction = len(mantissa.split('.')[1]) if '.' in mantissa else 0
    digits = mantissa.replace('.', '').lstrip('0').rstrip('0')
    if not digits:
        return (0, 0, '')
    full_digits = mantissa.replace('.', '').lstrip('0')
    return (sign, len(full_digits) + exponent - fraction, digits)


def _compare(left, right):
    a, b = _decimal_key(left), _decimal_key(right)
    if a[0] != b[0]:
        return 1 if a[0] > b[0] else -1
    if a[0] == 0:
        return 0
    size = max(len(a[2]), len(b[2]))
    x, y = (a[1], a[2].ljust(size, '0')), (b[1], b[2].ljust(size, '0'))
    return a[0] * ((x > y) - (x < y))


def _float32(value):
    return struct.unpack('>f', struct.pack('>f', value))[0]


def check_value(target, point, value_text, encoded):
    # TYPE3/5には未指定の規格を追加しない。既存の数値・診断条件は維持する。
    if target not in TARGETS:
        return None
    try:
        if not isinstance(settings.SETTINGS_REV, str) or not settings.SETTINGS_REV.strip():
            raise ValueError('revision')
        limits = {}
        for circuit in TARGETS:
            for slot in ('A', 'B'):
                lower = getattr(settings, circuit + '_' + slot + '_LOWER')
                upper = getattr(settings, circuit + '_' + slot + '_UPPER')
                if any(type(v) not in (int, float) or not -3.402823466e38 <= v <= 3.402823466e38
                       for v in (lower, upper)) or lower > upper:
                    raise ValueError('limits')
                if any(v != 0 and _float32(v) == 0 for v in (lower, upper)):
                    raise ValueError('underflow')
                limits[(circuit, slot)] = (lower, upper)
        lower, upper = limits[(target, point)]
    except (AttributeError, TypeError, ValueError, KeyError, OverflowError):
        return 'SETTINGS'
    # 原入力は厳密に境界包含。送信値は同じfloat32表現にした境界と比較する。
    # これにより35.2等の正確な境界入力を許可し、元の値が範囲外なら拒否する。
    value = struct.unpack('>f', encoded)[0]
    if (_compare(value_text, str(lower)) < 0 or _compare(value_text, str(upper)) > 0
            or not _float32(lower) <= value <= _float32(upper)):
        return 'RANGE'
    return None
