import zipfile,xml.etree.ElementTree as E,json,pathlib
from PIL import Image,ImageOps,ImageDraw
p="C:/Users/m_yamada/Desktop/NF55application仕様(FWU以外)改.xlsx"
out=pathlib.Path("tmp/mock_app_spec_images_20261126");out.mkdir(exist_ok=True)
with zipfile.ZipFile(p) as z:
 texts=[]
 for name in z.namelist():
  if name.startswith("xl/drawings/") and name.endswith(".xml"):
   tree=E.fromstring(z.read(name))
   words=[x.text for x in tree.iter() if x.tag.endswith("}t") and x.text]
   texts.append({"path":name,"text":words})
 for name in z.namelist():
  if name.startswith("xl/media/"): (out/pathlib.Path(name).name).write_bytes(z.read(name))
 (out/"drawing_text.json").write_text(json.dumps(texts,ensure_ascii=False,indent=2),encoding="utf-8")
 imgs=[]
 for p in sorted(out.glob("image*"),key=lambda p:int("".join(c for c in p.stem if c.isdigit()))):
  im=Image.open(p).convert("RGB"); im.thumbnail((380,230))
  card=Image.new("RGB",(400,260),"white");card.paste(im,((400-im.width)//2,25));ImageDraw.Draw(card).text((8,5),p.name,fill="black");imgs.append(card)
 for start in range(0,len(imgs),16):
  group=imgs[start:start+16]; canvas=Image.new("RGB",(1600,260*((len(group)+3)//4)),"#999999")
  for i,card in enumerate(group): canvas.paste(card,((i%4)*400,(i//4)*260))
  canvas.save(out/("contact_%02d.png"%start))
