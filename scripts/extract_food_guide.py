"""Extract food pantries / meals from the Rutgers "Middlesex County Food Pantries and Meals" PDF.

Run from the repo root:  python scripts/extract_food_guide.py
Input:  data/raw/services/Middlesex-County-Food-Guide-2.pdf
        (download: https://sites.rutgers.edu/food-waste/wp-content/uploads/sites/667/2025/10/Middlesex-County-Food-Guide-2.pdf)
Output: data/manual/food_guide_extracted.csv  -> reviewed by hand, then copied into
        data/manual/services.csv (category = food)

The PDF is laid out in 3 columns; each entry is: name (bold), address (italic,
"..., City"), description, hours, "Call ### for more information.", bus stop (small italic).
Lines are classified by font, so wrapped lines don't leak into the next entry.
"""
import csv
import re
import sys
from pathlib import Path

import pdfplumber

PDF = Path("data/raw/services/Middlesex-County-Food-Guide-2.pdf")
OUT = Path("data/manual/food_guide_extracted.csv")
SOURCE = ("https://sites.rutgers.edu/food-waste/wp-content/uploads/sites/667/2025/10/"
          "Middlesex-County-Food-Guide-2.pdf")
HOURS = re.compile(r"\b(Mon|Tue|Tues|Wed|Thu|Thurs|Fri|Sat|Sun|Every day|Last|1st|2nd|3rd|4th|Walk-in|Daily)\b")


def column_lines(pdf):
    """Yield (kind, text) per line, column by column. kind comes from the font:
    name = bold ~23pt, addr = italic ~23pt, bus = italic ~19pt, header = bold > 30pt."""
    with pdfplumber.open(pdf) as p:
        for pg in p.pages:
            x0, y0, x1, y1 = pg.bbox
            w = x1 - x0
            for k in range(3):
                col = pg.crop((x0 + k * w / 3, y0, x0 + (k + 1) * w / 3, y1))
                words = col.extract_words(extra_attrs=["fontname", "size"], keep_blank_chars=True)
                lines = {}
                for wd in words:
                    key = (round(wd["top"] / 3), "Bold" in wd["fontname"] and wd["size"] < 26,
                           "Italic" in wd["fontname"], round(wd["size"]))
                    lines.setdefault(key, []).append(wd)
                for key in sorted(lines):
                    ws = sorted(lines[key], key=lambda d: d["x0"])
                    text = " ".join(d["text"].strip() for d in ws).strip()
                    _, bold, italic, size = key
                    if size > 30:
                        kind = "header"
                    elif italic and size < 21:
                        kind = "bus"
                    elif italic:
                        kind = "addr"
                    elif bold and size >= 22 and not re.fullmatch(r"[\d\s()-]+(ext\.? ?\d+)?", text):
                        kind = "name"
                    else:
                        kind = "body"   # includes bold phone numbers (21pt)
                    yield kind, text


def entries(lines):
    cur, last = None, None
    for kind, text in lines:
        if kind == "header":
            continue
        if kind == "name":
            if last != "name":
                if cur:
                    yield cur
                cur = {"name": [], "addr": [], "body": [], "bus": []}
            cur["name"].append(text)
        elif cur is not None:
            cur[kind].append(text)
        last = kind
    if cur:
        yield cur


def parse(e):
    name = re.sub(r"\s+", " ", " ".join(e["name"])).strip()
    addr = re.sub(r"\s+", " ", " ".join(e["addr"])).strip()
    if "Nearest Bus Stop:" in addr:   # some bus stops are set in the address font
        addr, extra = addr.split("Nearest Bus Stop:", 1)
        addr = addr.strip()
        e["bus"].append(extra.strip())
    if not addr:
        return None
    m = re.match(r"(.+?),\s*([A-Za-z .]+)$", addr)
    street, city = (m.group(1).strip(), m.group(2).strip()) if m else (addr, "")
    text = re.sub(r"\s+", " ", " ".join(e["body"]))
    phone = re.search(r"(\d{3}-\s?\d{3}-\d{4})", text)
    body = re.sub(r"Call\s*(\d{3}-\s?\d{3}-\d{4})?\s*for\s+more\s+(information\.?)?", "", text)
    body = re.sub(r"^\s*information\.?\s*|\s+information\.?\s*$", " ", body)
    body = re.sub(r"\d{3}-\s?\d{3}-\d{4}", "", body).strip()
    hm = HOURS.search(body)
    desc, hours = (body[:hm.start()].strip(), body[hm.start():].strip()) if hm else (body, "")
    bus = re.sub(r"^Nearest Bus Stop:\s*", "", " ".join(e["bus"])).strip()
    # two entries' italic address lines sometimes interleave on the later pages
    review = "" if len(re.findall(r"\d+\s+[A-Z]", addr)) <= 1 else \
        "address merged with another entry, fix by hand"
    return {"review": review, "name": name, "address": street, "city": city,
            "phone": phone.group(1).replace(" ", "") if phone else "",
            "description": desc, "hours": hours, "nearest_bus_stop": bus, "source_url": SOURCE}


def main():
    if not PDF.exists():
        print(f"missing {PDF}; download it from {SOURCE}")
        return 1
    rows, seen = [], set()
    for b in entries(column_lines(PDF)):
        r = parse(b)
        if r and (r["name"].lower(), r["address"].lower()) not in seen:
            seen.add((r["name"].lower(), r["address"].lower()))
            rows.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} entries -> {OUT} (review by hand before copying into services.csv)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
