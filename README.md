# DeepSeek-V4.1-Flash 技术报告 · 中英对照版 / 中文译本 / 英文重排版

> 收录 **DeepSeek-AI** 发布的 *DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression*（51 页，A4）的
> **官方英文原版 PDF**，以及据此制作的三个衍生版本：**中英对照版**、**中文全译本**、**英文重排版**（HTML + PDF）。

原文地址：<https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash>
**在线浏览（GitHub Pages）**：<https://moonquake2004.github.io/deepseek-v41-flash-zh/>

---

## 1. 四个版本

| 版本 | PDF | 页数 | 收录范围 | 特点 |
|---|---|---|---|---|
| **官方英文原版**<br>Original | [`pdf/…-Original.pdf`](pdf/DeepSeek-V4.1-Flash-Technical-Report-Original.pdf) | 51 | 全文 | DeepSeek-AI 原始排版，**技术细节与公式的权威依据** |
| **英文重排版**<br>English | [`pdf/…-English.pdf`](pdf/DeepSeek-V4.1-Flash-Technical-Report-English.pdf) | 38 | 全文含附录 | 文字、图、表重排为网页/打印友好的版式；表格加粗与下划线由原 PDF 字体与矢量数据还原 |
| **中英对照版**<br>Bilingual | [`pdf/…-中英对照版.pdf`](pdf/DeepSeek-V4.1-Flash-技术报告-中英对照版.pdf) | 52 | 摘要 + 第 1–6 章 | 英文原段在上、中文译文在下，逐段对照（128 组）；图 1–10、表 1–4 |
| **中文全译本**<br>中文 | [`pdf/…-中文译本.pdf`](pdf/DeepSeek-V4.1-Flash-技术报告-中文译本.pdf) | 48 | 全文含附录 | 纯中文排版；附录 A（作者名单）/ B / C 与参考文献完整收录，图 1–12、表 1–5 |

三种版本都提供网页版（HTML），可直接用浏览器打开、检索：

| 网页版 | 文件 |
|---|---|
| 英文重排版 | [`DeepSeek-V4.1-Flash-Technical-Report-English.html`](DeepSeek-V4.1-Flash-Technical-Report-English.html) |
| 中英对照版 | [`DeepSeek-V4.1-Flash-技术报告-中英对照.html`](DeepSeek-V4.1-Flash-技术报告-中英对照.html) |
| 中文全译本 | [`DeepSeek-V4.1-Flash-技术报告-中文译本.html`](DeepSeek-V4.1-Flash-技术报告-中文译本.html) |

网页版依赖同目录下的 `figs/`，请保持目录结构完整。

---

## 2. 内容与保真度

- **英文正文、表头、表内数据、图注**均从原 PDF 提取，**未作改写**。
- **表格中的加粗与下划线**不是按规则猜的：加粗取自 PDF 的字体信息（`URWPalladioL-Bold`），
  下划线取自 PDF 的矢量线段（短横线），两者都已与原版逐行核对。
  例：表 1 中 `DROP (F1)` 行的 88.6 与 88.7 同时加粗（同一水平，0.3 分差规则），而 87.9 既不加粗也不加下划线 —— 与原版一致。
- **插图**为从原 PDF 按图注位置裁切所得的原始位图（12 幅）。
- **段落结构**按 PDF 的文本块（block）还原 —— 该 PDF 的段落仅靠首行缩进区分，`pdftotext -layout` 不保留缩进，所以必须用 `-bbox-layout` 的 block 结构。

### 已知差异（三个衍生版本共有）

1. **公式为 Unicode 近似**：正文行内公式与附录 C 的推导式以 Unicode 数学字符近似还原，复杂排版公式（分式、上下标对齐）
   建议对照**官方原版 PDF**。
2. **附录 C 的公式顺序**：PDF 中公式块与正文块的文档顺序并不总是阅读顺序，重排后个别公式会出现在其所解释的句子之前；
   内容完整，但阅读顺序与原文略有出入。
3. **中英对照版不含附录**：对照版覆盖摘要 + 第 1–6 章（图 1–10、表 1–4）；附录 A/B/C（含图 11–12、表 5）与参考文献见其余版本。
4. **中英对照版的段落边界**：英文按 PDF 文本块切分、中文按自然段切分，个别位置的切分点与原排版略有差异，内容顺序与信息完整性一致。
5. 译文中的模型名、基准名、数据集名保留英文原写法。

---

## 3. 生成流程

```
官方原版 PDF
 ├─ pdftotext -bbox-layout   → 按 <block> 还原自然段
 ├─ pdftoppm -png + crop_figs.py   → 按「图注 + 最近两端对齐正文行」自动裁图（12 幅）
 ├─ PyMuPDF                  → 表格：单元格文本 + 字体（加粗）+ 矢量线段（下划线）
 ↓
extract_en.py / extract_en_full.py   英文段落提取（含图表内部文字噪声过滤）
extract_tables.py                    表格结构化（表 1–5 → JSON）
 ↓
build_bilingual.py   锚点 DP 对齐英中段落 → 中英对照 HTML
build_en.py          英文重排版 HTML
 ↓
Chrome headless --print-to-pdf  → 各版本 PDF
```

