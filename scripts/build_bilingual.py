"""Build a bilingual (EN/ZH) side-by-side paragraph-aligned HTML report."""
import json
import re

# ---------------------------------------------------------------- English side
raw = open("raw.txt", encoding="utf-8").read()
raw_lines = raw.split("\n")

# abstract (lines between "Abstract" and "1. Introduction")
ai = next(i for i, l in enumerate(raw_lines) if l.strip() == "Abstract")
aj = next(i for i, l in enumerate(raw_lines) if l.strip().startswith("1. Introduction"))
abstract_en = re.sub(r"\s+", " ", " ".join(x.strip() for x in raw_lines[ai + 1:aj] if x.strip()))

en = json.load(open("paragraphs.json"))


def split_bullets(paras):
    out = []
    for p in paras:
        for q in re.split(r"\s+(?=•\s)", p):
            for r in re.split(r"(?<=\.)\s+(?=(?:Full|Reindex|Reuse) Mode\.)", q):
                r = r.strip()
                if r:
                    out.append(r)
    return out


en = {k: split_bullets(v) for k, v in en.items()}

TABLE_AFTER = {
    "4.3.2. Evaluation Results": [(0, "Table 1 | Comparison among DeepSeek-V4-Flash-Base, DeepSeek-V4-Pro-Base, and DeepSeek-V4.1-Flash-Base. All models are evaluated in our internal framework under the same setting. Scores within a 0.3 gap are treated as the same level; the best score in each row is in bold and the second is underlined.")],
    "5.1.4. Controllable Reasoning Effort in RL": [(1, "Table 2 | Mapping between the public API reasoning-effort tiers and the underlying scalar effort values b.")],
    "5.3.2. Evaluation Results": [(2, "Table 3 | Comparison between DeepSeek-V4.1-Flash and closed/open-source models. † denotes the text-only subset of HLE. The best results are in bold; the second-best are underlined.")],
    "5.3.4. Performance across agent scaffolds": [(3, "Table 4 | Performance across agent scaffolds at Max reasoning effort. All scaffolds use N=8 samples per task on DeepSWE v1.1 and N=3 on Terminal-Bench v2.1, with Linux containers, temperature 1.0, top-p 0.95, a 1M-token context window, and max_steps=500.")],
}

# figure captions
fig_caps = {}
for m in re.finditer(r"Figure (\d+) \| (.*?)(?=\n\s*\n|\n\s*\d{1,3}\s*\n)", raw, re.S):
    num = int(m.group(1))
    txt = re.sub(r"-\n", "", m.group(2))          # rejoin hyphenated line breaks
    txt = re.sub(r"\s+", " ", txt).strip()
    if num not in fig_caps or len(txt) > len(fig_caps[num]):
        fig_caps[num] = txt

# ---------------------------------------------------------------- Chinese side
html = open("DeepSeek_V41_Tech_Report_中文译本.html", encoding="utf-8").read()
zh_tables = re.findall(r"<table.*?</table>", html, re.S)
zh_secs, cur = [], None
for m in re.finditer(r"<(h2|h3|h4|p|li)\b([^>]*)>(.*?)</\1>", html, re.S):
    tag, attrs, txt = m.group(1), m.group(2), m.group(3)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    if tag in ("h2", "h3", "h4"):
        cur = {"title": txt, "paras": []}
        zh_secs.append(cur)
    elif cur is not None and "note" not in attrs and "warn" not in attrs and txt:
        cur["paras"].append(txt)
zh_by_title = {s["title"]: s["paras"] for s in zh_secs}

