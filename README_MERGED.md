# Zijian × Li：合并编排与数据库联调交接

这份文档是 `zijian-Luo` 分支的集成入口。目标是让一个案件里的聊天、结构计算、资料检索和研究报告连起来，下一位组员可以按本文安装并复测。当前交付是内部研究原型，税务口径仍需专业负责人复核。

## 1. 框架怎么分工

- **Zijian 的编排**负责访谈、识别任务、事实修改/确认、暂停恢复、案件保存、用户隔离和报告复核。原有 Hybrid/LangGraph 流程保留。
- **Li 的编排**包含结构搜索、规则计算、上下界分析、追问和事后请求处理。本次接入真实 `planner.plan` 和固定结构计算；不是只把 Li 当知识检索器。
- **知识接口**把 Li 的法规/参数资料接到已有 `KnowledgeProvider`。明确选择 `combined` 时，法规走 Li 只读服务，裁定走原 PostgreSQL 资料；每个来源保留原文版本、引用及哈希。
- **数据库**分工保留：PostgreSQL 保存案件进度；Li SQLite/CSV 是固定发布版本的知识依赖。没有把 244 MB 数据库再提交一次到这个分支。

```mermaid
flowchart TD
  U[聊天与结构分析页面] --> B[Zijian 会话编排 / DomainCoordinator]
  B --> F[唯一事实源 canonical_fact_records]
  F --> P[旧 FSIE facts 兼容视图]
  F --> C[Li Case / Answers 投影]
  P --> G[Zijian FSIE 规则链]
  C --> L[Li 一次性子进程：规划或固定图计算]
  L --> Q[事实 / 行动 / 专业判断问题]
  Q --> B
  B --> K[统一 KnowledgeProvider]
  K --> S[Li 官方资料只读 HTTP 服务 / SQLite]
  K --> R[原 PostgreSQL 裁定资料]
  G --> O[同一事实版本的研究稿 / 哈希 / 最终复核]
  L --> O
  B --> DB[PostgreSQL chat_cases：整轮一次提交]
```

**一轮操作的提交人只有 Zijian。** Li 子进程只收到案件快照，没有模型或案件数据库密钥。计算成功后，答案、结果和运行记录一起保存；计算失败不会只保存答案。`owner` 隔离案件，`revision` 拦住旧版本更新，`request_id` 用于重放。相同请求号换内容会被拒绝。

## 2. 已实现和当前边界

| 功能 | 当前行为 |
|---|---|
| 共同事实模型 | schema `2.0.0`；记录值、地址、来源、单位、状态、修订和确认；旧案按需迁移并保留原 facts 快照 |
| 两边同步 | 原 facts 与 Li 输入都是共同记录的投影；只有人工确认的字段归属建立绑定，禁止把一个事实复制给多家公司 |
| 现有结构 `assess_current` | 要求明确 `present`；只计算既有公司/持股，拒绝新增或迁移公司；不会偷偷改成结构设计 |
| 结构比较 `plan_structure` | 调用 Li planner；保留上游候选、问题种类和排序；目标是候选集内先比较税额上界，不代表现实世界全局最优 |
| 已缴事项 `review_paid` | 已接固定图/claims 的实验入口，完整业务时效与专业验收未完成；不要作为第一轮验收目标 |
| 回答与恢复 | 类型校验、事实未知、暂缓、暂停/恢复；过期问题拒绝；刷新能恢复本案件 |
| 主聊天联动 | 运行结果和下一题写入对话；可在结构面板答题，也可输入 `结构答复：答案`。普通聊天继续原编排 |
| 专业问题 | `ruling/library` 不开放给普通用户；指定复核者可提交带可回读依据的答复，记录依据哈希。当前裁量只支持有利判断 `yes`，不支持不利裁量自动执行 |
| 合并研究稿 | 确认当前事实后生成；未完整时须明确同意部分稿；已确认旧字段归属的现有结构附加 Zijian FSIE 规则链；保留两种结果及缺口；映射案件的报告共用证据缓存；普通分析最多 14 次回读，用户明确生成的合并报告限 35 次（FSIE 7、裁定 7、领域 21），检索最多 10 次（最多 5 个请求各含一次重试），全稿共用 45 秒预算，超出部分逐项留缺口 |
| 原文定位 | FSIE 的 21 个定位按 7 个父条文回读，再验证子段位置和哈希；未定位/失效/受限均留缺口 |
| 资料用途 | Li 原文目前允许展示、禁止发送给模型；工程可定位不等于已经通过税务专业审核 |
| 计算币种 | 首期支持明确的 **CNY**；缺币种拒绝，HKD/SGD 返回 `unsupported`，不暗自换汇。集团欧元收入等规则字段仍按其指定单位填写 |

