"""Build the English (re-typeset) HTML edition of the DeepSeek-V4.1-Flash report.

Body text comes from `paragraphs_full.json` (block-accurate extraction), tables
from `tables.json` (bold from PDF font data, underline from PDF vector lines),
figure captions from `figcaps.json`.
"""
import html
import json
import re

paras = json.load(open("paragraphs_full.json"))
tables = json.load(open("tables.json"))
figcaps = json.load(open("figcaps.json"))
tabcaps = json.load(open("tabcaps.json"))

esc = lambda s: html.escape(s, quote=False)

# ---------------------------------------------------------------- structure
# (level, number, title, key) -- 1 = chapter, 2 = section, 3 = subsection
STRUCTURE = [
    (1, "1", "Introduction", "1. Introduction"),
    (1, "2", "Architecture", None),
    (2, "2.1", "Overview", "2.1. Overview"),
    (3, "2.1.1", "Multimodal Architecture", "2.1.1. Multimodal Architecture"),
    (2, "2.2", "Causal Encoder-Decoder (CED)", "2.2. Causal Encoder-Decoder (CED)"),
    (2, "2.3", "Compressed Sparse Attention 2 (CSA2)", "2.3. Compressed Sparse Attention 2 (CSA2)"),
    (3, "2.3.1", "Cross-Layer KV and Index Reuse", "2.3.1. Cross-Layer KV and Index Reuse"),
    (3, "2.3.2", "Hierarchical Sparse Indexer", "2.3.2. Hierarchical Sparse Indexer"),
    (2, "2.4", "Efficient Architectural Extensions", None),
    (3, "2.4.1", "Single-Pass mHC", "2.4.1. Single-Pass mHC"),
    (3, "2.4.2", "Engram", "2.4.2. Engram"),
    (3, "2.4.3", "DSpark", "2.4.3. DSpark"),
    (3, "2.4.4", "FP4 Main KV Cache", "2.4.4. FP4 Main KV Cache"),
    (2, "2.5", "Optimization", "2.5. Optimization"),
    (1, "3", "General Infrastructures", None),
    (2, "3.1", "Training Infrastructure", None),
    (3, "3.1.1", "Multimodal Training Infrastructure", "3.1.1. Multimodal Training Infrastructure"),
    (3, "3.1.2", "Attention Sharing Training for CSA2", "3.1.2. Attention Sharing Training for CSA2"),
    (3, "3.1.3", "Engram", "3.1.3. Engram"),
    (2, "3.2", "Inference System", "3.2. Inference System"),
    (3, "3.2.1", "Persistent KV Cache Management", "3.2.1. Persistent KV Cache Management"),
    (3, "3.2.2", "SWA Bounded Replay", "3.2.2. SWA Bounded Replay"),
    (1, "4", "Pre-Training", None),
    (2, "4.1", "Data Construction", "4.1. Data Construction"),
    (2, "4.2", "Pre-Training Setups", None),
    (3, "4.2.1", "Model Setups", "4.2.1. Model Setups"),
    (3, "4.2.2", "Training Setups", "4.2.2. Training Setups"),
    (2, "4.3", "Evaluations", None),
    (3, "4.3.1", "Evaluation Benchmarks", "4.3.1. Evaluation Benchmarks"),
    (3, "4.3.2", "Evaluation Results", "4.3.2. Evaluation Results"),
    (1, "5", "Post-Training", None),
    (2, "5.1", "Post-Training Pipeline", "5.1. Post-Training Pipeline"),
    (3, "5.1.1", "Large-Scale Agent Task Synthesis", "5.1.1. Large-Scale Agent Task Synthesis"),
    (3, "5.1.2", "RL in Synthesized Tasks", "5.1.2. RL in Synthesized Tasks"),
    (3, "5.1.3", "Running Agents at Massive Scale: DSec", "5.1.3. Running Agents at Massive Scale: DSec"),
    (3, "5.1.4", "Controllable Reasoning Effort in RL", "5.1.4. Controllable Reasoning Effort in RL"),
    (2, "5.2", "Asynchronous Post-training Infrastructure", "5.2. Asynchronous Post-training Infrastructure"),
    (3, "5.2.1", "Overall Workflow", "5.2.1. Overall Workflow"),
    (3, "5.2.2", "Mitigating Length Bias and Off-Policy Effects", "5.2.2. Mitigating Length Bias and Off-Policy Effects"),
    (3, "5.2.3", "Performance Optimization", "5.2.3. Performance Optimization"),
    (3, "5.2.4", "Large-Scale On-Policy Distillation", "5.2.4. Large-Scale On-Policy Distillation"),
    (2, "5.3", "Evaluation", None),
    (3, "5.3.1", "Evaluation Setup", "5.3.1. Evaluation Setup"),
    (3, "5.3.2", "Evaluation Results", "5.3.2. Evaluation Results"),
    (3, "5.3.3", "Performance across reasoning efforts", "5.3.3. Performance across reasoning efforts"),
    (3, "5.3.4", "Performance across agent scaffolds", "5.3.4. Performance across agent scaffolds"),
    (3, "5.3.5", "Multi-Agent", "5.3.5. Multi-Agent"),
    (1, "6", "Conclusion, Limitations, and Future Directions", "6. Conclusion, Limitations, and Future Directions"),
]