MAP = [
    ("Abstract", "摘要", "Abstract / 摘要"),
    ("1. Introduction", "1 引言", "1 Introduction / 引言"),
    ("2.1. Overview", "2.1 总览", "2.1 Overview / 总览"),
    ("2.1.1. Multimodal Architecture", "2.1.1 多模态架构", "2.1.1 Multimodal Architecture / 多模态架构"),
    ("2.2. Causal Encoder-Decoder (CED)", "2.2 因果编码器-解码器（CED）", "2.2 Causal Encoder-Decoder (CED) / 因果编码器-解码器"),
    ("2.3. Compressed Sparse Attention 2 (CSA2)", "2.3 压缩稀疏注意力 2（CSA2）", "2.3 Compressed Sparse Attention 2 (CSA2) / 压缩稀疏注意力 2"),
    ("2.3.1. Cross-Layer KV and Index Reuse", "2.3.1 跨层 KV 与索引复用", "2.3.1 Cross-Layer KV and Index Reuse / 跨层 KV 与索引复用"),
    ("2.3.2. Hierarchical Sparse Indexer", "2.3.2 分层稀疏索引器", "2.3.2 Hierarchical Sparse Indexer / 分层稀疏索引器"),
    ("2.4.1. Single-Pass mHC", "2.4.1 单趟 mHC（Single-Pass mHC）", "2.4.1 Single-Pass mHC / 单趟 mHC"),
    ("2.4.2. Engram", "2.4.2 Engram", "2.4.2 Engram"),
    ("2.4.3. DSpark", "2.4.3 DSpark", "2.4.3 DSpark"),
    ("2.4.4. FP4 Main KV Cache", "2.4.4 FP4 主 KV 缓存", "2.4.4 FP4 Main KV Cache / FP4 主 KV 缓存"),
    ("2.5. Optimization", "2.5 优化方法", "2.5 Optimization / 优化方法"),
    ("3.1.1. Multimodal Training Infrastructure", "3.1.1 多模态训练基础设施", "3.1.1 Multimodal Training Infrastructure / 多模态训练基础设施"),
    ("3.1.2. Attention Sharing Training for CSA2", "3.1.2 面向 CSA2 的注意力共享训练", "3.1.2 Attention Sharing Training for CSA2 / 面向 CSA2 的注意力共享训练"),
    ("3.1.3. Engram", "3.1.3 Engram", "3.1.3 Engram"),
    ("3.2. Inference System", "3.2 推理系统", "3.2 Inference System / 推理系统"),
    ("3.2.1. Persistent KV Cache Management", "3.2.1 持久化 KV 缓存管理", "3.2.1 Persistent KV Cache Management / 持久化 KV 缓存管理"),
    ("3.2.2. SWA Bounded Replay", "3.2.2 SWA 有界重放", "3.2.2 SWA Bounded Replay / SWA 有界重放"),
    ("4.1. Data Construction", "4.1 数据构建", "4.1 Data Construction / 数据构建"),
    ("4.2.1. Model Setups", "4.2.1 模型设置", "4.2.1 Model Setups / 模型设置"),
    ("4.2.2. Training Setups", "4.2.2 训练设置", "4.2.2 Training Setups / 训练设置"),
    ("4.3.1. Evaluation Benchmarks", "4.3.1 评测基准", "4.3.1 Evaluation Benchmarks / 评测基准"),
    ("4.3.2. Evaluation Results", "4.3.2 评测结果", "4.3.2 Evaluation Results / 评测结果"),
    ("5.1. Post-Training Pipeline", "5.1 后训练流水线", "5.1 Post-Training Pipeline / 后训练流水线"),
    ("5.1.1. Large-Scale Agent Task Synthesis", "5.1.1 大规模智能体任务合成", "5.1.1 Large-Scale Agent Task Synthesis / 大规模智能体任务合成"),
    ("5.1.2. RL in Synthesized Tasks", "5.1.2 在合成任务上做 RL", "5.1.2 RL in Synthesized Tasks / 在合成任务上做 RL"),
    ("5.1.3. Running Agents at Massive Scale: DSec", "5.1.3 大规模运行智能体：DSec", "5.1.3 Running Agents at Massive Scale: DSec"),
    ("5.1.4. Controllable Reasoning Effort in RL", "5.1.4 RL 中的可控推理力度", "5.1.4 Controllable Reasoning Effort in RL / RL 中的可控推理力度"),
    ("5.2. Asynchronous Post-training Infrastructure", "5.2 异步后训练基础设施", "5.2 Asynchronous Post-training Infrastructure / 异步后训练基础设施"),
    ("5.2.1. Overall Workflow", "5.2.1 整体工作流", "5.2.1 Overall Workflow / 整体工作流"),
    ("5.2.2. Mitigating Length Bias and Off-Policy Effects", "5.2.2 缓解长度偏差与离策略效应", "5.2.2 Mitigating Length Bias and Off-Policy Effects / 缓解长度偏差与离策略效应"),
    ("5.2.3. Performance Optimization", "5.2.3 性能优化", "5.2.3 Performance Optimization / 性能优化"),
    ("5.2.4. Large-Scale On-Policy Distillation", "5.2.4 大规模在策略蒸馏（OPD）", "5.2.4 Large-Scale On-Policy Distillation (OPD) / 大规模在策略蒸馏"),
    ("5.3.1. Evaluation Setup", "5.3.1 评测设置", "5.3.1 Evaluation Setup / 评测设置"),
    ("5.3.2. Evaluation Results", "5.3.2 评测结果", "5.3.2 Evaluation Results / 评测结果"),
    ("5.3.3. Performance across reasoning efforts", "5.3.3 跨推理力度的表现", "5.3.3 Performance across reasoning efforts / 跨推理力度的表现"),
    ("5.3.4. Performance across agent scaffolds", "5.3.4 跨智能体脚手架的表现", "5.3.4 Performance across agent scaffolds / 跨智能体脚手架的表现"),
    ("5.3.5. Multi-Agent", "5.3.5 多智能体", "5.3.5 Multi-Agent / 多智能体"),
    ("6. Conclusion, Limitations, and Future Directions", "6 结论、局限与未来方向", "6 Conclusion, Limitations, and Future Directions / 结论、局限与未来方向"),
]