首期业务表单覆盖直接持股股息；复杂结构可用高级 JSON。其他五种模板及二模板组合有 API 输入支持，但没有声称逐个完成业务验收。向量检索、Li 文档提取器、自动换汇、多用户专家协作界面和公网部署不属于这次已验证交付。

## 3. 文件导航

| 位置 | 看什么 |
|---|---|
| `packages/domain_bridge/state.py` | 唯一事实源、迁移、旧字段绑定、Li 投影 |
| `packages/domain_bridge/coordinator.py` | 调用、题目过期判断、答案、暂停、专业答复、报告的事务协调 |
| `packages/domain_bridge/bridge.py`、`worker.py` | 案件校验、固定发布校验、子进程、真实 Li 调用 |
| `packages/domain_bridge/reporting.py` | 冻结事实/结果/证据的合并研究稿与 Markdown |
| `apps/knowledge_api/main.py` | Li 的只读 `/search`、`/evidence` 服务 |
| `packages/agent/providers.py`、`knowledge.py` | 原来源、Li 来源组合路由和父子条文校验 |
| `apps/api/chat.py` | 已登录用户的案件、结构、报告和复核接口 |
| `apps/web/src/components/StructurePanel.tsx`、`DomainResult.tsx` | 表单、题目、计算结果、研究稿下载 |
| `tests/integration/fixtures/holding.synthetic.json` | 可分享的 CNY 合成样例 |
| `tests/integration/`、`apps/web/tests/structure.spec.ts` | 自动联调回归与浏览器测试 |
| `scripts/install_li_release.py`、`check_combined_live.py`、`check_postgres_acceptance.py` | 固定依赖安装、真实模型/数据库复测、一次性 PostgreSQL 全套验收 |
| `docs/implementation/COMBINED_INTEGRATION_ACCEPTANCE.md` | 本次实测结果、局限和后续责任人 |

## 4. 新组员安装

需要 Python 3.11+（本次使用 3.12）、Node.js 20.19+ 或 22.12+、Git，以及可连接的 PostgreSQL。Windows 建议 WSL；下面命令以 macOS/Linux 为例。

```sh
git clone --branch zijian-Luo https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent.git
cd Asia-Tax-AI-Agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/install_li_release.py
npm --prefix apps/web ci
npm --prefix apps/web run build
cp .env.example .env
```

安装脚本从 GitHub 下载固定提交 `771e4524961bcc36718db1c9331e7a5f4cda0ce7` 的代码/CSV及真实 LFS SQLite，校验后原子安装到忽略目录 `data/li/releases/<commit>/`。它不跟随 Li 分支最新 HEAD 自动漂移。若本机 Python 缺省 CA，可安装 `truststore` 并用 `python scripts/install_li_release.py --system-trust`，保持 TLS 验证。网络限制环境可使用已取得的完整快照：

```sh
python scripts/install_li_release.py --from-directory /absolute/path/to/Li-release
```

安装内容必须包含 `official/labels/*.csv`，它是规则编译的依赖。不要仅复制 `tax_graph/` 或仅复制数据库。校验失败时不能关闭校验；重新取得同一提交的完整资料。首次联网下载约 244 MB 数据库。

## 5. 配置和启动

在 `.env` 填写已有环境信息；不要提交或在群里发送密钥：

