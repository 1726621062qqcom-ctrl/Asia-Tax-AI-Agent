# Taxrora

面向企业税务研究与顾问复核场景的东亚税务 AI 平台项目。项目以中国香港境外来源收入豁免征税机制（FSIE）为深度 MVP，并为中国内地、日本和韩国建立可扩展的官方资料与规则框架。

本仓库已完成 L0 内部研究原型工程验收（见 [L0 验收记录](docs/project/L0_ACCEPTANCE_RECORD.md)），尚不提供正式税务意见，也不是可供客户直接使用的产品；进入 L1 须先通过香港税务专家验证与安全门槛。

## 当前交付边界

- **L0 内部研究原型**：2026 年默认目标，只能用于受控研究和工程验证；
- **L1 封闭顾问试点**：必须通过香港税务专家验证、安全和运营门槛；
- **L2 正式客户能力**：不属于 2026 年默认范围。

香港是当前唯一的深度 MVP。中国内地、日本和韩国在保守资源基线下先交付 `source-catalog baseline`，额外工程与知识运营资源到位后再扩展为标准研究包。

## 核心文档

- [Project Framework — English](docs/architecture/PROJECT_FRAMEWORK.md)：当前项目框架图，区分已实现链路与待接通部分。

- [本地聊天 Demo 运行说明](docs/implementation/CHAT_DEMO_RUNBOOK.md)：运行 `make demo`，打开 `http://127.0.0.1:8000`。支持香港 FSIE 研究问答、候选事实更正、官方引用和条件化筹划路径；无模型配置时明确使用本地资料模式，不需要 PostgreSQL。

- [产品需求文档](docs/product/PRD.md)
- [技术路线图](docs/architecture/TECHNICAL_ROADMAP.md)
- [2026 项目计划](docs/project/PROJECT_PLAN_2026.md)
- [批判性文档审查报告](docs/reviews/2026-08-15-prd-roadmap-project-plan-plain-language-review.md)
- [文档导航](docs/README.md)

## 仓库结构

| 目录 | 当前用途 |
|---|---|
| `docs/` | 产品、架构、项目计划、审查和设计记录 |
| `apps/` | 本地聊天工作台与 FastAPI 服务 |
| `packages/` | 事实抽取、资料检索、咨询编排、规则、报告和持久化模块 |
| `knowledge/` | 可公开并允许版本管理的资料清单、标注定义和规则元数据 |
| `tests/` | 自动化测试、合成事实抽取及咨询行为评测 |
| `scripts/` | 知识包校验、语料整理和离线演示检查 |
| `infrastructure/` | 本地 PostgreSQL 配置 |

聊天 Demo 可独立运行；原有命令行规则评测与数据库链路继续保留。聊天输出仍为未经专业验证的研究内容，且不代表原有税务规则已扩展为完整咨询系统。

## 知识与数据安全

- 首版专业资料应优先使用可验证的官方来源；
- RAG 资料、确定性规则和案例评测必须分别管理；
- 不得提交客户案件、个人资料、密钥、`.env` 或受限原始资料；
- `knowledge/` 只保存获准版本管理的清单、元数据、标注规范和规则定义；
- 系统输出必须保留来源、规则版本和适用时间，且最终专业判断由合资格人员负责。

## 项目背景

本项目最初作为 TUM Project Study 开展，后续目标是在受控验证基础上逐步扩展为东亚税务研究与顾问辅助平台。
