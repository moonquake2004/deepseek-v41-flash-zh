"""Paragraph extraction from `pdftotext -bbox-layout` block structure.

In the PDF each body paragraph is a single text <block>; using the block
boundaries recovers the true paragraph structure (blank-line and indentation
heuristics both fail on this file).
"""
import json
import re

raw = open("bbox.xml", encoding="utf-8", errors="replace").read()

page_re = re.compile(r"<page\b[^>]*?width=\"([\d.]+)\"\s+height=\"([\d.]+)\"(.*?)</page>", re.S)
block_re = re.compile(r"<block\b([^>]*)>(.*?)</block>", re.S)
line_re = re.compile(r"<line\b([^>]*)>(.*?)</line>", re.S)
word_re = re.compile(r"<word\b([^>]*)>(.*?)</word>", re.S)
tag_re = re.compile(r"<[^>]+>")
attr = lambda s, k: float(re.search(k + r"=\"([-\d.]+)\"", s).group(1)) if re.search(k + r"=\"([-\d.]+)\"", s) else 0.0

blocks = []          # (page, y, x, text)
for pi, pm in enumerate(page_re.finditer(raw), start=1):
    for bm in block_re.finditer(pm.group(3)):
        bs, body = bm.group(1), bm.group(2)
        lines = []
        for lm in line_re.finditer(body):
            words = [tag_re.sub("", w.group(2)) for w in word_re.finditer(lm.group(2))]
            words = [w for w in words if w.strip()]
            if words:
                lines.append(" ".join(words))
        if not lines:
            continue
        text = ""
        for ln in lines:
            if text.endswith("-") and ln[:1].islower():
                text = text[:-1] + ln
            else:
                text = (text + " " + ln).strip()
        blocks.append((pi, attr(bs, "yMin"), attr(bs, "xMin"), text))

blocks.sort(key=lambda b: (b[0], b[1], b[2]))

# stop before the bibliography / appendix
ref_i = next((i for i, b in enumerate(blocks) if b[3].strip() == "References"), None)
if ref_i is not None:
    blocks = blocks[:ref_i]

MATH = set("𝐿𝐻𝑊𝑍𝐴𝐵𝐶𝑁𝐾𝑄𝑋𝑌∈⩾⩽√∑≈×·Δℓρτηγθπ∇̂")
STOP = re.compile(r"\b(the|of|and|is|are|in|to|for|with|that|as|we|by|on|be|it|this|from|which|at|an)\b", re.I)
CAP = re.compile(r"^\s*(Figure|Table)\s*\d+\s*\|")


def is_body(t):
    s = t.strip()
    if CAP.match(s):
        return False
    if s.count(".") + s.count("?") + s.count("!") == 0:
        return False
    if len(STOP.findall(s)) < 4:
        return False
    if not re.search(r"\b(the|a|an)\b", s) and len(s) < 240:
        return False
    if len(s) > 60 and (len(STOP.findall(s)) / max(len(s.split()), 1)) < 0.10:
        return False
    if sum(1 for ch in s if ch in MATH) >= 8 and len(STOP.findall(s)) < 3:
        return False
    return True


SECTION = re.compile(r"^(\d{1,2}(?:\.\d{1,2})*)\.?\s+([A-Z][A-Za-z0-9 ,\-–—&()/'’:?]{3,70})$")

items = []
for pg, y, x, t in blocks:
    s = t.strip()
    if SECTION.match(s) and len(s) < 75 and not s.endswith("."):
        items.append(("H", s))
    elif is_body(s):
        items.append(("B", s))

merged = []
for kind, t in items:
    if kind == "H":
        merged.append(("H", t))
    elif merged and merged[-1][0] == "B" and not re.search(r"[.!?:\u201d\")]$", merged[-1][1]):
        merged[-1] = ("B", merged[-1][1].rstrip("- ") + " " + t)
    else:
        merged.append(("B", t))

# abstract = everything before the first numbered heading
abstract = [t for k, t in merged[:next((i for i, (k, _) in enumerate(merged) if k == "H"), 0)] if k == "B"]

sections, cur = {}, None
for kind, t in merged:
    if kind == "H":
        cur = t
        sections.setdefault(cur, [])
    elif cur is not None:
        sections[cur].append(t)

out = {"Abstract": abstract}
for k, v in sections.items():
    if v:
        out[k] = v

json.dump(out, open("paragraphs.json", "w"), ensure_ascii=False, indent=1)
for k, v in out.items():
    print(f"{len(v):3d}  {k}")
print("TOTAL:", sum(len(v) for v in out.values()))