```dotenv
FSIE_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DB?sslmode=require
FSIE_MODEL_BASE_URL=https://YOUR_CONFIGURED_PROVIDER/v1
FSIE_MODEL_API_KEY=YOUR_LOCAL_KEY
FSIE_MODEL_NAME=YOUR_MODEL_NAME
FSIE_AUTH_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
FSIE_AUTH_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
FSIE_AUTH_SITE_URL=http://127.0.0.1:8000
FSIE_AGENT_ORCHESTRATION=hybrid
FSIE_AGENT_DYNAMIC_PLANNER=false
FSIE_AGENT_HARNESS_MODE=rewrite
FSIE_AGENT_PROVIDER=combined
FSIE_AGENT_C_URL=http://127.0.0.1:8010
# JSON 数组；填 Supabase 用户 UUID（不是邮箱、也不是 user: 前缀）。默认无人有权限。
FSIE_AGENT_REVIEWER_IDS=[]
```

默认用安装目录，无需填写 `FSIE_LI_RELEASE_DIR`；使用外部完整快照时填绝对路径。可选 `FSIE_AGENT_C_TOKEN` 两边共用，知识服务与 B 均读取 `.env`。知识服务只监听环回；迁到远端需 HTTPS、令牌和访问控制。

用专用测试数据库运行现有迁移与知识装载流程，参见 [云端研究链路](docs/project/CLOUD_KNOWLEDGE_SLICE.md)和 [认证说明](docs/project/TAXORA_AUTH.md)。`chat_cases` 在服务初始化时创建；不要拿新的 URL 当作已有案件迁移工具。原裁定库需要有已经导入的 `legal_units/sources` 等表；空库会显示裁定资料不可用。

有本机 Docker 的组员可以先启动仓库自带数据库：

```sh
docker compose -f infrastructure/postgres/docker-compose.yml up -d
python -m alembic upgrade head
```

数据库连接必须与这个环境匹配；这条命令不会替你配置云端账号或填充裁定资料。

启动两个终端（都激活虚拟环境并位于仓库根目录）：

```sh
# 终端 1
python -m uvicorn apps.knowledge_api.main:app --host 127.0.0.1 --port 8010
# 终端 2
python scripts/run_chat.py
```

打开 http://127.0.0.1:8000 并登录。可先访问 http://127.0.0.1:8010/health；返回 `knowledge_ready=true` 表示固定资料已装好。正式入口保留邮箱认证，测试服务的身份替身不用于正常启动。

## 6. 建议先跑的自动检查

```sh
python -m pytest -q
python -m pytest -q tests/integration
npm --prefix apps/web run build
cd apps/web
npx playwright install chromium
FSIE_TEST_PYTHON="../../.venv/bin/python" \
FSIE_LI_RELEASE_DIR="$(pwd)/../../data/li/releases/771e4524961bcc36718db1c9331e7a5f4cda0ce7" \
npm test -- --workers=1
```

macOS 已有 Chrome 时，可设 `PLAYWRIGHT_CHANNEL=chrome`。浏览器测试启动临时 SQLite 案件库、确定性模型替身和真实 Li 引擎；不能把它当成真实模型/云端数据库验收。旧 PostgreSQL 集成测试默认跳过，需按其 `FSIE_RUN_INTEGRATION` 开关在专用环境启用。如果没有 Li 发布物，相关真实引擎测试会跳过；交接验收必须检查跳过原因。

真实 HTTP 知识服务与合并报告的本地复测（不调用模型，案件库为临时 SQLite）：

```sh
python scripts/check_combined_local.py
```

真实模型与 PostgreSQL 复测（仅发送合成案情）：

```sh
python scripts/check_combined_live.py --env-file .env --output data/combined-live-result.json
```

数据库未就绪时，可加 `--model-only` 单独测两轮模型与 Li，此时输出明确标识 SQLite，不能算 PostgreSQL 通过。模型未就绪时，可加 `--database-only` 测真实 PostgreSQL、真实 C HTTP、Li 及裁定回读，输出明确标识模型 `not_called`。两种单项模式互斥。配置分开存放时，用 `--model-env-file` 指定另一份本地模型配置，数据库仍从 `--env-file` 读取。

macOS Python 缺省 CA 文件时，可先安装 `truststore` 并加 `--system-trust` 使用系统已信任证书；始终保留 HTTPS 校验。`401/invalid_api_key` 需配置负责人在本地更新有效密钥。

