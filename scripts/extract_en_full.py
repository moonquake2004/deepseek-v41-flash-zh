"""Full-text extraction for the English edition.

Same block-based strategy as `extract_en.py`, but instead of stopping at the
bibliography it also emits the references and appendices A/B/C.
"""
import json
import re

raw = open("bbox.xml", encoding="utf-8", errors="replace").read()

page_re = re.compile(r"<page\b[^>]*?width=\"([\d.]+)\"\s+height=\"([\d.]+)\"(.*?)</page>", re.S)
block_re = re.compile(r"<block\b([^>]*)>(.*?)</block>", re.S)
line_re = re.compile(r"<line\b([^>]*)>(.*?)</line>", re.S)
word_re = re.compile(r"<word\b([^>]*)>(.*?)</word>", re.S)
tag_re = re.compile(r"<[^>]+>")


def attr(s, k):
    m = re.search(k + r"=\"([-\d.]+)\"", s)
    return float(m.group(1)) if m else 0.0


blocks = []
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

MATH = set("𝐿𝐻𝑊𝑍𝐴𝐵𝐶𝑁𝐾𝑄𝑋𝑌∈⩾⩽√∑≈×·Δℓρτηγθπ∇̂")
STOP = re.compile(r"\b(the|of|and|is|are|in|to|for|with|that|as|we|by|on|be|it|this|from|which|at|an)\b", re.I)
CAP = re.compile(r"^\s*(Figure|Table)\s*\d+\s*\|")

HEADINGS = {
    "References": "References",
    "A. Author List": "A. Author List",
    "B. Evaluation Details": "B. Evaluation Details",
    "C. Exponential Token Penalty in Reasoning Effort Control":
        "C. Exponential Token Penalty in Reasoning Effort Control",
}
SECTION = re.compile(r"^(\d{1,2}(?:\.\d{1,2})*)\.?\s+([A-Z][A-Za-z0-9 ,\-–—&()/'’:?]{3,70})$")


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


APX_SUBHEAD = [
    "B.1. Scaffold Configurations",
    "B.2. Reasoning Efforts across Scaffolds",
    "B.3. Detailed Results of Reasoning Benchmarks across Reasoning Efforts",
]


def apx_subhead(s):
    """Return (heading, remainder) if the block starts with an appendix sub-heading."""
    for h in APX_SUBHEAD:
        pat = re.escape(h).replace(r"\ ", r"\s+")
        m = re.match(pat + r"\s*(.*)$", s)
        if m:
            return h, m.group(1).strip()
    return None, None


NUMTOK = re.compile(r"(?<![A-Za-z0-9.$])\d+(?:\.\d+)?(?![A-Za-z0-9])")


def is_noise(t):
    """Axis labels / table rows / figure-internal text that leak out of graphics."""
    s = t.strip()
    if CAP.match(s) or re.match(r"^Table \d", s):
        return True
    if s.startswith("Note."):
        return True
    if "Output tokens (k)" in s or s.startswith("Avg output tokens"):
        return True
    if "Reasoning effort" in s and len(NUMTOK.findall(s)) >= 3:
        return True
    nums = NUMTOK.findall(s)
    words = re.findall(r"[a-z]{3,}", s)
    if len(nums) >= 6 and len(words) < len(nums):
        return True
    return False


def is_appendix_body(s):
    if is_body(s):
        return True
    if s.startswith("•"):
        return True                        # bullet list inside B.1
    if re.match(r"^[A-Z][A-Za-z &/]+:", s):
        return True                        # author-list group heading
    if s.count(",") >= 8 and len(s) > 120:
        return True                        # author-list run
    if re.search(r"\b(is|are|denote|listed)\b", s) and len(s) > 60:
        return True                        # prose that lacks articles ("Authors are listed ...")
    if "=" in s and len(re.findall(r"[A-Za-z]{3,}", s)) >= 2:
        return True                        # display equation with surrounding prose
    if len(s) <= 45 and any(ord(c) > 127 for c in s) and not s.isdigit():
        return True                        # math fragment ("𝐿 norm", "𝜏") -- merged into the line above
    return False