APPENDIX = [
    (1, "A", "Author List", "A. Author List"),
    (1, "B", "Evaluation Details", "B. Evaluation Details"),
    (1, "C", "Exponential Token Penalty in Reasoning Effort Control",
     "C. Exponential Token Penalty in Reasoning Effort Control"),
]

AFTER_FIG = {
    "Abstract": [1],
    "1. Introduction": [2, 3],
    "2.3. Compressed Sparse Attention 2 (CSA2)": [4],
    "2.3.2. Hierarchical Sparse Indexer": [5],
    "4.3.2. Evaluation Results": [6],
    "5.1.2. RL in Synthesized Tasks": [7, 8],
    "5.3.3. Performance across reasoning efforts": [9],
    "5.3.5. Multi-Agent": [10],
    "B. Evaluation Details": [],
}
AFTER_FIG_APX = {"B.2. Reasoning Efforts across Scaffolds": [11],
                 "B.3. Detailed Results of Reasoning Benchmarks across Reasoning Efforts": [12]}

TABLE_CAP = {
    1: "Table 1 | Comparison among DeepSeek-V4-Flash-Base, DeepSeek-V4-Pro-Base, and DeepSeek-V4.1-Flash-Base. All models are evaluated in our internal framework and share the same evaluation setting. Scores with a gap not exceeding 0.3 are considered to be at the same level. The highest score in each row is in bold font, and the second is underlined.",
    2: "Table 2 | Mapping between the public API reasoning-effort tiers and the underlying scalar effort values b.",
    3: "Table 3 | Comparison between DeepSeek-V4.1-Flash with closed/open source models. † denotes text-only subset of HLE. The best results are highlighted in bold; the second-best results are underlined.",
    4: "Table 4 | Performance across agent scaffolds at Max reasoning effort.",
    5: "Table 5 | Performance across Claude Code versions at Max reasoning effort.",
}

TABLE_NOTE = {
    4: "Note. All scaffolds use N = 8 samples per task on DeepSWE v1.1 and N = 3 on Terminal-Bench v2.1. Runs use Linux containers, temperature 1.0, top-p 0.95, a 1M-token context window, and max_steps=500 model-generation rounds per agent on both benchmarks. Terminal-Bench v2.1 is evaluated without network access. We evaluate four Claude Code versions, with per-version results and their average reported in Appendix Table 5; this table reports v2.1.251. More scaffold-specific configurations are detailed in Appendix B.1.",
    5: "Note. Average is computed from the unrounded Pass@1 scores of the four versions.",
}

TABLE_AFTER = {
    "4.3.2. Evaluation Results": [1],
    "5.1.4. Controllable Reasoning Effort in RL": [2],
    "5.3.2. Evaluation Results": [3],
    "5.3.4. Performance across agent scaffolds": [4],
}
TABLE_AFTER_APX = {"B.1. Scaffold Configurations": [5]}

