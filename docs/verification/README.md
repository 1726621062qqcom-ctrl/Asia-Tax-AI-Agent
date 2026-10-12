# 当前 main 的验收入口

本页用于开始下一轮真实链路检验，详细安装命令以[集成运行说明](../../README_MERGED.md)为准。上次检查结果见[集成验收记录](../implementation/COMBINED_INTEGRATION_ACCEPTANCE.md)；它不是本轮结果。

2026-10-12 的首轮实测及两条评测线的判定方案见[真实链路冒烟记录](REAL_CHAIN_SMOKE_2026_10_12.md)。

## 先确认环境

1. 从项目根目录安装 Python 依赖并构建 `apps/web`；按集成运行说明安装固定版本 Li 组件。安装器会校验发布文件，校验失败不能视为已安装。
2. 在 Git 忽略的 `.env` 中配置云端 PostgreSQL、Supabase 邮箱认证与模型服务。不要把密钥写入命令、报告或版本库。
3. 运行 `python scripts/run_chat.py`，确认页面、登录和健康检查可用。数据存储在云端不等于前后端已经公网部署。

## 建议的检验顺序

| 阶段 | 入口 | 要记录的证据 |
|---|---|---|
| 代码与前端回归 | `python -m pytest -q`、`npm --prefix apps/web run build` | 通过、失败、跳过数量及提交号 |
| 数据库与 C 集成 | `python scripts/check_combined_live.py --database-only --env-file .env.integration` | 资料版本、引用回读、案件恢复与隔离、失败原因 |
| 真实模型联合链路 | `python scripts/check_combined_live.py --env-file .env.integration --model-env-file .env` | 实际模型调用、问答、来源、耗时与错误 |
| 页面人工操作 | 当前聊天工作台及测试账号 | 登录、三入口、事实确认、分析、刷新恢复和导出 |
| 质量比较 | [评测导航](../../evals/README.md) | 同题旧/新答案、来源命中、专家判定与耗时 |

一次性数据库全套复验可使用 `check_postgres_acceptance.py`，但它会创建、迁移并清理测试数据库；先阅读[运行说明](../../README_MERGED.md)确认所用连接。评测报告应分别标明工程通过、真实模型通过和税务专家认可；引用能回读只能证明可追溯，不能单独证明税务判断正确。

当前 `main` 使用固定版本 Li 组件；C 分支后续提交（包括新增的追溯检查）需要单独对比和集成，不能直接算作 `main` 已验收。早期 `demo/hk-web` 也仍是独立分支。
