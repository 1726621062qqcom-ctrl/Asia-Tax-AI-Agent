# Agent 独立日志系统

日期：2026-10-17。本系统替代原来的聊天执行记录面板。对话页面不展示调试记录，不提供日志下载或历史日志入口，聊天API不返回详细执行日志。

## 文件与记录方式

默认目录：`data/local-setup/agent-logs/`，Git已忽略。

| 文件 | 用途 |
| --- | --- |
| `events.jsonl` | 每发生一个事件立即追加一行JSON，支持执行中查看；包含节点、模型决策摘要、工具提议、实际参数、校验、执行结果和失败事件 |
| `runs.jsonl` | 每轮Agent结束后追加一行汇总：Trace ID、案件/请求ID、状态、耗时、模型请求/调用数、工具列表、拒绝事件数、已上报token用量、共享预算 |
| `events.1.jsonl`等 | 轮转历史，数字越大越旧 |
| `runs.1.jsonl`等 | 轮次汇总历史 |

两个流分别约5MB轮转，当前文件外保留3份历史。默认目录创建权限0700，文件0600；同一主机的Unix进程通过文件锁协调追加与轮转，线程也有互斥锁。日志写入失败只记录安全错误类型，不中断业务。

事件使用Trace ID关联同一轮，使用request_id对应请求，case_id关联会话；另有事件序号、UTC时间、相对毫秒时间及父span ID。同一请求的幂等重试不重新执行Agent，也不重复生成一份执行日志。

普通事件每轮最多250条，省略数量写入轮次汇总；保留错误事件。只有事件保存在日志里，详细日志不再写入新助手消息或案件文档。旧案件中已有的历史日志保持原存储状态，API返回前剔除对应字段，页面也已删除相关组件与类型。

## 本地查询

以下命令在项目根目录运行，不需要网页接口或新增外部日志服务。

```sh
# 最近20轮：时间、Trace ID、案件、结果、耗时、模型调用数、工具
.venv/bin/python scripts/agent_logs.py list

# 按案件查最近轮次
.venv/bin/python scripts/agent_logs.py list --case-id CASE_UUID

# 一轮的完整时间线
.venv/bin/python scripts/agent_logs.py show --trace-id TRACE_UUID --limit 0

# 只看工具规划、校验与执行
.venv/bin/python scripts/agent_logs.py show --trace-id TRACE_UUID --event tool. --limit 0

# 检查错误和校验拒绝
.venv/bin/python scripts/agent_logs.py show --errors --limit 50

# 汇总状态、模型调用、工具分布、拒绝原因、P50/P95耗时和节点平均耗时
.venv/bin/python scripts/agent_logs.py stats

# 输出机器可读结果，便于继续做分析
.venv/bin/python scripts/agent_logs.py show --trace-id TRACE_UUID --limit 0 --json

# 执行中实时查看事件
tail -f data/local-setup/agent-logs/events.jsonl
```

支持`--request-id`、`--directory`和`--json`。`list --errors`包含失败、部分失败和出现校验拒绝的轮次，便于发现后来修复成功的重试。`show --errors`仅显示error/rejected事件。统计默认覆盖保留文件中的所有匹配记录，`--limit`只限制列表/时间线展示。P50/P95使用nearest-rank定义；token仅统计提供方实际上报的计数，不估算未上报用量。

日志目录可通过启动进程环境变量`FSIE_AGENT_LOG_DIR`设置为项目data目录下的路径；值为`off`可关闭。默认无需配置，标准启动器及普通应用入口均写入默认目录。离线测试统一禁用真实日志输出，日志专项使用独立临时目录。

## 记录范围

- 聊天图：route、facts、consultation、fact_intake、reference_lookup、tool_harness、observe、validate，以及旧版retrieve/compose路径。
- 工具：当时开放的候选、模型选择摘要、查询参数、服务端接受/拒绝/修复/覆盖、实际调用、耗时和停止原因。
- 模型：调用与HTTP请求起止、路由/规划结构化决策、提供方上报的token数量。
- 证据和生成：检索、原文读取/缓存、入模与展示准入、来源定位、覆盖缺口、初次生成/修复/复核与校验结果。
- 其他分支：一般费用查询prepare/search/answer；正式分析前置校验和返回的规则节点结果。外部Li进程未改造其内部遥测。

记录中的“决策摘要”是模型返回的一句话说明，不能当作模型内部逐字思维链，也不能证明选择或业务推理正确。不记录完整提示词、原文全文、原始模型回答和事实字段值；查询及摘要会做凭据、邮件和手机号脱敏。对话文本与最终答案仍按原有产品流程保存，日志只保留分析所需元数据。

日志的完成状态描述Agent执行阶段，数据库提交及Agent启动前的认证失败不被伪装成Agent节点。进程突然终止时，已经追加的事件仍在，可能没有对应runs汇总；可通过show检查最后的started事件。轮转后只有保留范围内的事件可查询，不能把缺失历史当作未执行。

## 验证

新增与更新的测试覆盖：事件即时落盘、轮次汇总、token保留与脱敏、并发追加、权限及轮转、部分行恢复、写入失败隔离、CLI筛选与统计、幂等请求、失败轮次、聊天响应不含日志，以及旧记录从API剔除。网页回归检查发送与刷新后均无日志控件。

最终验证：Python **446 passed，11 skipped**；跳过的是需显式开启的云端集成测试。浏览器专项 **10 passed**，包含发送、刷新后都没有日志面板、导出或历史入口的检查。前端生产构建通过。

真实网页对原会话刷新后确认旧日志面板消失，再提交“请查询香港境外股息参与豁免的持股比例与持有期要求。”：

- 执行尚未结束时，events.jsonl已实时写入75个事件，runs.jsonl尚未生成。
- 完成后新增一条轮次汇总，Trace ID为`596a7352-d95c-49d1-827f-b25f838721a5`，4次模型调用、1次search_guidance，耗时约7.78秒。
- 提供方上报prompt 8634、completion 791、total 9425 tokens。该值仅是本轮样例，不代表平均开销。
- 用list、show --event tool.、stats三个命令读取到同一轮日志；工具提议、校验、查询、完成原因和节点耗时均可查询。
- 网页完成正常回答，执行记录控件数量为0。