W_EN, W_ZH = 1.0, 2.55   # information-density weights


STOPW = set("""the of and is are in to for with that as we by on be it this from which at an a our its
their they them these those such can may not but also more most other into over under than then when
where while during between within across about above after before because both each only same some
used using use into via per all any own so if no nor too very""".split())


def feats(t):
    """Anchor features shared by an English paragraph and its translation."""
    f = set()
    for m in re.finditer(r"([A-Z][a-zA-Z]{2,})\s*(?:et al\.?)?[,\s]*\(?(\d{4})\)?", t):
        f.add(("cite", m.group(1).lower(), m.group(2)))
    for m in re.finditer(r"\b([A-Z][A-Za-z0-9]{1,9})\b", t):
        w = m.group(1)
        if len(w) >= 2 and w.lower() not in STOPW:
            f.add(("term", w.lower()))
    for m in re.finditer(r"\d[\d.,/]*\s*(?:T|B|M|K|k|%|x|bit)?", t):
        s = m.group(0).strip().replace(" ", "").lower()
        if len(s) >= 2:
            f.add(("num", s))
    return f


def align_paras(e_paras, z_paras):
    """Order-preserving alignment of English and Chinese paragraphs using
    citation / term / number anchors, allowing n:m groupings."""
    ne, nz = len(e_paras), len(z_paras)
    FE = [feats(p) for p in e_paras]
    FZ = [feats(p) for p in z_paras]
    LE = [len(p) for p in e_paras]
    LZ = [len(p) for p in z_paras]

    def sim(es, zs):
        fa = set().union(*[FE[i] for i in es]) if es else set()
        fb = set().union(*[FZ[j] for j in zs]) if zs else set()
        anchor = len(fa & fb) / max(1, len(fa | fb))
        la = sum(LE[i] for i in es) * 2.2
        lb = sum(LZ[j] for j in zs)
        ratio = min(la, lb) / max(1.0, max(la, lb))
        return 0.82 * anchor + 0.18 * ratio

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def best(i, j):
        if i == ne and j == nz:
            return 0.0, ()
        if i > ne or j > nz:
            return -1e9, ()
        cands = []
        if i < ne and j < nz:
            s, path = best(i + 1, j + 1)
            cands.append((s + sim((i,), (j,)), ((i, i + 1, j, j + 1),) + path))
        if i < ne and j + 1 < nz:
            s, path = best(i + 1, j + 2)
            cands.append((s + sim((i,), (j, j + 1)), ((i, i + 1, j, j + 2),) + path))
        if i + 1 < ne and j < nz:
            s, path = best(i + 2, j + 1)
            cands.append((s + sim((i, i + 1), (j,)), ((i, i + 2, j, j + 1),) + path))
        if i < ne and j + 2 < nz:
            s, path = best(i + 1, j + 3)
            cands.append((s + sim((i,), (j, j + 2)), ((i, i + 1, j, j + 3),) + path))
        if i + 2 < ne and j < nz:
            s, path = best(i + 3, j + 1)
            cands.append((s + sim((i, i + 2), (j,)), ((i, i + 3, j, j + 1),) + path))
        if not cands:
            return -1e9, ()
        return max(cands, key=lambda x: x[0])

    score, path = best(0, 0)
    if score < -1e8:                       # fall back to proportional cutting
        ia, ja = joint_cut([len(p) for p in e_paras], [len(p) for p in z_paras],
                           min(ne, nz))
        return [(ia[i], ia[i + 1], ja[i], ja[i + 1]) for i in range(len(ia) - 1)]
    return list(path)


