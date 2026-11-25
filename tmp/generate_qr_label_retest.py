import hashlib
import json
from pathlib import Path
import sys

sys.path[:0] = [str(Path.cwd()), str(Path(__file__).parent / 'qr_label_deps')]
from PIL import Image, ImageDraw, ImageFont
import qrcode
import zxingcpp
from src.qr_reader import decode_nf55g_label
from src.qr_write_session import serial_data_from_qr


folder = Path('docs/QR_Hardware_Integration_20261123_01/Production_Label_Retest_20261125')
folder.mkdir(exist_ok=False)
examples = (('A', 'US250A-CGXE-009491-101A1.2601000001'),
            ('B', 'US250A-CGXE-009491-101A032601000002'))
manifest = {}
font_path = Path(r'C:\Windows\Fonts\consola.ttf')
title_font = ImageFont.truetype(str(font_path), 23)
payload_font = ImageFont.truetype(str(font_path), 17)
for label, payload in examples:
    fields = decode_nf55g_label(payload)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=9, border=4)
    qr.add_data(payload)
    symbol = qr.make_image().convert('L')
    canvas = Image.new('L', (430, 395), 'white')
    canvas.paste(symbol, ((canvas.width - symbol.width) // 2, 47))
    draw = ImageDraw.Draw(canvas)
    draw.text((215, 27), f'TEST {label}  S/N {fields["serial"]}', fill=0, font=title_font, anchor='mm')
    draw.text((215, 368), payload, fill=0, font=payload_font, anchor='mm')
    path = folder / f'QR_Test_{label}_{fields["serial"]}.png'
    canvas.save(path, dpi=(300, 300))
    with Image.open(path) as saved:
        decoded = zxingcpp.read_barcodes(saved)
    assert len(decoded) == 1 and decoded[0].bytes == payload.encode('ascii'), decoded
    manifest[label] = {'file': path.name, 'payload': payload, 'fields': fields,
                       'ss_data_hex': serial_data_from_qr(payload).hex(),
                       'qr_version': qr.version, 'quiet_zone_modules': 4, 'error_correction': 'M',
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(folder / 'expected.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
print(folder)
