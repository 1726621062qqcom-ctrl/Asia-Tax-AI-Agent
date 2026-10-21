> 当前启动方式（2026-10-20）：先安装固定依赖 `python scripts/install_tax_engine_release.py`，再运行 `python scripts/run_chat.py`。本地和 Render 均读取 `config/runtime.json`，由 API 自动管理资料服务。以下日期记录中的本地开关状态是历史验收记录，不代表当前机器配置。以 `/health` 的 runtime 字段为准。详见 [部署说明](../project/RENDER_DEPLOYMENT.md)。

# 本地测试启动说明

配置日期：2026-10-16。

## 启动

在 Finder 双击 `start-local.command`，或在项目根目录运行：

```sh
./start-local.command
```

打开 http://127.0.0.1:8000，使用原有 Supabase 账号登录。在启动终端按 Ctrl+C 停止服务。重复启动前先停止已有进程，避免占用 8000 端口。

脚本使用本项目独立的 `.venv`、已构建的前端和当前 `main` 的 `scripts.run_combined`。macOS 证书通过 `truststore` 使用系统信任库，HTTPS 证书验证保持开启。

## 本地与云端边界

| 组件 | 运行位置 |
|---|---|
| React 前端与 FastAPI 后端 | 本机 127.0.0.1:8000 |
| 固定 tax engine 规则引擎、官方 SQLite 资料库及只读检索服务 | 本机；知识服务端口由 combined 启动器动态分配并自动清理 |
| 模型 | `.env` 指定的 DeepSeek 服务 |
| 账号认证 | `.env` 指定的 Supabase 项目 |
| 案件、对话及原有云端资料查询 | `.env` 指定的 Supabase PostgreSQL |

这不是完全离线部署。按照提供的连接配置，本地测试创建或更新的对话仍会写入同一个云端数据库；请使用合成测试案情。此次配置不复制云端用户记录，也不主动迁移或清空云端数据库。

## 本地文件

- `.env`：本机配置，Git 已忽略；包含凭据，请勿提交或截图分享。
- `data/local-setup/`：被忽略的旧配置备份、检查结果与依赖版本记录。
- `data/tax_engine/releases/771e4524961bcc36718db1c9331e7a5f4cda0ce7/`：当前主线要求的固定法规/引擎依赖，安装器校验来源代码与 SQLite 哈希。
- `.venv/`、`apps/web/node_modules/`：本项目独立依赖。
- `apps/web/dist/`：本地构建后的前端。

## 常用命令

```sh
# 修改前端后重新构建，然后重启服务
npm --prefix apps/web run build

# 运行离线测试：旧测试需要默认 legacy 配置；hybrid 专项测试自行指定模式
FSIE_RUN_INTEGRATION=0 FSIE_AGENT_ORCHESTRATION=legacy FSIE_AGENT_PROVIDER=legacy \
FSIE_AGENT_DYNAMIC_PLANNER=false FSIE_AGENT_HARNESS_MODE=rewrite \
  .venv/bin/python -m pytest -q

# 只读知识服务 + 合成案件的本地整合检查，不调用在线模型
.venv/bin/python scripts/check_combined_local.py
```

当前输出问题的诊断与输出格式设计保留在 `docs/archive/reviews/`。环境配置不包含对这些业务问题的修复；本地运行用于复现当前 main 行为。

2026-10-17更新：本地工作区已接入回答质量核心改造（未推送），包括按提问语言回答、工具材料统一生成、原文片段引用校验、月级日期保护和明确持股更正。实施及真实网页回归记录见 `docs/archive/reviews/2026-10-17-answer-quality-implementation.md`；上文的“复现main”描述对应初始环境配置，当前工作区包含后续修改。

## 配置验证记录