脚本在指定 PostgreSQL 新建随机测试 schema，测试案件/恢复/隔离/报告，结束清理该 schema；原公共知识表仅读取。运行账号必须能建 schema。输出不包含连接串/密钥，包含真实模型命中的字段、人工补录步骤后的结果、法规/裁定覆盖数和状态。**它会调用配置的模型 API，可能消耗用量。**模型识别缺字段时，脚本单独记录人工确认的合成样例补录，不把补录算成模型准确率。

数据库完整验收另有一个入口：

```sh
python scripts/check_postgres_acceptance.py --env-file .env.integration --system-trust
```

先把专用 PostgreSQL 连接写入本地 `.env.integration` 的 `FSIE_DATABASE_URL`。服务器需安装 pgvector，账号需能创建数据库。没有服务器时，可用仓库已有的 `infrastructure/postgres/docker-compose.yml` 启动本地环境。`--system-trust` 仅在安装了 `truststore` 时使用，其余机器可以省略。

这个脚本新建随机数据库，执行迁移、规则包导入、官方资料构建、`tests/persistence` 和真实 HTTP/Li 合并验收，最后删除自己创建的库；不会迁移或清空连接配置中原有的数据库。资料快照保存在忽略目录，网页与清单的哈希差异会记录下来。模型测试明确跳过，单独补测。输出和脱敏子步骤日志默认在 `data/` 下。

2026-10-11 已用 PostgreSQL 17.11 / pgvector 0.8.7 跑通：持久化检查 14 项通过、2 项模型检查跳过；10 份官方资料解析出 697 个单元；真实 HTTP 合并报告取得 21 个法规定位和 7 段裁定。脱敏结果见 [PostgreSQL 验收结果](docs/implementation/COMBINED_POSTGRES_RESULT_2026_10_11.json)。本次还补齐 Alembic 的聊天表元数据与 Source 地区索引声明，验证降级保留聊天数据及 RLS、再升级继续使用同一案件。

本次联调机器另保留了项目内的隔离数据库运行时及 `.env.integration`，均不上传。本机可用 `data/local-postgres/runtime/bin/pg_ctl -D data/local-postgres/cluster -l data/local-postgres/server.log start` 启动，`data/local-postgres/runtime/bin/pg_ctl -D data/local-postgres/cluster stop` 停止。这份运行时只适用于本机；其他组员按自己的 PostgreSQL 环境配置连接。

## 7. 手工验收：下一位组员逐项测试

只用上述合成样例；每一步记录案件 ID、模式、修订、现象和缺口，不记录密钥。

1. **现有结构**：新建案件 → 结构分析 → 载入合成示例 → 选择“只分析现有结构” → 确认合成资料 → 保存 → 运行。应只有 `OP/ULT` 两家公司、1 个候选；返回税额范围和缺口，而不是新增控股公司。
2. **结构比较**：另建案件，同样例改成“比较新结构方案”，保存后运行。应进入真实 planner 的候选比较和追问；记录候选数量，不把待补状态当成成功税务方案。
3. **数值/布尔/日期回答**：按题目提示填写，不把“不知道”输入成 0 或 false。关键金额未知可导致 `blocked`，这是合法结果。明确的 false 必须保留。
4. **主聊天回答**：已有当前结构问题时输入 `结构答复：1000000` 或 `结构答复：未知`。应保存一次用户消息、同一地址事实和新结果；重复点击同一请求不能重复提交。
5. **暂缓与暂停**：暂缓一题后应转到其他问题；暂停后不接受领域答案；恢复重新计算并恢复问题。刷新后状态仍存在。
6. **字段映射**：先在聊天/事实面板记录香港收款、中国内地付款、CNY 金额与日期，再从当前事实生成草稿。核对 OP/ULT/股权边及明确的 `present`；确认绑定后保存。修改聊天金额，应同步到结构事件且旧结果过期；改结构金额，应同步到已绑定的聊天字段。未映射的法律判断不能自动复制。
7. **旧题/并发**：打开两个页面，一个修改事实，另一个用旧 revision 提交。应返回 409、重新读取；旧题不能覆盖新事实。
8. **研究稿**：运行后先确认结构事实；尚有缺口时须选“同意部分研究稿”。生成后在主对话查看结构、税额、依据与缺口并下载 Markdown。建立映射的现有结构稿还应显示 FSIE 规则链。修改事实后旧稿应显示过期。
9. **专业边界**：普通账号不应能回答 ruling/library。配置的复核账号可填写依据引用对象；不能用不存在/不能回读的依据。最终报告仍须专门复核，不因模型计算成功自动批准。
10. **知识和币种失败**：查 FSIE 条款，核对 21 个定位；停止知识服务后应提示不可用，不能偷偷用其他资料替代。清空币种应拒绝；改 HKD/SGD 应明确不支持，不能输出 CNY 税额。
11. **失败不提交**：自动测试覆盖 worker 超时/失败；案件 revision 与答案应保持原状。线上手工复测可在专用测试环境临时降低超时，不修改正式配置。
12. **账号隔离**：另一个账号不能读取该案件；当前专家配置仅支持账号自己的案件，跨账号分派审核尚需另做授权模型。

