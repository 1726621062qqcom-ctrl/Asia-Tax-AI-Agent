# 真实链路验收：旧/新检索与依据追溯（2026-10-13）

## 判定方案

本轮把“能检索”“能回答”“能追溯”分开判定，不能用某一层通过代替整条链路通过。

| 层次 | 实际入口与通过条件 |
|---|---|
| 同题旧/新检索 | 同一 20 道合成题分别经过旧云端 PostgreSQL 检索与新 C HTTP 法规检索＋云端裁定检索。15 道正例核对预期条款/案例定位，5 道负例必须明确无匹配；记录单题与汇总耗时、来源版本。 |
| 聊天回答 | 真实 DeepSeek、聊天流与相同的新检索配置。找到资料的题须有可核对的依据摘录和证据 ID；无匹配题不能编造结论。 |
| 规则到原文 | 从实际案件报告的 `rule_id → citation → passage` 逐一回读固定版本原文；核对文本 SHA-256、缺失引用、报告冻结哈希、用户隔离与事实更正后的状态。 |
| 税务正确性 | 只有人工专家对事实、期间、适用条款与结论逐题标注后才算通过。本轮没有专家金标准，因此不判定为通过。 |

## 运行记录

使用当前 `main` 工作树、固定 Li 提交 `771e4524961bcc36718db1c9331e7a5f4cda0ce7`；SQLite SHA-256 为 `2756d2862330cb746d4103f0e690182fdc9fe7b2436a4ac738b156416aeca143`，103 个源文件的可跨平台清单哈希为 `d4c5495302fc9c755eb750d70fc181dc99f58e6905a79709e93845ea7b5d37e9`。旧资料来自云端 PostgreSQL，真实模型是 `deepseek-flash`。所有提问、公司事实和金额都是合成测试数据；没有把密钥写入报告。

| 检查 | 结果 | 解释 |
|---|---|---|
| 固定发布物安装与哈希校验 | 通过 | 原来期望的源文件哈希已过期，安装器曾报 `release_hash_mismatch`；改为针对该固定提交的可跨平台哈希后可验证安装。 |
| 旧/新检索，同一 20 题 | 最终复跑旧 20/20、新 20/20；两者负例均 5/5 | 先前一轮旧路径 N04 暂时失败，单独与最终复跑均通过。只能证明修复了新路径已知的 9 道漏检，**不能声称新策略总体召回率提高**。两边资料库也不同。 |
| 真实聊天 8 题 | 7 道有依据题形成带证据 ID 的摘录草稿；1 道负例停在 `no_match`；引用/哈希检查 8/8 | 修复前 7 道命中资料却全部因 `evidence_restricted` 停下。修复后仅香港公开官方来源获准入模，仍为待复核摘录，不是完整的税务建议。 |
| PostgreSQL＋C HTTP＋固定规则＋真实模型 | 通过 | 隔离的 PostgreSQL 17.6 随机 schema、真实本机 HTTP 知识服务、固定规则与 DeepSeek 均运行；报告仍保持 `evidence_gate=insufficient`，未知事实导致规划阻塞。 |
| 规则追溯 | 6 个规则条目均有可回读依据，21 个法规定位、7 段裁定材料；47 段回读原文哈希全部正确 | 0 个缺失规则依据、0 个缺失领域引用；报告冻结哈希和用户隔离通过。固定规则对未知事实仍输出 `blocked`，证据门仍为 `insufficient`。 |
| 代码与前端构建 | Python 341 通过、11 跳过；前端构建通过 | 跳过的 11 项是会操作现有数据库的可选 live 集成测试。本轮使用随机隔离 schema 的联合脚本验证云端数据库，不对现有业务表做清理。 |
| 组合启动入口 | 本机 `/health` 为 200 且状态 `ok`，首页为 200 并加载 Taxora | 验证了服务能启动和提供页面；没有把这项当成登录或浏览器人工验收。 |

`DeepSeek` 在合成案情中独立提取了 8 个必需字段中的 7 个，遗漏/不准确的是 `payer_jurisdiction`。联合脚本随后明确补齐测试夹具事实，故不能把后续报告成功说成模型独立完成了全字段理解。

复现命令（需配置本地忽略的 `.env`；真实模型会产生 API 调用）：

```powershell
.venv\Scripts\python.exe -m scripts.evaluate_real_chain --output reports/strategy-comparison.json
.venv\Scripts\python.exe -m scripts.evaluate_combined_chat --output reports/chat-combined-grounding.json
.venv\Scripts\python.exe -m scripts.check_combined_live --env-file .env --output reports/combined-full-trace.json
.venv\Scripts\python.exe -m pytest -q
```

完成前端构建后，使用 `.venv\Scripts\python.exe -m scripts.run_combined` 在本机启动本轮实际验收过的组合路由；它在进程存活期间启动并回收本机 C 知识服务，避免 `.env` 未设置 `FSIE_AGENT_*` 时悄悄回到旧检索。打开 `http://127.0.0.1:8000`。这仍是本机服务，不是公网部署。

原始逐题结果保存在 Git 忽略的 `reports/`，避免上传模型输出和环境信息。代码内保留可重跑脚本与不含凭据的断言。未做浏览器人工验收、Supabase 邮箱端到端或真实客户资料测试；后续需要专家逐题给出标准答案，并用独立于开发调参集的新题评估召回和税务正确性。
