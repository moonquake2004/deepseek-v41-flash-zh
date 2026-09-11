"""Extract the report's tables with fidelity (bold from font info, underline from vector lines).

Rows are clustered by vertical centre, columns by right edge (numeric cells are
right-aligned in this report).  Underlines are short horizontal vector segments
sitting just below a text span -- table rules are far longer, so a length filter
separates the two.
"""
import json
import re

import fitz

DOC = fitz.open("DeepSeek_V41_Tech_Report.pdf")

# table -> (page, y-top, y-bottom, x-left, x-right) in PDF points
TABLES = {
    1: (24, 149.6, 462.2, 60, 545),
    2: (30, 285.0, 355.0, 60, 545),
    3: (33, 220.9, 471.8, 55, 545),
    4: (35, 340.0, 395.0, 55, 545),
    5: (48, 108.0, 150.0, 55, 545),
}


def spans_in(page, y0, y1, x0, x1):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for s in ln["spans"]:
                bb = s["bbox"]
                if not s["text"].strip():
                    continue
                if y0 is not None and (bb[1] < y0 - 2 or bb[3] > y1 + 2):
                    continue
                if bb[0] < x0 - 2 or bb[2] > x1 + 2:
                    continue
                out.append({
                    "t": s["text"].strip(),
                    "bb": bb,
                    "bold": "Bold" in s["font"],
                    "yc": (bb[1] + bb[3]) / 2.0,
                })
    return out


def underline_segments(page, x0, x1, y0, y1):
    segs = []
    for g in page.get_drawings():
        for it in g["items"]:
            if it[0] != "l":
                continue
            a, b = it[1], it[2]
            if abs(a.y - b.y) > 0.8:
                continue
            length = abs(a.x - b.x)
            if not (4 <= length <= 45):            # underlines are glyph-width; rules are 100s of pt
                continue
            xs, xe, y = min(a.x, b.x), max(a.x, b.x), (a.y + b.y) / 2.0
            if y0 is not None and not (y0 - 4 <= y <= y1 + 20):
                continue
            if xe < x0 or xs > x1:
                continue
            segs.append((xs, xe, y))
    return segs


def cluster_rows(spans, tol=4.0):
    rows = []
    for s in sorted(spans, key=lambda s: s["yc"]):
        for r in rows:
            if abs(r["yc"] - s["yc"]) <= tol:
                r["items"].append(s)
                r["yc"] = sum(i["yc"] for i in r["items"]) / len(r["items"])
                break
        else:
            rows.append({"yc": s["yc"], "items": [s]})
    for r in rows:
        r["items"].sort(key=lambda i: i["bb"][0])
    return sorted(rows, key=lambda r: r["yc"])


NUMISH = re.compile(r"^[\d.,]+$")
SHOTLIKE = re.compile(r"^\d+(?:\.\d+)?(?:\s*-\s*\d+)?-shot$|^\d+-shot$")


def _group(values, tol, min_size):
    groups = []
    for x in sorted(values):
        if groups and x - groups[-1][-1] <= tol:
            groups[-1].append(x)
        else:
            groups.append([x])
    return [sum(g) / len(g) for g in groups if len(g) >= min_size]


def cluster_cols(spans, tol=4.0):
    """Right edges of numeric cells give the data columns (right-aligned tables)."""
    rights = [s["bb"][2] for s in spans
              if NUMISH.match(s["t"]) or re.match(r"^\d+(\.\d+)?[TBMK]$", s["t"])]
    anchors = _group(rights, tol, 3)
    if anchors:
        return anchors
    # fall back to centre alignment (some tables centre their numbers)
    centres = [(s["bb"][0] + s["bb"][2]) / 2.0 for s in spans if NUMISH.match(s["t"])]
    return _group(centres, 6.0, 2)


def build(tnum):
    page_no, y0, y1, x0, x1 = TABLES[tnum]
    page = DOC[page_no - 1]
    if y0 is None:                              # crop to the table's own extent
        hits = [s for s in spans_in(page, None, None, x0, x1)
                if re.match(r"^Table %d$" % tnum, s["t"])]
        cap = hits[0]["bb"][3] if hits else 0
        y0, y1 = cap + 8, page.rect.height - 60
    spans = spans_in(page, y0, y1, x0, x1)
    segs = underline_segments(page, x0, x1, y0, y1)

    def underlined(s):
        sx0, sy0, sx1, sy1 = s["bb"]
        for a, b, y in segs:
            ov = min(sx1, b) - max(sx0, a)
            if ov > 0.5 * (sx1 - sx0) and -1.5 <= y - sy1 <= 4.5:
                return True
        return False

    for s in spans:
        s["u"] = underlined(s)

    rows = cluster_rows(spans)
    anchors = cluster_cols(spans)
    shots_right = None
    shot_edges = sorted(s["bb"][2] for s in spans if SHOTLIKE.match(s["t"]))
    if shot_edges:
        shots_right = shot_edges[len(shot_edges) // 2]

    def col_of(s):
        r = s["bb"][2]
        c = s["bb"][0]
        if shots_right is not None and abs(r - shots_right) <= 6:
            return 1                                    # "# Shots"
        if s["t"] == "-":                               # placeholder dash: judge by centre
            mid = (c + r) / 2.0
            best = min(range(len(anchors)), key=lambda i: abs(anchors[i] - mid)) if anchors else None
            if best is not None and abs(anchors[best] - mid) <= 30:
                return best + 2
            return 1
        if anchors:
            best = min(range(len(anchors)), key=lambda i: abs(anchors[i] - r))
            if abs(anchors[best] - r) <= 22:
                return best + 2                         # data columns start after stub
        return -1 if c < 130 else 0                     # row-group label vs metric name

    table = []
    for r in rows:
        cells = {}
        for s in r["items"]:
            c = col_of(s)
            cell = cells.setdefault(c, {"t": "", "bold": False, "u": False, "x": s["bb"][0]})
            cell["t"] = (cell["t"] + " " + s["t"]).strip()
            cell["bold"] |= s["bold"]
            cell["u"] |= s["u"]
        table.append(cells)
    return table, anchors


if __name__ == "__main__":
    dump = {}
    for n in sorted(TABLES):
        t, _ = build(n)
        dump[n] = [[{"t": c["t"], "b": c["bold"], "u": c["u"]}
                    for _, c in sorted(cells.items())] for cells in t]
        print("=" * 30, "Table", n)
        for cells in t:
            print("  " + " || ".join(
                ("**" if c["bold"] else "") + ("_" if c["u"] else "") + c["t"]
                for _, c in sorted(cells.items())))
    json.dump(dump, open("tables.json", "w"), ensure_ascii=False, indent=1)
    print("\nwrote tables.json")
