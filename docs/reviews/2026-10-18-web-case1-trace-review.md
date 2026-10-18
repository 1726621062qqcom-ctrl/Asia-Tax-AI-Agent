# 网页案例与埋点核对

整理日期：2026-10-18。实际网页提交时间：2026-10-17 12:59:54（北京时间）。本次整理复用已完成的真实网页运行，没有重复提交或以API测试替代网页输入。

## 样例与结果

来源：`docs/product/HK_FSIE_USER_CASE_TEMPLATES.md` 的第一个虚构英文案例。香港跨国企业成员持有新加坡子公司35%股权，自2022年3月持有，2025年8月收取约180万新加坡元股息，外国税务证明尚不完整。

- Case ID：`8a53c87f-7ed3-447c-8cf5-a5cac2473802`
- Trace ID：`1fd7b0e8-b7a3-489a-864c-a04c877e42a1`
- Request ID：`2a179cef-9bb2-4fc5-8ea3-9f93091fc20e`
- Agent耗时13.632秒；120个事件；丢弃0个；6次模型调用、6次模型请求。
- 提供方上报prompt 16,104、completion 2,225、total 18,329 tokens。
- 执行状态completed，业务状态waiting_user，原因fact_collection；没有终止性执行错误，有1次路由校验拒绝并成功重试。

网页最终正文采用英文，按Current position、Conditions to check、Documents to request first、References组织。结合了35%持股、持股起始月份、三名员工职责和缺少税务证明等输入；末尾列出s.15K、s.15M、s.15N，并展示10个原文片段。未出现日志面板。此处核对呈现和执行路径，不代表法律表述已逐条审核通过。

## 实际调用顺序

| 阶段 | 日志证据 | 观察 |
| --- | --- | --- |
| route | #10、#19 | 首次invalid_route_shape（ValueError）被拒绝，第二次完成；合计5.934秒 |
| facts | #21 | acquisition_date只有月份，被精确日期保护移除；未补造某一天 |
| dispatch | #24 | dynamic_planner=true，harness_mode=tools，进入tool_harness |
| read_case_facts | #35–42 | 模型选择先读取已陈述事实和资料清单；服务端接受并执行 |
| check_fact_gaps | #52–59 | 模型选择先检查事实缺口，再决定检索；服务端接受并执行 |
| search_law | #69–96 | 查询FSIE股息的经济实质及参与豁免；检索返回3份证据、10段展示片段 |
| stop | #98 | search_law之后因waiting_user停止工具循环；不是模型主动选择finish |
| observe / validate | #101–119 | 进入最终生成和校验；生成使用英文，1次尝试，grounded |
| turn | #120 | 完成执行，保留fact_collection业务状态 |

工具选择说明是模型生成的简短决策摘要，不是内部逐字思维链。日志中的选择摘要为中文，而最终正文为英文；目前这不影响用户正文的语言。

## 暴露的问题及后续优先级

1. **路由错误定位还不够精确。** 当前日志只给出invalid_route_shape和ValueError，不能据此确定究竟哪个字段或枚举非法。建议增加安全的校验规则编号与字段名，不记录原始提示词或模型全文。
2. **资料检索被事实追问提前终止。** `packages/agent/hybrid.py` 的检索分支调用update_dialogue，发现问题后改为waiting_user；`packages/agent/tool_harness.py`见搜索工具带question便停止循环。因此本轮没有执行search_guidance。建议把“仍有待补事实”与“本轮资料检索完成”分开：缺事实可以阻止确定性结论，但不应自动阻止完成用户要求的已有资料研究。
3. **模型预算余量为零。** 2次路由、3次工具规划、1次最终生成恰好用完6次额度。本轮没有预算错误，但后续修复或独立复核缺乏余量。优先减少无必要的路由重试与重复规划，并为最终生成/复核预留额度，不能只扩大总预算。
4. **待补事实表达和状态不够一致。** 日志中存在question和waiting_user，网页正文主要给出材料清单，末尾是中文“核对案例事实”按钮。建议最终输出明确“哪些问题待答、为什么影响判断”，并让相关操作文案随回答语言一致。
5. **证据数量不等于法律校验通过。** evidence.admission记录verified_count=0；有3份来源、10段展示片段，只说明检索和引用链可追踪。不能把grounded或answer.validate完成理解为每一法律命题都已被独立核实。

## 本地记录

详细事件和轮次汇总仍在独立日志中：`data/local-setup/agent-logs/events.jsonl`及`runs.jsonl`。

本次另存的分析材料（均在Git忽略目录）：

- `data/local-setup/agent-logs/case1-web-trace.json`：该轮120个事件。
- `data/local-setup/agent-logs/case1-web-output.txt`：完成时网页DOM文本。
- `data/local-setup/agent-logs/case1-web-result.png`：当时网页截图，视口位于引用片段和输入框。

查询工具调用：

```sh
.venv/bin/python scripts/agent_logs.py show --trace-id 1fd7b0e8-b7a3-489a-864c-a04c877e42a1 --event tool. --limit 0
```

本次只完成网页运行和日志分析，没有修改业务流程。10月18日恢复整理时原浏览器标签已不存在，未为重拍截图而另起一轮。