## 8. 如何判断交接完成、还缺什么

工程验收必须同时保留：Python/构建/浏览器结果、固定发布哈希、真实模型与专用 PostgreSQL 复测结果、至少一个现有结构和一个多轮规划案例。`needs_input`/`blocked` 可以是正确结果，但不能写成“已完成免税结论”。真实依赖不可用时要明确记录，不能用 Mock 报通过。

| 后续事项 | 找谁 | 具体怎么补 |
|---|---|---|
| 真实模型与联合验收 | 模型配置负责人 + 运行组员 | 更新有效模型密钥后先跑 `--model-only`，再用已备好的专用 PostgreSQL 跑完整 live 脚本；本机数据库已实测通过 |
| 正常账号页面验收 | 环境负责人 + 运行组员 | 配置 Supabase 邮箱认证，用测试账号按第 7 节走完页面；现有自动浏览器测试使用测试认证 |
| 税务口径、适用期、专业裁量 | Li 协调知识维护者及税务负责人 | 核对 D14–D31、参数单位、上下界条件、现有图与 planner 的差异，提供有出处的认可/退回记录 |
| 换汇与 HKD/SGD | 集成侧 + 税务负责人 | 明确汇率来源、日期、阈值单位和税额折算，再补样例与测试；不要只改币种标签 |
| 复杂模板与已缴请求 | 集成侧 + Li | 逐模板提供真实跑通的合成样例、期限/关闭字段、预期结果及专业复核，再开放业务入口 |
| 案件专家协作与部署 | 集成侧 / 环境负责人 | 跨账号审核授权、发布配置、日志/备份与操作流程；本次默认环回运行 |

## 9. 常见问题和回退

- `domain_unavailable`：安装固定依赖或核对绝对路径；不要把 LFS 指针当 SQLite。
- `release_hash_mismatch`：源文件/CSV/数据库不配套。下载同一提交重新安装，保留旧包供复现。
- `domain_execution_failed`：先跑 integration 测试、检查 `official/labels/observed_rules.csv`；API 不返回内部 traceback/密钥。
- `blocked` 且提示缺 `present`：现有安排未明确。holding 直接持股样例是 `HOLD:null, financing:"EQUITY", payment:false`；复杂案件必须按其真实安排填写。
- `blocked` 且提示 `unbounded`：关键金额未知，不能计算有限方案；补真实有据金额或保留阻塞研究记录。
- `knowledge_unavailable`：检查 8010 服务、令牌、发布物；`combined` 的裁定另检查原知识库。
- `revision_conflict/question_changed`：重新读取当前案件后答当前题，不重用旧题 ID。
- `review_incomplete`：缺口/证据门槛未满足。当前 Li 资料未经专业核验，完整工程运行也不自动满足正式批准条件。

回退时先备份测试/案件数据库，再切回集成前 Git 提交；新 schema 保留迁移前事实快照。回退旧程序不会迁回全部领域记录，不应继续编辑同一个测试案件来验证新流程。需要升 Li 版本时另开变更：重新审查配套资料、更新固定提交与两项哈希并复跑上述矩阵；不要改运行目录冒充旧发布。
