# 抽取边界的模型对照（2026-10-14）

十个带出处的案例（4 个 K4 真实、6 个 K3 半合成），标准答案取案例文件 `provenance`：disclosed / derived 的值应读出，missing / synthetic 应答缺失。建模参数（present.payment、event.years 等）不计。

| 轮 | 代码 | 模型 | 披露值正确 / 86 | 推导值正确 / 60 | 错值 + 错填 | 不一致退回 | 调用数 | API 秒 |
|---|---|---|---|---|---|---|---|---|
| 1 `round1_strict/` | 改前（引文只忽略空白，JSON 严格） | flash | 83 | 27 | 10 | — | 149 | 2184 |
| 1 | 同上 | v4-pro | 70（6 项因引号写法作废，1 案例因控制字符崩溃） | 24 | 9 | — | 127 | 3537 |
| 2 `round2_relaxed/` | 引号归一 + JSON 非严格（评测侧打补丁） | flash | 86 | 28 | 10 | — | 151 | 2337 |
| 2 | 同上 | v4-pro | 81 | 28 | 12 | — | 147 | 3475 |
| 3 `round3_production/` | 生产代码改后（quotes.loose、samples=2、释义 + 守则、非严格 JSON） | flash | 83 | 22 | 4 | 9 | 286 | 2866 |

| 4a `round4a_patterns_raw/` | 正则定值 + 检索 k=3（查询无当事方名），逐段单读，程序解析数值 | flash | 45（16 冲突、22 缺、3 错） | 3 | 3 | — | 369 | 1126 |
| 4 `round4_k5/`、`round4_k8/` | 正则定值（名在句中）+ 检索 k=5 / k=8（查询带名） | flash | 56（22 冲突、4 缺、3 错、1 拒） | 12 / 16 | 4 / 5 | — | 595 / 952 | — |
| 4 `round4_qwen/` | 同 round4_production，模型换 qwen3.8-flash（DeepSeek 中断期间） | qwen3.8-flash | 68（7 冲突、8 缺、2 错、1 拒） | 10 | 4 | 冲突 7 | 1025 | 3074 |
| 5 `round5_en/` | 同 round4_production，字段词典与提示改英文（提示版本 2026-10-15-en） | flash | 72（7 冲突、5 缺、1 错、1 拒） | 9 | 4 | 冲突 7 | 145 新调用 + 880 缓存 | 690 |
| **4 `round4_production/`** | **正则只定位 + 检索 k=5 带名 + 逐段单读 + 程序解析（`抽取改造.md` §5–§7）** | flash | **72（7 冲突、5 缺、1 错、1 拒）** | 9 | **4** | 冲突 7 | 1025 | 3971（含三次累计；最终版零调用重放） |

端到端：`e2e_qwen.log`（三案例完整入口：登记簿查到、模型对文档没有的字段全答缺失）、`e2e_eur.log`（欧元收入三案例：两个程序读表零调用、Shein 走模型指认句子 + 程序解析币种，均与标准答案一致）。渠道 B、C 的程序路径（2026-10-15，不调模型）：`registry_check.py`（新加坡 5 家公司在 ACRA 全部查到，`round4_channels.txt`）、`tables_check.py`（六案例集团收入 5 个与标准答案一致，Shein 只有正文句、落到模型）。第 4 轮的脚本：`extract_eval3.py`（走生产代码 `tax_graph.llm.extract`，`--k --locate --no-patterns --no-dense --temperature --meta`）、`eval_summary3.py`（含冲突明细、按检索排名归因、覆盖率—错误率、蜕变测试）、`retrieval_recall.py`（不调模型，`round4_recall.txt`）。回复缓存 `out/llm_cache.sqlite`，向量缓存 `out/extract_vec_cache.sqlite`。当事方名在 `extract_eval3.NAMES`（人写的定义词）。结果与结论在 `抽取改造.md` §6。

第 3 轮剩下的 4 处都是取数口径之争，不是编造：两处对价在文档里有两个数或以外币计，一处只实缴了一部分，一处"首次取得日"与"持满 100% 日"之别。
脚本：`extract_eval.py`（第 1、2 轮，自带调用器）、`extract_eval2.py`（第 3 轮，走 `tax_graph.llm.extract` 与 `tax_graph.llm.deepseek`）、`eval_summary.py`。结果文件不含密钥。
