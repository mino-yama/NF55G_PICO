"""2026-11-16 DMM Host調査用の原典を別フォルダへ保存しhashを記録する。"""

import concurrent.futures
import hashlib
import json
import sys
from pathlib import Path
import urllib.error
import urllib.request

DEST = Path(__file__).resolve().parents[1] / "reference/USB_Host_SubMCU_20261116_RP2350_USB_A"
SOURCES = [
    ("SwitchScience_10275.html", "https://www.switch-science.com/products/10275"),
    ("Waveshare_Wiki.html", "https://www.waveshare.com/wiki/RP2350-USB-A"),
    ("RP2350-USB-A.pdf", "https://files.waveshare.com/wiki/RP2350-USB-A/RP2350-USB-A.pdf"),
    ("RP2350-USB-A.zip", "https://files.waveshare.com/wiki/RP2350-USB-A/RP2350-USB-A.zip"),
    ("TinyUSB_CDC.html", "https://docs.tinyusb.org/en/latest/reference/class/cdc.html"),
    ("TinyUSB_Host_CDC_Example.html", "https://docs.tinyusb.org/en/latest/examples/host/cdc_msc_hid.html"),
    ("Waveshare_R13_Location.png", "https://www.waveshare.com/w/upload/c/ca/RP2350-USB-A-R13.png"),
    ("Waveshare_Pinout.jpg", "https://www.waveshare.com/w/upload/6/64/680px-RP2350-USB-A-details-6.jpg"),
    ("Hardware-design-with-rp2350.pdf", "https://files.waveshare.com/wiki/common/Hardware-design-with-rp2350.pdf"),
    ("Raspberry-pi-pico-2-c-sdk.pdf", "https://files.waveshare.com/wiki/common/Raspberry-pi-pico-2-c-sdk.pdf"),
]


def fetch(source):
    name, url = source
    path = DEST / name
    entry = {"file": name, "url": url}
    if path.exists():
        entry["status"] = "existing_preserved"
        data = path.read_bytes()
    else:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                data = response.read()
                entry["http_status"] = response.status
                entry["content_type"] = response.headers.get("Content-Type")
                entry["final_url"] = response.url
            if name.endswith(".pdf") and not data.startswith(b"%PDF"):
                raise ValueError("PDF signature missing")
            if name.endswith(".zip") and not data.startswith(b"PK"):
                raise ValueError("ZIP signature missing")
            path.write_bytes(data)
            entry["status"] = "downloaded"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            entry.update(status="failed", error=str(exc))
            return entry
    entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return entry


if __name__ == "__main__":
    DEST.mkdir(parents=True, exist_ok=True)
    selected = [source for source in SOURCES if not sys.argv[1:] or source[0] in sys.argv[1:]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(fetch, selected))
    manifest = {"retrieved_date_jst": "2026-11-16", "purpose": "7355 CDC Host on RP2350-USB-A", "files": results}
    output = DEST / "download_manifest.json"
    attempt = 0
    while output.exists():
        attempt += 1
        output = DEST / ("download_manifest_retry.json" if attempt == 1 else "download_manifest_retry_%02d.json" % attempt)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(result["file"], result["status"], result.get("bytes", result.get("error")))
