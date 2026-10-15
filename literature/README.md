# literature：paper_list.txt 的文献原文与论文卡片

**范围**：`paper_list.txt` 的 A–G 节，共 71 条。H 节是一手法规，已在 `official/`，这里不收。当前结果见 [STATUS.md](STATUS.md)，逐条元数据见 `manifest.csv`，每篇的中性摘要见 [paper_cards/](paper_cards/README.md)。

## 1. 规则

```text
1. 优先收发表版（version of record）：出版商排版的最终版，或仓储里与之相同的副本。
2. 脚本下载：每个文件最多 3 次尝试，由一次 fetch 完成：
     第 1 次 curl
     第 2 次 curl_cffi（Chrome TLS 指纹，先访问落地页；可换一个备用的发表版地址）
     第 3 次 无头 Chrome，即“虚拟 web”：打开落地页后在页内取 PDF，不行再由浏览器下载
   查元数据、探测页面不计次数。仍失败就记录，不再尝试。
3. 只用正当来源：出版商、出版商或学会的开放平台、机构与学科仓储里的发表版、作者机构主页上的发表版。
   不用影子图书馆，不绕过付费墙或登录，不点选、不代解人机验证。
4. 脚本拿不到的，由用户手动下载（2026-10-05）。发表版拿不到时，用户采用了预印本或工作论文，
   这类文件名带 _preprint，manifest 的 version 列为 preprint。
5. 用户手动也找不到的，记为缺失，不再找。
6. 入库前看第一页：题目、作者、刊名或会议名、卷期页或文章号、DOI 或版权行，确认是哪个版本。
```

## 2. 布局

| 位置 | 内容 |
|---|---|
| `<ID>_<第一作者姓><年>_<短题>[_preprint].pdf` | 原文，字节不改；同一条的第二个文件（如更正）加后缀 `_correction` |
| `paper_cards/<ID>.md` | 论文卡片，规则见 `paper_cards/README.md`，验收记录见 `paper_cards/ACCEPTANCE.md` |
| `manifest.csv` | 每条一行：核对后的元数据、DOI 链接、状态、版本、来源、文件、`sha256`、尝试摘要、与清单不符之处 |
| `STATUS.md` | 由 `tools/build_manifest.py` 生成：统计、缺失条目、预印本条目、发表版条目 |
| `tools/items_src.json` | 人工核对的事实：发表版 DOI（无 DOI 时为题目、作者、出处）、手动文件及其版本、开放获取、与清单不符之处、备注 |
| `_work/items/<ID>.json` | 每条的记录，由 `tools/make_items.py` 从 `items_src.json`、Crossref 和尝试日志生成 |
| `_work/text/<ID>.txt` | PDF 文字层，每页以 `=== [p.N] ===` 开头；卡片的页码和引文以此为准 |
| `_work/log/<ID>__<file_key>.jsonl` | 每次下载尝试一行 |
| `_work/renames.csv` | 用户手动文件的改名记录，含 `sha256` |
| `_work/originals/` | 改名之外另作处理的原件（E5 的整本论文集） |
| `_work/quarantine/`、`_work/render/` | 失败时取回的页面、被拒收的文件；核对版本用的页面截图 |

## 3. 状态

| status | version | 含义 |
|---|---|---|
| `downloaded` | `published` | 有发表版文件 |
| `downloaded` | `preprint` | 只有预印本或工作论文文件 |
| `failed` | | 缺失：脚本和用户都没拿到 |

`source`：`fetch_lit.py` 为脚本下载，`user (...)` 为用户手动下载。`failure_kind`：`paywall` 付费墙，`human_verification` 人机验证，`blocked` 其他拦截，`no_online_copy` 无在线全文，`not_found` 地址失效，`other`。

## 4. 工具

Python 一律用 conda 环境 `pytorch`：`source /c/Coding/Anaconda/etc/profile.d/conda.sh && conda activate pytorch`

```bash
python literature/tools/fetch_lit.py meta --doi 10.1145/3473582            # Crossref + OpenAlex，含开放获取位置与版本
python literature/tools/fetch_lit.py meta --title "A Logic for Statutes"     # OpenAlex、Crossref、DBLP 题名检索
python literature/tools/fetch_lit.py probe URL [--browser]                   # 看落地页的 citation_pdf_url 与 PDF 链接
python literature/tools/fetch_lit.py fetch --id A1 --out literature/A1_Merigoux2021_Catala.pdf \
    --url https://dl.acm.org/doi/pdf/10.1145/3473582 --landing https://dl.acm.org/doi/10.1145/3473582 \
    --expect "programming language for the law"                              # 最多 3 次尝试
python literature/tools/fetch_lit.py render literature/A1_Merigoux2021_Catala.pdf --pages 1
python literature/tools/fetch_lit.py reject --id A1 --reason "accepted manuscript"   # 拒收后可用剩余次数重取
python literature/tools/fetch_lit.py attempts --id A1
python literature/tools/make_items.py                                        # 生成 _work/items/*.json
python literature/tools/build_manifest.py                                    # 生成 manifest.csv 与 STATUS.md
python literature/tools/extract_text.py                                      # 生成 _work/text/*.txt
python literature/tools/card_skeleton.py                                     # 生成卡片骨架（已有的不覆盖）
python literature/tools/check_card.py --all                                  # 检查卡片
```

本机实测（2026-10-04）：ACM 数字图书馆（偶有一次放行）、Wiley、SAGE、SSRN、OUP、PMC 对脚本和无头浏览器都弹出需要勾选的人机验证。Springer 对无订阅的文章返回 HTTP 204。IOS Press 只经页面按钮的 POST 表单给 PDF。
