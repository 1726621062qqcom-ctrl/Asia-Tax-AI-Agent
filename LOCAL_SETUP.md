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
| 固定 Li 规则引擎、官方 SQLite 资料库及只读检索服务 | 本机；知识服务端口由 combined 启动器动态分配并自动清理 |
| 模型 | `.env` 指定的 DeepSeek 服务 |
| 账号认证 | `.env` 指定的 Supabase 项目 |
| 案件、对话及原有云端资料查询 | `.env` 指定的 Supabase PostgreSQL |

这不是完全离线部署。按照提供的连接配置，本地测试创建或更新的对话仍会写入同一个云端数据库；请使用合成测试案情。此次配置不复制云端用户记录，也不主动迁移或清空云端数据库。

## 本地文件

- `.env`：本机配置，Git 已忽略；包含凭据，请勿提交或截图分享。
- `data/local-setup/`：被忽略的旧配置备份、检查结果与依赖版本记录。
- `data/li/releases/771e4524961bcc36718db1c9331e7a5f4cda0ce7/`：当前主线要求的固定法规/引擎依赖，安装器校验来源代码与 SQLite 哈希。
- `.venv/`、`apps/web/node_modules/`：本项目独立依赖。
- `apps/web/dist/`：本地构建后的前端。

## 常用命令

```sh
# 修改前端后重新构建，然后重启服务
npm --prefix apps/web run build

# 运行离线测试：旧测试需要默认 legacy 配置；hybrid 专项测试自行指定模式
FSIE_RUN_INTEGRATION=0 FSIE_AGENT_ORCHESTRATION=legacy FSIE_AGENT_PROVIDER=legacy \
  .venv/bin/python -m pytest -q

# 只读知识服务 + 合成案件的本地整合检查，不调用在线模型
.venv/bin/python scripts/check_combined_local.py
```

当前输出问题的诊断与输出格式设计保留在 `docs/reviews/`。环境配置不包含对这些业务问题的修复；本地运行用于复现当前 main 行为。

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
