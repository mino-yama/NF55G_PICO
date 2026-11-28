# LoggerとSDの命名・番号抽出を共通化する。日時のない名前は時刻として扱わない。


def _digits(text):
    return bool(text) and all('0' <= c <= '9' for c in text)


def log_identity(name):
    """認識できるCSVは(kind, number)、対象外はNone。日時CONTのnumberは0。"""
    if not isinstance(name, str) or len(name) > 255:
        return None
    if len(name) > 7 and name[6] == '_' and _digits(name[:6]):
        name = name[7:]
    if not name.endswith('.csv'):
        return None
    stem = name[:-4]
    if stem.startswith('NO_RTC_'):
        kind, number = stem[7:8], stem[8:]
        if kind in ('T', 'C') and len(number) >= 6 and _digits(number):
            return kind, int(number)
        return None
    if len(stem) < 15 or stem[8] != '_' or not _digits(stem[:8] + stem[9:15]):
        return None
    if len(stem) == 15:
        return 'C', 0
    if stem[15:17] == '_T' and len(stem[17:]) >= 6 and _digits(stem[17:]):
        return 'T', int(stem[17:])
    return None
