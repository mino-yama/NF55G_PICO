"""PCで生HEXログを再生する。Pico・NF55Gへ接続しない。"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from ch9350_decode import KeyboardDecoder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="RX ... hex=...形式、または1行1HEXのテキスト")
    args = parser.parse_args()
    decoder = KeyboardDecoder()
    failed = False
    with args.log.open(encoding="utf-8-sig") as source:
        for number, line in enumerate(source, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("LOSS "):
                failed = True
                decoder.reset()
                print(json.dumps({"type": "error", "reason": "CAPTURE_LOSS", "line": number}))
                # 欠落後に正常な行として解釈しない。再収集する。
                return 1
            if line.startswith("CAPTURE_"):
                continue
            if line.startswith("RX ") and "hex=" in line:
                line = line.split("hex=", 1)[1]
            try:
                data = bytes.fromhex(line)
            except ValueError:
                print("Invalid HEX at line %d" % number, file=sys.stderr)
                return 2
            for event in decoder.feed(data):
                print(json.dumps(event, ensure_ascii=False))
                if event["type"] in ("error", "line_error"):
                    failed = True
    for event in decoder.finish():
        print(json.dumps(event))
        failed = True
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
