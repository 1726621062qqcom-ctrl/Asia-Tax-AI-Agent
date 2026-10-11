# Li × Zijian 第一条联调链路（历史阶段记录）

> 本文记录初始 MVP，不描述最终集成状态。共同事实、固定结构、报告和测试的后续实现见 [合并交接 README](../../README_MERGED.md)及[集成验收记录](COMBINED_INTEGRATION_ACCEPTANCE.md)。

2026-10-11，本地集成代码已接入 Zijian 工作区，使用 Li `771e4524961bcc36718db1c9331e7a5f4cda0ce7` 的完整发布快照。它是受控工程原型，尚未达到原方案的完整双编排验收。

## 已接通

1. **案情转换。** 用户在现有案件的“结构分析”面板保存明确的实体、持股、流和事件 JSON。`DomainCase` 校验角色、比例、日期及大小；桥接进程把它转换为 Li `Case`、`Event`、`Answers`，调用真实 `planner.plan`。这条路径没有从旧平面 facts 猜测公司归属。
2. **会话与存储。** Li 返回的问题、答案、候选结果、输入哈希和日期写入同一个 `chat_cases.document`，沿用 owner、revision、request_id 的隔离、乐观锁和重放回执。提交回答时先重新运行引擎，成功后一次保存；超时或失败不保存半次更新。修改现有事实会标记领域结果过期，需核对并重存结构案情。
3. **知识接口。** 独立只读服务从 Li `official.sqlite` 做 exact/BM25 检索，按引用区间重新读取原文并校验 SHA-256；通过 Zijian 已有 `CKnowledgeProvider` `/search`、`/evidence` 契约接到来源面板和 B 分析。香港《税务条例》的部分子条款有显式定位映射。单轮最多返回 12 段原文，未覆盖定位逐项写入缺口，避免超过 B 的 14 次读取预算。Li 资料目前仅供展示，`model_use=denied`，未经专业核验不放开结论。
4. **页面。** 结构分析面板可载入合成样例、保存、运行、逐题回答并在刷新后恢复。结果展示状态、候选数量、结构及模型税额界限。原“依据”面板在配置 C provider 后走 Li 知识服务。
5. **版本隔离。** 领域调用运行在一次性 Python 子进程；服务与子进程校验固定发布包的 SQLite 哈希及 `tax_graph` 下 Python/CSV/JSON、`official/tools` 下 Python、`official` 顶层 CSV 的集合哈希。结果记录 commit、输入哈希及分析日期。只允许同一发布版本，版本不匹配即拒绝运行。

## 本地运行

在仓库根目录安装本项目依赖，保留完整 Li 发布快照及真实 LFS `official/official.sqlite`。设置 `FSIE_LI_RELEASE_DIR` 为该快照的绝对路径；不要只复制源码或 SQLite。先启动知识服务：

```sh
python -m uvicorn apps.knowledge_api.main:app --host 127.0.0.1 --port 8010
```

然后设置 `FSIE_AGENT_PROVIDER=c`、`FSIE_AGENT_C_URL=http://127.0.0.1:8010`，启动 `python scripts/run_chat.py`。如设置 `FSIE_AGENT_C_TOKEN`，两进程用同一值。现有认证和案件数据库配置照原项目 `.env.example`；网页构建在 `apps/web` 执行 `npm run build`。知识服务只应监听环回地址。

可复现检查：

```sh
FSIE_LI_RELEASE_DIR=/absolute/path/to/release python -m pytest -q tests/integration/test_li_bridge.py
```

这组测试用真实 Li SQLite/CSV、真实 planner、B API 与本地案件数据库，另以进程内 HTTP 传输检验 C wire、原文回读、B 分析的资料预算及缺口。正式 PostgreSQL、真实模型和浏览器全链路尚未执行，不应把这些测试当成上线验收。

## 还要补的部分

- 统一事实模型：现有 B 平面 facts 与领域结构案情目前并列存储；需要稳定实体/流 ID、字段/单位/时间语义映射、旧案迁移和双向更新。缺乏归属的信息应由用户确认，不能自动填到某家公司。
- `assess_current` 固定结构分析、`review_paid` 事后分析、ruling/library 专业分流，以及 Li 结构结果与 B 正式报告/复核流程的统一入口。这些尚未开放。
- 21 个 B 节点定位的完整映射、Li 法规与原 B 裁定的组合路由、适用期边界、资料用途及专业核验。当前真实 B 分析能取得 Li 原文，但覆盖不足，会明确标为 `insufficient`。
- 业务表单与更多样例：目前需要输入结构 JSON，页面只展示一项可由用户回答的问题；复杂案情的分组填报、联合问题、冲突/暂缓状态和税额条件还需产品化。
- 专用 PostgreSQL、真实模型多轮、浏览器联调、超时/并发/旧版本回放及税务专家审查；通过后才能考虑封闭试点。

Li 侧已交付此版本所需的代码、资料与样例。上述项目属于我们自己的集成与验收工作，除非发现发布包本身错误，无需让 Li 重新实现 Zijian 系统。