TABLE_HEAD = {
    1: '<tr><th class="l" rowspan="2">Benchmark (Metric)</th><th rowspan="2"># Shots</th>'
       '<th colspan="3">DeepSeek-V4-Flash Base &nbsp;|&nbsp; DeepSeek-V4-Pro Base &nbsp;|&nbsp; DeepSeek-V4.1-Flash Base</th></tr>'
       '<tr class="sub"><th>DeepSeek-V4-Flash</th><th>DeepSeek-V4-Pro</th><th>DeepSeek-V4.1-Flash</th></tr>'
       # placeholder replaced below
       ,
    2: '<tr><th class="l">API tier</th><th>Effort value <i>b</i></th></tr>',
    3: '<tr><th class="l" rowspan="2">Benchmark (Metric)</th>'
       '<th>Opus-5<br><span>Max</span></th><th>GPT-5.6<br><span>Max</span></th><th>Sol&nbsp;K3<br><span>Max</span></th>'
       '<th>GLM-5.3<br><span>Max</span></th><th>DS-V4-Pro<br><span>Max</span></th>'
       '<th>DS-V4-Flash<br><span>Max</span></th><th>DS-V4.1-Flash<br><span>Max</span></th></tr>',
    4: '<tr><th class="l" rowspan="2">Benchmark (Metric)</th><th rowspan="2">Claude Code</th>'
       '<th rowspan="2">Codex</th><th rowspan="2">OpenCode</th><th rowspan="2">Pi</th>'
       '<th rowspan="2">mini-SWE</th><th colspan="3">DeepSeek Harness</th></tr>'
       '<tr class="sub"><th>Minimal</th><th>Standard</th><th>PTC</th></tr>',
    5: '<tr><th class="l">Benchmark (Metric)</th><th>v2.1.105</th><th>v2.1.238</th>'
       '<th>v2.1.251</th><th>v2.1.259</th><th>Average</th></tr>',
}

# Table 1's header is a 3-line stack in the original; render it as two stacked rows.
TABLE_HEAD[1] = (
    '<tr class="sub"><th class="l" rowspan="3">Benchmark (Metric)</th><th rowspan="3"># Shots</th>'
    '<th>DeepSeek-V4-Flash</th><th>DeepSeek-V4-Pro</th><th>DeepSeek-V4.1-Flash</th></tr>'
    '<tr class="sub"><th>Base</th><th>Base</th><th>Base</th></tr>'
)

TABLE_DROP = {1: 3, 2: 1, 3: 3, 4: 3, 5: 1}
TABLE_COLS = {1: 5, 2: 2, 3: 8, 4: 8, 5: 6}

apx_tables = {"B.1. Scaffold Configurations": [5]}


def cell_html(c):
    t = esc(c["t"])
    if c["b"]:
        t = f"<b>{t}</b>"
    if c["u"]:
        t = f'<u>{t}</u>'
    return t


def render_rows(n):
    """Turn extracted rows into <tr> markup, handling group-label rows."""
    rows = tables[str(n)][TABLE_DROP[n]:]
    ncol = TABLE_COLS[n]
    out = []
    for row in rows:
        cells = [c for c in row if c["t"]]
        if not cells:
            continue
        if len(cells) == 1:
            out.append(f'<tr class="grp"><td colspan="{ncol}">{cell_html(cells[0])}</td></tr>')
            continue
        # a leading group label sits in the stub column and must become its own row
        if len(cells) == ncol + 1:
            out.append(f'<tr class="grp"><td colspan="{ncol}">{cell_html(cells[0])}</td></tr>')
            cells = cells[1:]
        tds = []
        for i, c in enumerate(cells):
            cls = ' class="l"' if i == 0 else ""
            tds.append(f"<td{cls}>{cell_html(c)}</td>")
        while len(tds) < ncol:
            tds.append("<td></td>")
        out.append("<tr>" + "".join(tds) + "</tr>")
    return "\n".join(out)