- GitHub `origin/main` 与本地一致：`22cdb92`。
- 前端 `npm ci` 和生产构建通过；Python 依赖检查无冲突。
- 固定规则/资料库安装器的源码与数据库哈希校验通过。
- Supabase PostgreSQL 只读连接通过，既有 `chat_cases`、`sources`、`legal_units`、`alembic_version` 表存在。
- Supabase 认证服务返回 200；DeepSeek 模型列表包含配置模型，最小合成 JSON 请求返回 200 并通过校验。
- 隔离运行配置后的离线测试：346 passed，11 skipped；跳过的是需要显式开启的云端集成测试。
- 本地只读 HTTP 知识服务与规则引擎联动检查通过：21 个 FSIE 定位、0 个缺失领域引用，使用隔离的合成案件库。
- 浏览器中本地登录通过，工作区及既有对话读取成功。

连接检查与测试日志保存在 Git 忽略的 `data/local-setup/`，不包含凭据。日常启动保持 `hybrid + combined`；上面的测试命令仅影响对应测试进程，不修改 `.env`。

## 动态工具规划（2026-10-17）

节点埋点写入独立日志：`data/local-setup/agent-logs/events.jsonl`实时保存事件，`runs.jsonl`保存每轮汇总，默认5MB轮转并保留3份历史。聊天里已移除日志面板、下载和历史入口，详细日志不随案件API返回。用 `.venv/bin/python scripts/agent_logs.py list`、`show --trace-id TRACE_UUID --limit 0`、`stats`查询。完整说明见 `docs/archive/reviews/2026-10-17-agent-logging-system.md`。原 `agent-traces.jsonl`保留为旧版历史文件，新日志使用上述独立目录。

本地 `.env` 已启用 `FSIE_AGENT_DYNAMIC_PLANNER=true`、`FSIE_AGENT_HARNESS_MODE=tools`，编排模式保持 `hybrid`。普通对话可按用户目标调用事实读取、缺口检查、法条/指引/案例检索；三个快捷按钮保留明确入口，后续普通输入由任务路由继续处理。已有待回答问题和事实冲突优先处理，显式多任务队列不再重复交给工具规划器执行。

共享预算仍为每轮 45 秒、最多 4 次工具动作、3 次检索；真实回答生成路径最多 6 次模型调用。重复工具调用、范围改变、事实确认和分析授权仍由程序校验。资源耗尽时保留已完成结果。

重启 `./start-local.command` 后生效；终端会显示实际编排模式和动态规划设置。若需关闭，将 `.env` 中动态规划设为 `false`、工具模式改回 `rewrite`，然后重启。

启用验证：工具编排、hybrid 及上下文回答专项共 150 项通过。使用真实配置模型、官方知识服务和隔离 SQLite 合成会话验证：普通对话 trace 包含 `tool_harness`，连续调用 `search_law`、`search_guidance`，以 `finished` 停止；用时约 12.5 秒、6 次模型调用、2 次检索。三个快捷入口分别进入 consultation/fact_intake/reference_lookup，保留澄清步骤。该真实调用中一个子结果的解释未通过引文校验，按现有策略回退为官方原文摘录；启用动态规划不代表每份解释都能通过核验。详细记录位于 Git 忽略的 `data/local-setup/dynamic-planning-smoke-2026-10-17.json`。


### 数据库与工具路由（2026-10-18）

`combined` 模式中，PostgreSQL 既保存 `chat_cases.document`，也提供已登记的 FSIE 指引、FAQ、示例和裁定；固定版本 `official.sqlite` 提供法条。`search_guidance` 按来源类型查询云端资料，`search_rulings` 查询裁定，旧 `search_cases` 调用会归一化为后者。数据库故障不会静默切换资料库。

普通资料查询先汇总证据再生成一次回答。事实状态和本轮相关缺口预先提供给调度器；材料缺失限制个案结论，不自动中断独立的法条/指引检索。日志的 `tool.coverage` 记录来源类型、候选条款定位及未定位问题；它不代表税务专家已验证命题。规则仍从 Git 版本包读取，未切换到云端空规则表。详细契约见 `docs/architecture/AGENT_TOOLS.md`。
