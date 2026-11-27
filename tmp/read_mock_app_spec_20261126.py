import zipfile, xml.etree.ElementTree as E, json
p="C:/Users/m_yamada/Desktop/NF55application仕様(FWU以外)改.xlsx"
n={"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
with zipfile.ZipFile(p) as z:
 ss=[]
 if "xl/sharedStrings.xml" in z.namelist():
  ss=["".join(x.itertext()) for x in E.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si",n)]
 wb=E.fromstring(z.read("xl/workbook.xml"))
 rels={x.get("Id"):x.get("Target") for x in E.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
 result=[]
 for sh in wb.find("s:sheets",n):
  target=rels[sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")]
  path=target.lstrip("/") if target.startswith("/") else "xl/"+target
  tree=E.fromstring(z.read(path)); cells=[]
  for c in tree.findall(".//s:c",n):
   v=c.find("s:v",n); text=v.text if v is not None else ""
   if c.get("t")=="s": text=ss[int(text)]
   elif c.get("t")=="inlineStr": text="".join(c.find("s:is",n).itertext())
   if text: cells.append({"cell":c.get("r"),"text":text,"formula":c.findtext("s:f",default="",namespaces=n)})
  result.append({"sheet":sh.get("name"),"path":path,"cells":cells})
 print(json.dumps([{ "sheet":x["sheet"],"path":x["path"],"count":len(x["cells"]),"hits":[c for c in x["cells"] if any(k in c["text"] for k in ("AR","REF","ADC","補正","校正","float","Float","浮動"))]} for x in result],ensure_ascii=False,indent=2))
 with open("tmp/mock_app_workbook_cells_20261126.json","w",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2)
 print("MEDIA",[x for x in z.namelist() if x.startswith("xl/media/")])