def table_block(n):
    parts = [f'<div class="tblwrap"><table class="tbl t{n}">',
             f'<caption><b>Table {n} |</b> {esc(TABLE_CAP[n].split("| ", 1)[1])}</caption>',
             f"<thead>{TABLE_HEAD[n]}</thead><tbody>", render_rows(n), "</tbody></table></div>"]
    if n in TABLE_NOTE:
        parts.append(f'<div class="tnote">{esc(TABLE_NOTE[n])}</div>')
    return "\n".join(parts)


# PDF line-break artefacts that survive block-joining (verified against the original)
REF_FIX = [
    ("low-pre cision-inference/ .", "low-precision-inference/."),
    (" gpt-oss-120b & gpt-oss-20b model card", " gpt-oss-120b & gpt-oss-20b model card"),
    (" ,", ","),
    (" .", "."),
]


def ref_fix(p):
    for a, b in REF_FIX:
        p = p.replace(a, b)
    return p


def figure_block(num):
    cap = figcaps[str(num)]
    body = cap.split("| ", 1)[1] if "| " in cap else cap
    return (f'<figure><img src="figs/fig-{num:02d}.png" alt="Figure {num}">'
            f'<figcaption><b>Figure {num} |</b> {esc(body)}</figcaption></figure>')


def para_block(p):
    if p.startswith("\x00"):
        return f'<h4>{esc(p[1:])}</h4>'
    if p.startswith("•"):
        return f'<li class="bullet">{esc(p.lstrip("• ").strip())}</li>'
    return f"<p>{esc(p)}</p>"


def section(level, num, title, key, extra_figs=None):
    label = f"{num} {title}" if num and title else (title or "")
    out = []
    if label:
        aid = esc(key or label)
        out.append(f'<h{level} id="{aid}">{esc(label)}</h{level}>')
    if key:
        for p in paras.get(key, []):
            out.append(para_block(p))
        for f in AFTER_FIG.get(key, []):
            out.append(figure_block(f))
        for t in TABLE_AFTER.get(key, []):
            out.append(table_block(t))
        for f in (extra_figs or {}).get(key, []):
            out.append(figure_block(f))
    return "\n".join(out)


# ---------------------------------------------------------------- assemble
body = []
body.append(section(0, "", None, "Abstract"))
for level, num, title, key in STRUCTURE:
    body.append(section(level, num, title, key))
body.append('<h1 id="references">References</h1>')
body.append('<ol class="refs">' + "".join(
    f"<li>{esc(ref_fix(p))}</li>" for p in paras["References"]) + "</ol>")
body.append('<h1 class="apx">Appendix</h1>')
for level, num, title, key in APPENDIX:
    body.append(f'<h1 id="{esc(key)}">{esc(num + ". " + title)}</h1>')
    for p in paras.get(key, []):
        body.append(para_block(p))
        if p.startswith("\x00") and p[1:] in AFTER_FIG_APX:
            for f in AFTER_FIG_APX[p[1:]]:
                body.append(figure_block(f))
        if p.startswith("\x00") and p[1:] in TABLE_AFTER_APX:
            for t in TABLE_AFTER_APX[p[1:]]:
                body.append(table_block(t))


def toc():
    items = []
    for level, num, title, key in STRUCTURE:
        if title and level <= 2:
            label = f"{num} {title}" if num else title
            items.append(f'<div class="l{level}">{esc(label)}</div>')
    items.append('<div class="l1">References</div>')
    for level, num, title, key in APPENDIX:
        items.append(f'<div class="l1">Appendix {num} &nbsp;{esc(title)}</div>')
    return '<div class="toc">' + "".join(items) + "</div>"