def joint_cut(len_a, len_b, k):
    """Cut both sides at the same *content progress* points so that block i of
    English covers roughly the same share of the text as block i of Chinese."""
    if k <= 1:
        return [0, len(len_a)], [0, len(len_b)]
    ca, cb = [0], [0]
    for x in len_a:
        ca.append(ca[-1] + x)
    for x in len_b:
        cb.append(cb[-1] + x)
    A, B = ca[-1] or 1, cb[-1] or 1
    n, m = len(len_a), len(len_b)
    ia, ja = [0], [0]
    for kk in range(1, k):
        t = kk / k
        lo_i, hi_i = ia[-1] + 1, n - (k - kk)
        lo_j, hi_j = ja[-1] + 1, m - (k - kk)
        if lo_i > hi_i or lo_j > hi_j:      # cannot split further
            ia.append(min(hi_i, n))
            ja.append(min(hi_j, m))
            continue
        i = min(range(lo_i, hi_i + 1), key=lambda x: abs(ca[x] / A - t))
        j = min(range(lo_j, hi_j + 1), key=lambda x: abs(cb[x] / B - t))
        ia.append(i)
        ja.append(j)
    ia.append(n)
    ja.append(m)
    # drop empty blocks
    return ia, ja


# figures to place after a given section
AFTER = {
    "Abstract": [1], "1. Introduction": [2, 3], "2.3. Compressed Sparse Attention 2 (CSA2)": [4],
    "2.3.2. Hierarchical Sparse Indexer": [5], "4.3.2. Evaluation Results": [6],
    "5.1.2. RL in Synthesized Tasks": [7, 8], "5.3.3. Performance across reasoning efforts": [9],
    "5.3.5. Multi-Agent": [10],
}
ZH_CAP = {
    1: "图 1 |(a) DeepSeek-V4.1-Flash 与同代模型在智能体基准上的性能对比。(b) 历代 DeepSeek 模型每 token 的全局 KV 缓存大小（字节）。相对 V4-Flash 与 V1，V4.1-Flash 的每 token 全局 KV 缓存分别缩减约 4 倍与 437 倍。",
    2: "图 2 | 历代 DeepSeek 模型的单 token 解码 FLOPs 随上下文长度的变化（BF16/FP8/FP4 按 1/0.5/0.25 加权）。V4.1-Flash 的解码 FLOPs 几乎不随上下文增长。",
    3: "图 3 | DeepSeek-V4.1-Flash 总体架构：40 层分为各 20 层的因果编码器与解码器；前两层用 SWA，其余用 CSA2；另含单趟 mHC、Engram、DSpark 与分层稀疏索引器。",
    4: "图 4 | CSA2 的三种工作模式（Full / Reindex / Reuse）。差异在于如何获得主 KV、索引器 K 与 Top-K 索引；绿色为当前层计算，黄色为复用的主 KV 与索引器 K，红色为复用的 Top-K 索引。",
    5: "图 5 | 分层稀疏索引器。解码器首个 Full 模式层选出 Top-512 索引并由被选块构建共享候选池，Reindex 模式层再从该池中选出各自的 Top-512 索引。",
    6: "图 6 | 三个基座模型在保留评测集上的每字节比特数（BPB）对比，V4.1-Flash-Base 在所有任务上 BPB 最低。",
    7: "图 7 | DeepSeek Harness Minimal 模式下，随 RL 训练规模扩展，各代码智能体基准性能持续提升；上下文扩展到 1M 后，超长时程任务（Terminal-Bench v3.0）继续改善。",
    8: "图 8 | 跨 Claude Code 多版本（左）与跨异构脚手架（右）联合训练时，性能随累积 RL 步数提升，评测集为 DeepSWE v1.1。",
    9: "图 9 | 性能与输出长度随推理力度的变化（八个推理密集基准平均；DeepSWE v1.1 基于 mini-SWE，Terminal-Bench v2.1 基于 DeepSeek Harness Minimal）。",
    10: "图 10 | 单智能体与多智能体配置在 ProgramBench（Almost@1）与 FrontierSWE v2（Mean@5）上的测试时算力扩展。",
}

