"""Crop figure regions out of the rendered PDF pages.

Strategy: use pdftotext -bbox-layout output to locate the "Figure N |" caption
on each page, then take the vertical gap between the caption and the nearest
surrounding text block as the figure region.
"""
import re
from PIL import Image

SCALE = 130 / 72.0  # pt -> px

raw = open("bbox.xml", encoding="utf-8", errors="replace").read()
page_re = re.compile(r"<page\b[^>]*?width=\"([\d.]+)\"\s+height=\"([\d.]+)\"(.*?)</page>", re.S)
word_re = re.compile(r"<word\s+xMin=\"([\d.]+)\"\s+yMin=\"([\d.]+)\"\s+xMax=\"([\d.]+)\"\s+yMax=\"([\d.]+)\"[^>]*>(.*?)</word>", re.S)
tag_re = re.compile(r"<[^>]+>")

pages = {}
for pi, m in enumerate(page_re.finditer(raw), start=1):
    W, H, body = float(m.group(1)), float(m.group(2)), m.group(3)
    words = []
    for wm in word_re.finditer(body):
        txt = tag_re.sub("", wm.group(5))
        bb = tuple(float(wm.group(i)) for i in range(1, 5))
        words.append((bb, txt))
    pages[pi] = {"size": (W, H), "words": words}

results = []
for pi, p in pages.items():
    W, H = p["size"]
    words = p["words"]
    # find caption start: a word "Figure" followed by integer
    cap_idx = None
    for i, (bb, t) in enumerate(words):
        if t.strip() != "Figure":
            continue
        nxt = words[i + 1][1].strip() if i + 1 < len(words) else ""
        nxt2 = words[i + 2][1].strip() if i + 2 < len(words) else ""
        if re.match(r"^\d+", nxt) and ("|" in nxt or "|" in nxt2 or nxt2 == "|"):
            cap_idx = i
            break
    if cap_idx is None:
        continue
    capnum = re.match(r"^(\d+)", words[cap_idx + 1][1].strip()).group(1)
    # caption spans a few lines; find caption block vertical extent
    cap_top = words[cap_idx][0][1]
    cap_bot = words[cap_idx][0][3]
    j = cap_idx
    while j + 1 < len(words) and words[j + 1][0][1] < cap_bot + 12:
        cap_bot = max(cap_bot, words[j + 1][0][3])
        j += 1
        if j - cap_idx > 200:
            break

    xs = [w[0][0] for w in words] + [w[0][2] for w in words]
    left = max(0, min(xs) - 4)
    right = min(W, max(xs) + 4)

    # group words into lines; body lines are justified (left edge ~ margin,
    # right edge ~ right margin), which distinguishes paragraphs from labels
    # inside figures.
    lines = []
    for bb, t in sorted(words, key=lambda w: (w[0][1], w[0][0])):
        placed = False
        for ln in lines:
            if abs(ln["y0"] - bb[1]) < 3.5:
                ln["y0"] = min(ln["y0"], bb[1])
                ln["y1"] = max(ln["y1"], bb[3])
                ln["x0"] = min(ln["x0"], bb[0])
                ln["x1"] = max(ln["x1"], bb[2])
                placed = True
                break
        if not placed:
            lines.append({"y0": bb[1], "y1": bb[3], "x0": bb[0], "x1": bb[2]})

    def is_body(ln):
        return ln["x0"] < 80 and ln["x1"] > 495

    body_above = [ln["y1"] for ln in lines if ln["y1"] <= cap_top + 1 and is_body(ln)]
    body_below = [ln["y0"] for ln in lines if ln["y0"] >= cap_bot - 1 and is_body(ln)]

    if cap_top < 90 and body_below:  # caption on top -> figure below
        y0 = cap_bot + 6
        y1 = min(body_below) - 6
    else:  # caption below -> figure above
        y0 = (max(body_above) + 6) if body_above else 40
        y1 = cap_top - 4
    if y1 - y0 < 40:
        continue
    img = Image.open(f"pages/p-{pi:02d}.png")
    box = (int(left * SCALE), int(y0 * SCALE), int(right * SCALE), int(y1 * SCALE))
    crop = img.crop(box)
    name = f"figs/fig-{int(capnum):02d}.png" if capnum else f"figs/fig-p{pi:02d}.png"
    crop.save(name)
    results.append((name, pi, round(y1 - y0, 1)))

for r in sorted(results):
    print(r)