STYLE = """
@page { size: A4; margin: 0; }
body { font-family: "Charter","Georgia","Times New Roman",serif; margin:0; color:#111; }
.page { padding: 20mm 18mm; page-break-after: always; }
.page:last-child { page-break-after: auto; }
h1 { font-size: 17pt; margin: 22px 0 10px; padding-bottom: 5px; border-bottom: 2px solid #4d6bfe; page-break-after: avoid; }
h2 { font-size: 13pt; margin: 20px 0 8px; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 16px 0 6px; page-break-after: avoid; }
h4 { font-size: 10.5pt; margin: 13px 0 5px; color:#1f2937; page-break-after: avoid; }
h1.apx { margin-top: 30px; }
p { font-size: 10pt; line-height: 1.62; margin: 0 0 9px; text-align: justify; }
li.bullet { font-size: 10pt; line-height: 1.62; margin: 3px 0 3px 6px; }
.cover { text-align:center; padding-top: 55mm; }
.cover h1 { font-size: 24pt; border: none; margin: 0 0 6px; }
.cover .sub { font-size: 13pt; color:#374151; margin-top: 10mm; line-height: 1.5; }
.cover .meta { font-size: 10pt; color:#6b7280; line-height: 1.9; margin-top: 14mm; }
.badge { display:inline-block; background:#4d6bfe; color:#fff; border-radius:4px; padding:3px 12px; font-size:10pt; }
.note { background:#f8fafc; border-left:3px solid #93c5fd; padding:10px 13px; font-size:9pt; color:#374151; text-align:left; margin-top:16mm; line-height:1.6; }
.toc { margin-top: 30mm; }
.toc div { font-size: 10.5pt; margin: 5px 0; color:#111; }
.toc .l1 { font-weight:700; margin-top: 9px; }
.toc .l2 { padding-left: 16px; color:#374151; font-size: 9.8pt; }
figure { margin: 14px 0 16px; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; }
figcaption { font-size: 8.2pt; color:#374151; line-height: 1.5; margin-top: 6px; text-align: justify; }
figcaption b { color:#111; }
.tblwrap { margin: 14px 0 16px; page-break-inside: avoid; }
table.tbl { border-collapse: collapse; width: 100%; font-size: 7.6pt; font-family: "Helvetica Neue",Helvetica,Arial,sans-serif; }
table.tbl caption { caption-side: top; text-align: left; font-size: 8.2pt; color:#374151; line-height:1.5; margin-bottom: 5px; font-family:"Charter",Georgia,serif; }
table.tbl caption b { color:#111; }
table.tbl th, table.tbl td { border: 1px solid #d1d5db; padding: 2.4px 4px; text-align: center; }
table.tbl th { background:#f3f4f6; font-weight: 700; }
table.tbl tr.sub th { background:#fafafa; font-weight: 400; color:#4b5563; }
table.tbl td.l, table.tbl th.l { text-align: left; }
table.tbl tr.grp td { background:#f9fafb; text-align: left; font-style: italic; color:#4b5563; }
table.tbl u { text-decoration: underline; text-underline-offset: 1px; }
.tnote { font-size: 7.6pt; color:#4b5563; line-height: 1.55; margin-top: -8px; text-align: justify; }
ol.refs { font-size: 8.4pt; line-height: 1.5; padding-left: 1.6em; column-count: 2; column-gap: 22px; }
ol.refs li { margin-bottom: 5px; text-align: left; }
"""

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>DeepSeek-V4.1-Flash Technical Report (English, re-typeset)</title><style>{STYLE}</style>
</head><body>
<div class="page cover">
  <div class="badge">English Edition · Re-typeset</div>
  <h1 style="margin-top:8mm">DeepSeek-V4.1-Flash</h1>
  <div class="sub">Pushing the Limits of KV Cache Compression</div>
  <div class="meta">
    DeepSeek-AI &middot; research@deepseek.com<br>
    Original: huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash<br>
    Re-typeset: September 11, 2026
  </div>
  <div class="note">
    This edition reproduces the original report's text, figures and tables in a
    web/print-friendly layout. Body text, figure captions and table values are
    extracted from the original PDF; bold and underlined cells are restored from
    the PDF's own font and vector data. Inline formulas are rendered as Unicode
    approximations &mdash; for typeset mathematics and exact pagination, refer to the
    original PDF (<b>DeepSeek-V4.1-Flash-Technical-Report-Original.pdf</b>).
  </div>
</div>
<div class="page">
  <h1 style="border:none;margin-top:0">Contents</h1>
  {toc()}
</div>
<div class="page">
{"".join(body)}
</div></body></html>"""

open("DeepSeek_V41_Tech_Report_English.html", "w", encoding="utf-8").write(HTML)
print("wrote DeepSeek_V41_Tech_Report_English.html",
      len(HTML.encode()), "bytes")
