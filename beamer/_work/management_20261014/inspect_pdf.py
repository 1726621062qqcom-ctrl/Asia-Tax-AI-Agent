from pathlib import Path
import json
import sys
import fitz
from PIL import Image

pdf = Path(sys.argv[1])
work = Path(__file__).resolve().parent
doc = fitz.open(pdf)
issues = []
pages = []
for index, page in enumerate(doc, 1):
    info = {"page": index, "lines": [], "font_sizes": set()}
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            text = "".join(s["text"] for s in line["spans"])
            bbox = fitz.Rect(line["bbox"])
            info["lines"].append({"text": text, "bbox": list(bbox)})
            info["font_sizes"].update(round(s["size"], 2) for s in line["spans"])
            if bbox.x0 < -0.5 or bbox.y0 < -0.5 or bbox.x1 > page.rect.width + 0.5 or bbox.y1 > page.rect.height + 0.5:
                issues.append({"page": index, "text": text, "bbox": list(bbox), "issue": "outside-page"})
            if "\ufffd" in text:
                issues.append({"page": index, "text": text, "issue": "replacement-character"})
    info["font_sizes"] = sorted(info["font_sizes"])
    pages.append(info)
report = {"pages": len(doc), "issues": issues, "page_details": pages}
(work / "pdf-inspection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
(work / "slides-text.txt").write_text("\n\n".join(f"PAGE {p['page']}\n" + "\n".join(x["text"] for x in p["lines"]) for p in pages), encoding="utf-8")
render = Path(sys.argv[2]) if len(sys.argv) > 2 else work / "after"
paths = sorted(render.glob("slide-*.png"))
if paths:
    width, height = 560, 315
    rows = (len(paths) + 3) // 4
    canvas = Image.new("RGB", (4 * width, rows * (height + 8)), "#e8e8e8")
    for i, path in enumerate(paths):
        with Image.open(path) as img:
            canvas.paste(img.resize((width, height)), ((i % 4) * width, (i // 4) * (height + 8)))
    canvas.save(work / "after-montage.png")
print(json.dumps({"pages": len(doc), "issues": issues}, ensure_ascii=False))
