# Scripts

本目录用于可重复执行的资料处理、索引、验证、迁移和开发辅助脚本。

当前可运行：

- `validate_fsie_package.py`：校验香港 FSIE 候选知识包的来源、规则、证据和虚构案例引用完整性。
- `inspect_ruling_sources.py`：检查四个官方裁定来源的内容保留情况，复用本地快照；运行结果保存在被 Git 忽略的原始资料目录。
- `check_postgres_acceptance.py`：新建一次性 PostgreSQL 数据库，验证迁移、知识构建、持久化与真实 HTTP/Li 合并链路，结束清理；原配置库不被迁移或清空。
- `check_combined_live.py`：真实模型和 PostgreSQL 联合验收，也支持互斥的 `--model-only` / `--database-only`；可用 `--model-env-file` 分开配置。运行说明见 [合并 README](../README_MERGED.md)。

脚本应支持明确输入、可审计输出和失败状态，不得把密钥或客户数据写入仓库。