HEAD = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>DeepSeek-V4.1-Flash 技术报告 · 中英对照版</title><style>
@page { size: A4; margin: 0; }
body { font-family: "PingFang SC","Hiragino Sans GB",sans-serif; margin:0; color:#111; }
.page { padding: 20mm 18mm; page-break-after: always; }
.page:last-child { page-break-after: auto; }
h1 { font-size: 22pt; margin: 0 0 4px; }
h2 { font-size: 14pt; margin: 0 0 14px; padding-bottom: 6px; border-bottom: 2px solid #2563eb; page-break-after: avoid; }
h2 .en { display:block; font-size: 10pt; font-weight: 500; color:#6b7280; margin-top:3px; letter-spacing:.2px; }
.cover { text-align:center; padding-top: 62mm; }
.cover .sub { color:#6b7280; font-size: 12pt; margin-top: 6mm; }
.cover .meta { color:#666; font-size: 10pt; line-height: 2; margin-top: 16mm; }
.badge { display:inline-block; background:#2563eb; color:#fff; border-radius:4px; padding:3px 12px; font-size:10pt; }
.pair { margin: 0 0 11px; page-break-inside: avoid; }
.en { font-size: 8.8pt; line-height: 1.55; color: #4b5563; border-left: 3px solid #93c5fd;
      padding: 2px 0 2px 10px; margin: 0; text-align: justify; }
.zh { font-size: 10pt; line-height: 1.7; color: #111; padding: 5px 10px 0 13px; margin: 0; text-align: justify; }
.zh ul, .zh ol { margin: 4px 0; padding-left: 1.5em; }
.zh li { margin: 2px 0; }
figure { margin: 12px 0; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; border:1px solid #e5e7eb; border-radius:4px; }
figcaption { font-size: 8.2pt; color:#555; text-align:left; margin-top:4px; line-height:1.5; }
figcaption .en { font-size:7.8pt; background:none; border:none; padding:0 0 3px; color:#374151; }
figure .cap-zh { font-size: 8.6pt; color:#111; }
table { border-collapse: collapse; width:100%; font-size:8pt; margin: 10px 0; page-break-inside: avoid; }
th,td { border:1px solid #d1d5db; padding:3px 6px; text-align:center; }
th { background:#eff6ff; }
td.l, th.l { text-align:left; }
.note { background:#f0f7ff; border-left:4px solid #2563eb; padding:8px 12px; font-size:9pt; margin:10px 0; border-radius:0 6px 6px 0; }
.toc { columns:2; column-gap:22px; font-size:9.5pt; }
.toc div { margin:2px 0; break-inside:avoid; }
.tbl { margin: 12px 0; page-break-inside: avoid; }
.tcap { font-size: 8.6pt; color:#374151; margin-bottom:5px; line-height:1.5; }
</style></head><body>
<div class="page cover">
  <div class="badge">中英对照版 · Bilingual Edition</div>
  <h1 style="margin-top:8mm">DeepSeek-V4.1-Flash</h1>
  <div class="sub">Pushing the Limits of KV Cache Compression<br><span style="color:#111;font-weight:700">突破 KV 缓存压缩的极限</span></div>
  <div class="meta">
    DeepSeek-AI · 技术报告<br>
    原文来源：huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash<br>
    排版方式：逐段对照（蓝色竖线内为英文原文，其下为中文译文）<br>
    译本生成：2026 年 9 月 11 日
  </div>
  <div class="note" style="text-align:left; margin-top:18mm">
    本对照版以「英文原段 + 中文译文」的方式逐段排版，便于核对术语与原文表述。
    公式、图表编号与原文一致；英文正文取自原报告 PDF，未作改动。
    收录范围：摘要 + 第 1–6 章正文，含图 1–10 与表 1–4；附录 A（作者名单）、附录 B/C 与参考文献未纳入，
    可在中文全译本（<b>DeepSeek-V4.1-Flash-技术报告-中文译本.pdf</b>）中查阅。
  </div>
</div>
"""

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

body = []
body.append('<div class="page">')
for en_key, zh_key, heading in MAP:
    en_paras = en.get(en_key, [])
    zh_paras = zh_by_title.get(zh_key, [])
    if not en_paras and not zh_paras:
        continue
    groups = align_paras(en_paras, zh_paras)
    en_parts = [" ".join(en_paras[a:b]) for a, b, c, d in groups]
    zh_parts = [zh_paras[c:d] for a, b, c, d in groups]

    body.append(f'<h2>{esc(heading.split(" / ")[0])}<span class="en">{esc(heading.split(" / ")[-1])}</span></h2>')
    for i in range(len(groups)):
        if not en_parts[i] and not zh_parts[i]:
            continue
        e = esc(en_parts[i]) or "—"
        zs = zh_parts[i] or ["—"]
        if len(zs) == 1:
            zh_html = f"<p>{zs[0]}</p>" if not zs[0].startswith(("•", "-")) else f"<ul><li>{zs[0].lstrip('•- ').strip()}</li></ul>"
        else:
            items = "".join(f"<li>{x.lstrip('•- ').strip()}</li>" for x in zs)
            zh_html = f"<ul>{items}</ul>"
        body.append(f'<div class="pair"><p class="en">{e}</p><div class="zh">{zh_html}</div></div>')

    for fnum in AFTER.get(en_key, []):
        cap_en = esc(fig_caps.get(fnum, ""))
        body.append(
            f'<figure><img src="figs/fig-{fnum:02d}.png" alt="Figure {fnum}">'
            f'<figcaption><span class="en"><b>Figure {fnum} |</b> {cap_en}</span>'
            f'<div class="cap-zh">{ZH_CAP[fnum]}</div></figcaption></figure>'
        )
    for tidx, tcap in TABLE_AFTER.get(en_key, []):
        if tidx < len(zh_tables):
            body.append(f'<div class="tbl"><div class="tcap"><b>{esc(tcap)}</b></div>{zh_tables[tidx]}</div>')
    if en_key in ("4.3.2. Evaluation Results",):
        body.append('</div><div class="page">')
body.append(
    '<h2>附录与参考文献<span class="en">Appendix &amp; References</span></h2>'
    '<div class="note">本对照版收录原报告摘要与第 1–6 章正文的逐段对照，'
    '并附正文全部 <b>10 幅插图（图 1–10）</b>与 <b>4 张表格（表 1–4）</b>。'
    '附录 A（作者名单）、附录 B/C（评测细节、指数 token 惩罚推导，含图 11–12、表 5）与参考文献'
    '已在中文全译本中完整收录，请参阅 <b>DeepSeek-V4.1-Flash-技术报告-中文译本.pdf</b>。</div>'
    '<div class="note" style="background:#fffbeb;border-left-color:#f59e0b">'
    '<b>译文说明：</b>英文正文取自原报告 PDF 并保留原始表述；中文为对应译文。'
    '为保证对照可读性，英文按原 PDF 的文本块切分，中文按自然段切分，个别位置的段落边界可能与原排版略有差异，'
    '但内容顺序与信息完整性与原文一致。公式编号、图表编号均与原文对应。</div>'
)
body.append("</div></body></html>")

open("DeepSeek_V41_技术报告_中英对照.html", "w", encoding="utf-8").write(HEAD + "\n".join(body))

# ---- alignment report for spot-checking -------------------------------------
print("=== alignment spot-check (EN head / ZH head) ===")
for en_key, zh_key, _ in MAP:
    en_paras, zh_paras = en.get(en_key, []), zh_by_title.get(zh_key, [])
    if not en_paras or not zh_paras:
        print(f"!! MISSING {en_key} en={len(en_paras)} zh={len(zh_paras)}")
        continue
    k = min(len(en_paras), len(zh_paras))
    groups = align_paras(en_paras, zh_paras)
    ep = [" ".join(en_paras[a:b]) for a, b, c, d in groups]
    zp = [" | ".join(zh_paras[c:d]) for a, b, c, d in groups]
    k = len(groups)
    print(f"[{en_key}] en={len(en_paras)} zh={len(zh_paras)} blocks={k}")
    for i in range(k):
        print(f"   {i:2d} EN: {ep[i][:58]}")
        print(f"      ZH: {zp[i][:44]}")