关键经验：

1. **段落提取不能用空行或缩进**，必须用 `-bbox-layout` 的 `<block>`；该 XML 含非法字符，不要用 ElementTree，用正则。
2. **中英段落对齐不能按长度比例硬切**（会整段错位），要用「引用 / 术语 / 数字」锚点做保序 DP 对齐。
3. **表格加粗不要用规则推导**：先用字体信息取真值。表 1 的 `DROP (F1)` 行就是反例 ——
   按「次优加下划线」推导会误判 87.9。
4. **表格下划线是矢量线段**，长度 4–45 pt 的是下划线，跨整列的是表格框线，用长度阈值区分。

---

## 4. 脚本

| 文件 | 作用 |
|---|---|
| `scripts/extract_en.py` | 提取正文英文段落（block 结构 + 噪声过滤） |
| `scripts/extract_en_full.py` | 同上，并额外提取参考文献与附录 A/B/C |
| `scripts/extract_tables.py` | 表格结构化：加粗（字体）、下划线（矢量线）→ `tables.json` |
| `scripts/crop_figs.py` | 按图注定位自动裁剪插图 |
| `scripts/build_bilingual.py` | 锚点 DP 对齐 + 生成中英对照 HTML |
| `scripts/build_en.py` | 生成英文重排版 HTML |

脚本按流水线顺序执行即可复现（需 poppler-utils、PyMuPDF、Pillow、Chrome）。

### DeepInfer 文档生成

| 文件 | 作用 |
|---|---|
| `scripts/build_deepinfer.py` | 翻译并生成《DeepSeek V4.1 Flash 推理部署技术问答》中英对照 HTML |
| `scripts/build_zhihu_report.py` | 翻译并生成《DeepSeek V4.1 Flash 大规模推理部署实践》（知乎技术报告）中英对照 HTML（中文原文在上、英文译文在下） |

---

## 5. DeepInfer 推理部署技术问答（新增）

> 译自 DeepSeek 开源推理框架 **DeepInfer** 仓库中的官方文档
> [`doc/inference_deployment_qa.md`](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/inference_deployment_qa.md)
> （*DeepSeek V4.1 Flash Inference Deployment Q&A*）。该文档聚焦于 V4.1 Flash 的**推理部署架构**，
> 并非模型技术报告 PDF。

在线页面：[`DeepSeek-V4.1-Flash-推理部署技术问答-中英对照.html`](DeepSeek-V4.1-Flash-推理部署技术问答-中英对照.html)

涵盖 12 节 Q&A：集群与存储、专家并行 / 数据并行负载均衡、KV 缓存存储与重计算、自动扩缩容与容错、低精度计算、算子实现、投机解码、异步调度、结构化输出、DeepSeek Recipe；含 2 张架构 / 性能图（取自原仓库 `doc/images/`）与 2 张数据表。

保真度说明：英文原文取自官方文档，未作改写；中文为对照译文，专有名词保留英文并首次出现处给出中文译名。

## 6. DeepSeek V4.1 Flash 大规模推理部署实践（知乎技术报告，新增）

> 译自 DeepSeek 官方知乎号于 **2026-10-20** 发布的技术报告
> [《DeepSeek V4.1 Flash 大规模推理部署实践》](https://zhuanlan.zhihu.com/p/2095560295930508953)。
> 这是 DeepSeek 在开源 DeepInfer / deepseek-recipe 当日发布的**正式技术报告**（非论文、非模型技术报告 PDF），
> 系统阐述 V4.1 Flash 推理系统的整体架构与关键实现。

在线页面：[`DeepSeek-V4.1-Flash-大规模推理部署实践-中英对照.html`](DeepSeek-V4.1-Flash-大规模推理部署实践-中英对照.html)
PDF：[`pdf/DeepSeek-V4.1-Flash-大规模推理部署实践-中英对照.pdf`](pdf/DeepSeek-V4.1-Flash-大规模推理部署实践-中英对照.pdf)

涵盖：三大设计目标、并行策略、DeepSeek Recipe 编解码（API 多协议适配 / Tokenizer 加速 / 流式输出解析）、四类负载均衡器与自动扩缩容、KVCache Storage（Block/SWA、3FS 分布式文件系统）、SWA Bounded Replay、DSpark 投机解码、异步调度（零开销批调度器）、结构化输出，以及 6 篇参考文献。

保真度说明：① 中文为**原文**、英文为对照**译文**；② 原文「架构示意图」因知乎图床防盗链无法内联，已用译注说明；③ 原文「线上统计数据」「离线基准」两节为性能图表，本页据公开报道中的官方数据重建了统计表；④ 专有名词（EP/DP/SWA/KV/EPLB/MoE 等）保留英文并首次出现处给出中文译名。

---

## 7. 免责声明

- 原报告著作权归 **DeepSeek-AI** 所有。本仓库收录官方原文以方便查阅，并提供**非官方**的中文译本与重排版，
  **仅供学习与技术交流**，不得用于商业用途。
- 衍生版本的译文与重排可能存在偏差，**技术细节请以官方英文原版为准**；若官方要求，可随时移除。
- 若有侵权，请联系删除。
