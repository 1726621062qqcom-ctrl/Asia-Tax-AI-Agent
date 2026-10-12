# Scripts

本目录用于可重复执行的资料处理、索引、验证、迁移和开发辅助脚本。

常用入口按用途分组。具体参数使用 `python scripts/<脚本名> --help` 查看；运行顺序与环境条件见[验收入口](../docs/verification/README.md)。

**启动与固定依赖**

- `run_chat.py`：启动 FastAPI 和构建后的前端。
- `install_li_release.py`：下载并校验集成文档指定的 Li 发布版本，安装在 Git 忽略的本地目录。

**资料与离线检查**

- `validate_fsie_package.py`：校验香港 FSIE 候选知识包的来源、规则、证据和虚构案例引用完整性。
- `inspect_ruling_sources.py`：检查四个官方裁定来源的内容保留情况，复用本地快照；运行结果保存在被 Git 忽略的原始资料目录。

**联调与评测**

- `check_postgres_acceptance.py`：新建一次性 PostgreSQL 数据库，验证迁移、知识构建、持久化与真实 HTTP/Li 合并链路，结束清理；原配置库不被迁移或清空。
- `check_combined_live.py`：真实模型和 PostgreSQL 联合验收，也支持互斥的 `--model-only` / `--database-only`；可用 `--model-env-file` 分开配置。运行说明见 [合并 README](../README_MERGED.md)。
- `evaluate_retrieval.py`、`evaluate_chat.py`：历史 A 侧检索与聊天题集复测，解释见[评测记录](../docs/project/evaluations/README.md)。
- `evaluate_b_workflow.py`：B 侧多轮业务脚本评测，输入与已知限制见[脚本说明](../evals/b_workflow/README.md)。

脚本应支持明确输入、可审计输出和失败状态，不得把密钥或客户数据写入仓库。