items = []                    # ("H"/"B"/"R", text)
mode = "main"                 # main | refs | apx
for pg, y, x, t in blocks:
    s = t.strip()
    if s in HEADINGS:
        items.append(("H", HEADINGS[s]))
        mode = "refs" if s == "References" else "apx"
        continue
    if mode == "main":
        if SECTION.match(s) and len(s) < 75 and not s.endswith("."):
            items.append(("H", s))
        elif not is_noise(s) and is_body(s):
            items.append(("B", s))
    elif mode == "refs":
        if len(s) > 25 and not is_noise(s):     # a citation entry
            items.append(("R", s))
    else:                                       # appendices
        head, rest = apx_subhead(s)
        if head:
            items.append(("B", "\x00" + head))
            if rest and not is_noise(rest):
                items.append(("B", rest))
            continue
        if is_noise(s):
            continue
        if is_appendix_body(s):
            items.append(("B", s))

# merge continuation fragments
merged = []
for kind, t in items:
    if kind == "H" or t.startswith("\x00"):
        merged.append((kind, t))
        continue
    if merged and merged[-1][0] == kind and not merged[-1][1].startswith("\x00") \
            and not re.search(r"[.!?:\u201d\")]$", merged[-1][1]) \
            and not re.search(r"[=≈⩾⩽−+×·∑√,]\s*$", merged[-1][1]):
        merged[-1] = (kind, merged[-1][1].rstrip("- ") + " " + t)
    else:
        merged.append((kind, t))

abstract = [t for k, t in merged[:next((i for i, (k, _) in enumerate(merged) if k == "H"), 0)] if k == "B"]

sections, cur, curkind = {}, None, None
for kind, t in merged:
    if kind == "H":
        cur, curkind = t, kind
        sections.setdefault(cur, [])
    elif cur is not None:
        sections[cur].append(t)

# ---- post-processing -------------------------------------------------------
import html as _html


def clean(t):
    t = _html.unescape(t)
    t = t.replace("\u00ad", "")
    return re.sub(r"\s+", " ", t).strip()


def is_table_row(t):
    """Blocks that are really rows of the appendix tables (Table 5)."""
    nums = re.findall(r"\b\d+\.\d\b", t)
    return len(nums) >= 3 and t.count(".") - len(nums) <= 1 and len(t) < 160


def is_caption(t):
    return bool(CAP.match(t)) or bool(re.match(r"^(Note\.|Figure|Table)\b", t)) and len(t) < 200


def ref_start(t):
    return bool(re.match(r"^[A-Z](\.[- ]?[A-Z]?\.? )?[A-Z][A-Za-z’'\-]+,", t) or
                re.match(r"^[A-Z][a-z]+ [A-Z]\.", t) or
                re.match(r"^(DeepSeek-AI|OpenAI|Anthropic|Qwen|Google|Meta|Alibaba|Moonshot)", t))


out = {"Abstract": [clean(p) for p in abstract]}
for k, v in sections.items():
    paras = []
    for p in v:
        p = clean(p)
        if not p or is_table_row(p) or p.strip().startswith("Table 5 |"):
            continue
        paras.append(p)
    if k == "References":                      # re-join citation fragments
        joined = []
        for p in paras:
            if joined and not ref_start(p):
                joined[-1] = (joined[-1].rstrip("- ") + " " + p).strip()
            else:
                joined.append(p)
        paras = joined
    if paras:
        out[k] = paras

json.dump(out, open("paragraphs_full.json", "w"), ensure_ascii=False, indent=1)
for k, v in out.items():
    print(f"{len(v):3d}  {k}")
print("TOTAL:", sum(len(v) for v in out.values()),
      "| chars:", sum(len(p) for v in out.values() for p in v))
