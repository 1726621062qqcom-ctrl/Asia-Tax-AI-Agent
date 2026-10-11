# 合并编排工程验收与交接记录

日期：2026-10-11。代码基线为 `zijian-Luo / 1de0163`，Li 依赖为固定提交 `771e4524961bcc36718db1c9331e7a5f4cda0ce7`。安装、框架和逐项接手测试见 [合并 README](../../README_MERGED.md)。

本次交付包括共同事实模型、旧字段归属绑定、真实领域调用、固定结构和规划两模式、问题分类与回写、只读资料接口、组合来源路由、页面、合并研究稿/导出/复核、固定发布安装及复测脚本。代码具备可复测链路；真实模型和 PostgreSQL 的联合验收受现有环境阻塞，尚未达到方案 P4 全部外部依赖通过的门槛。

## 固定发布核验

| 项目 | 本次结果 |
|---|---|
| SQLite | 243703808 字节，完整性 `ok` |
| 数据库 SHA-256 | `2756d2862330cb746d4103f0e690182fdc9fe7b2436a4ac738b156416aeca143` |
| 代码/CSV集合 SHA-256 | `b1f2c38a996481f1d1099aae43f5cb2ed68e7e2abdb1a32863289306811dd921` |
| 集合范围 | 103 文件：tax_graph Python/CSV/JSON、official/tools Python、official 所有层级 CSV，包含 `official/labels/observed_rules.csv` |
| 上游 handoff 审计复跑 | 通过；396 文档、8438 条款、390 参数、31 个口径 ID；CSV/数据库一致，145 条口径引语检查通过，D14–D31 完整 |
| 规则编译 | 184 条，缺参数 0、缺法条引用 0；编译器仍列出 38 个未被规则使用的范围内参数，这不等于专业覆盖完整 |
| 上游 check_engine | 94 个候选、0 缺陷；包括上下界、事后请求和缩放等工程检查 |

安装器最初遗漏 `official/labels`，新的安装目录测试发现编译失败后已补齐，并扩大集合校验至所有 official CSV。旧集合哈希仅覆盖 97 文件；本文 103 文件哈希为当前安装/运行依据。固定提交和 SQLite 未变。

Li 的税额项 `cites` 是规则 ID。适配器现保留 `rule_citations/citation_map`，沿 compiled rule sources → params cite_id / 显式法条引用转换，才送到知识服务查原文；不会把规则 ID 当成法律条文 ID。

## 实测结果

| 检查 | 结果及范围 |
|---|---|
| Python 全套 | 337 项通过，11 项 live PostgreSQL 测试按原开关跳过；跳过不计通过 |
| 前端构建 | TypeScript 与 Vite 通过 |
| 浏览器 | 原 27 项全套通过；新增结构回答/部分稿/导出测试与原结构测试共 2 项通过。测试使用临时 SQLite、确定性模型替身、真实 Li 引擎 |
| 真实 C HTTP | 已启动独立 uvicorn 环回服务，实际 HTTP `/search`、`/evidence` → B → 真实 Li → 冻结报告 → 重新读取通过，结束关闭服务 |
| 合并报告示例 | 明确直接持股 CN→HK；固定 OP/ULT 两公司；21 个 FSIE 定位；24 次证据回读；该样例 19 个领域法条引用全部回读，未回读领域引用 0；最终仍标 `insufficient/unverified` |
| 两轮 planner | 真实引擎连续三次运行（初次+两次答案），共同事实和结果保存/恢复通过。关键金额答 unknown 时最终正确返回 blocked，不伪造可计算方案 |
| 状态回归 | 旧案迁移、双向绑定、未知/false、实体隔离、重复请求/异内容、owner/revision、失败不提交、暂缓/暂停、过期问题、专业权限/撤销、确认/部分稿/冻结/过期均覆盖 |
| 真实模型 | 未通过：初次 Python 无默认 CA；使用 OS truststore 保持 TLS 校验后，API 返回 HTTP 401 / invalid_api_key。没有用替身数据宣称真实模型通过 |
| PostgreSQL | 未通过：现有配置指向本机 5432，连接被拒绝；Docker daemon 不可用，启动已安装 Docker 后控制接口仍超时。没有连接成功或写入正式客户案件 |

报告使用单一 45 秒预算；普通会话原限额保留，显式生成合并报告允许最多 35 次原文回读（FSIE 7、裁定 7、领域 21）和 10 次检索尝试（最多 5 个请求各一次重试），共享回读缓存。超出或无法取得的引用保留缺口。预算扩大仅用于完整报告，不重置子流程预算。

真实 HTTP 样例的裁定来源使用明确空读者，验证来源路由和无法取得时的状态；没有冒称云端裁定库存已联通。真实模型+PostgreSQL脚本将从实际库读取裁定并检查其状态，待环境就绪后执行。

## 接手后的必要补测

1. **模型配置负责人**在本地提供有效模型密钥，确认原 API 地址/模型可用；不在 GitHub、聊天或截图中暴露密钥。macOS 若 Python 缺 CA，按 README 使用系统信任库，保持证书验证。
2. **数据库/环境负责人**启动专用 PostgreSQL，配置连接、创建测试 schema 权限，并按原迁移/导入流程保证官方裁定资料存在。提供 Supabase 邮箱认证配置供正常页面登录。
3. **运行组员**执行 `python scripts/check_combined_live.py --env-file .env`，保存脱敏结果，检查模型实际命中字段、人工补录区分、现有结构+多轮规划、刷新/owner 隔离、组合报告与真实裁定读取。
4. **Li 与税务负责人**复核 D14–D31、参数单位、规则适用期、上下界的未决条件及特殊安排。工程原文定位/哈希检查不能替代专业审核。

## 已明确保留的范围限制

- 首期 CNY；其他币种明确不计算。集团欧元收入等特定字段按字段单位填写，不因为交易币种是 CNY 就改写阈值单位。
- 旧事实仅在人工确认主体归属后绑定；法律判断不自动转成 Li 裁量。缺 `present` 的现有图分析会阻塞。
- Li 原文仅展示；普通用户不能直接回答 ruling/library。专业答复回读依据并记录哈希，仍需人工核实它与题目的关联和适用期。
- 当前最终批准门槛保留，Li 资料 `unverified` 和合成案情不能直接批准为正式意见。专家界面可记录退回或暂不能结论。
- `review_paid`、非 holding 模板、复杂组合、向量检索、Li 文档提取、自动换汇、跨账号专家分派与公网部署仍需逐项专项验收。
- 未复跑上游全部 battery、全文资料构建或向量模型；完成的是上述 handoff、rules、check_engine 与合并链路检查。

## 可复现入口

```sh
python scripts/install_li_release.py
python -m pytest -q
npm --prefix apps/web run build
python scripts/check_combined_local.py
# 需有效模型、专用 PostgreSQL 与原裁定资料
python scripts/check_combined_live.py --env-file .env
# 只测真实模型，明确不算 PostgreSQL 通过
python scripts/check_combined_live.py --model-only --system-trust --env-file .env
```

每次复测须区分真实依赖、模型替身和合成资料；不能仅用测试条数宣称外部联合验收或税务专业验收完成。
