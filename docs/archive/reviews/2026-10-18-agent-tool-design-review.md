# Agent 工具与产品目标审查

实施更新：相关第一阶段代码调整及验证已记录于 [实施记录](2026-10-18-database-tool-implementation.md)。下文保留审查时的现状和分阶段建议。
日期：2026-10-18。基于当前本地代码静态检查，以及已完成的Case1网页日志；没有修改业务代码，没有新增线上测试或调用外部模型。

## 判断基准

README和PRD定义的核心目标是香港企业境外股息FSIE研究：自然语言收集事实、发现关键缺口、人工确认事实、执行版本化规则、引用官方来源、形成可复核的内部稿。中文或英文输入均应获得可读且语言一致的回答。普通资料问答无需先完成完整个案访谈；事实不足可以限制结论，不应阻止回答已经可以回答的部分。

工具设计应服务这些目标。现有6个业务工具加1个结束动作基本覆盖主干；问题优先级在工具职责、返回契约和调度逻辑，而不是数量。

## 当前可选工具

定义见`packages/agent/tools.py`；执行见`packages/agent/tool_harness.py`。

| 名称 | 实际功能与开放条件 | 建议 |
| --- | --- | --- |
| read_case_facts | 只读现有用户陈述；进入工具循环时默认开放；不确认事实 | 保留按需能力；常规调度直接使用预计算事实视图，避免为必读状态再花一次模型规划 |
| check_fact_gaps | 调用dialogue.gaps，按当前访谈目标列缺失/未知/冲突；默认开放 | 保留并改成按问题/判断分支检查，区分阻断项和后续证据项；不把所有缺项都变成立即追问 |
| search_law | HK范围且任务已有query时开放；映射kind=law | 保留；只返回可引用资料及覆盖信息，去除搜索内的答复生成和访谈推进 |
| search_guidance | 同上，映射kind=guidance | 保留；先修复实际来源类型过滤与能力检查，不能用法条命中冒充已查官方指引 |
| search_cases | 同上，映射kind=ruling | 保留但更名search_rulings以准确表达税务裁定检索；按需调用，不等同于所有司法判例搜索，也不证明事实相似 |
| prepare_analysis | 用户明确要求、没有本轮待写入事实修订、analysis_eligibility允许时开放 | 保留确认门槛；明确其生成内部待复核稿；不用于普通条件解释，不赋予批准权限 |
| finish | ToolDecision允许的结束动作；不在业务工具catalog描述中，提示词另行约定 | 作为控制动作显式描述；增加结构化结束原因，并由服务端检查用户所问部分是否已交付 |

除finish外，当前工具决策只接受query（搜索必填，其他不接受）及reason摘要；身份、权限和写入上下文由服务端掌握。这一边界应保留。未来增加参数应采用按工具区分的schema，不能让所有工具共用任意参数字典。

## 已有能力与可选工具的区别

- search_evidence/get_evidence是知识Provider接口，已经负责搜索、版本绑定和原文读取；不是额外的LLM可选工具。无需为了“工具更多”再重复实现读取API。
- compose_answer/validate_answer及grounded响应是内部生成和引用校验步骤，不在上述工具目录；应继续作为交付前的必经步骤。
- analysis_policy/report_proposal及chat.analysis已有规则分析和复核状态，不应新增一个绕过事实确认的自由分析工具。
- domain_bridge已有结构规划、现状评估、已支付情形复核，以及独立的问答、证据和专业审核流程；这些通过专门模块运行，没有作为聊天ToolName暴露。若未来从聊天进入，应先以“启动受控结构分析”的适配入口复用现有流程，不能让模型直接调用专业裁定或批准操作。
- chat.expenses为普通费用研究独立分支，已有检索/解释流程，但不属于FSIE工具循环；未来共用检索基础设施时必须保留主题隔离。
- 固定快捷入口和auto入口的图路径不同。hybrid._path只在dynamic+tools+auto等条件下进入工具循环；这不表示快捷入口没有业务流程。不能要求每个按钮都强制运行同一串工具。

## 核心问题与证据

### P0：搜索工具包含过多业务副作用

tool_harness.execute把搜索交给hybrid.execute。后者会检索、compose_answer、validate_answer，并针对uses_case调用update_dialogue。存在待问问题时workflow变成waiting_user；tool_harness再据此直接停止循环。

Case1实际为read_case_facts→check_fact_gaps→search_law→waiting_user，未继续搜索指引。120事件、13.632秒、6次模型调用，其中路由重试2次、工具规划3次、最终生成1次。代码路径还会先构造extractive结果，随后最终生成grounded回答。当前不能将这些中间处理都描述成重复模型调用，但确实存在检索与呈现、访谈职责耦合。

应改为搜索只读且返回证据；工具循环按任务覆盖情况决定补检索；全部证据统一合并后仅在最终交付阶段组织回答和追问。缺事实只阻断依赖它的结论。

### P0：工具名与Provider能力不完全一致

RoutedKnowledgeProvider仅把ruling路由到裁定Provider，law/guidance都交给同一个law Provider。apps/knowledge_api/main.py的/search仅专门处理ruling，其余分支未按law/guidance过滤doc.type；来源虽带source_type，未据请求kind强制筛选。因此在该Provider路径中，search_guidance不能保证只返回指引。LegacyKnowledgeProvider的数据库路径则有law/guidance分类，不能把问题泛化为所有Provider都如此。

建议Provider公布支持的jurisdiction/topic/source_types/date_coverage；候选工具按真实能力开放，搜索返回必须核对来源类型。不支持指引时明确coverage缺失，不自动把法条改标成指引。可检查已加载资料类型，不要仅凭配置认定有指引。

### P0：规划观测不足

observation里的案件状态仅有fact_fields、has_conflicts和has_pending_question；read_case_facts执行后只加入reason_code。check_fact_gaps增加字段名，搜索结果增加evidence_count和粗粒度reason_code。规划器看不到主题覆盖、缺失法条、来源类型是否合适等结构化信息，难以据此判断研究完成。

建议每个结果提供统一结构：tool_status、covered_issues、uncovered_issues、evidence_refs、source_types、date_applicability、blocking_fact_gaps、nonblocking_fact_gaps、next_options、warnings。字段采用受控枚举或经校验元数据，不让模型的“已覆盖”摘要替代证据判定；不要把完整原文或无关历史复制进规划提示词。

### P1：缺口检查过于接近完整访谈清单

dialogue.required_fields按consultation_goal等计算必需项；full_analysis会展开资金流、参与和经济实质信息。Case1的缺口中包括抵销、资金池、代付等字段，尽管本轮用户主要要条件解释和材料清单。它们可以记录为待核对，但不应全部作为回答当前问题的前置门槛。

建议传递受控purpose/issue_scope；输出事实缺失与证据缺失的区别、影响分支和优先级；已有明确路径时先询问相关分支，不对所有可能资金安排机械追问。仍保留未知状态和月份精度，不自动补造日期。

### P1：搜索参数与改写约束不足以表达研究子问题

公开ToolDecision仅有query；底层SearchRequest已经支持jurisdiction、date、kind、locators等。validate_call把所有搜索中的不同改写合并计数，出现第二种不同改写可能触发rewrite_limit；这可能把经济实质和参与豁免两个合法子问题误作重复改写。

建议将issue_id及检索目的纳入任务计划，在每个子问题内限制重试，并保留总预算。query负责检索措辞，法域、期间和显式编号来自可信任务状态；如模型提议locator，只允许已提供/已检索/规则映射内的定位，不能开放任意编号绕过现有保护。

### P1：完成条件与预算

finish目前重点检查是否至少完成搜索，而不验证用户问题各部分交付情况；waiting_user又能在搜索后直接终止。预算虽为最终生成预留1次调用，但遇到路由重试和多主题检索时，独立复核余量不足。

建议使用任务清单与服务端结束校验：已答复、证据不足并明确说明、或确需补充后才能继续。确定的状态读取/缺口计算优先在代码中直接执行，模型只选择有意义的检索分支；预留最终生成与必要修复预算，无需每个节点都再调用模型。

## 推荐的下一版边界

| 层 | 能力 | 执行方式 |
| --- | --- | --- |
| 任务前置 | 语言、场景、范围、交易选择、当前事实视图、缺口/可分析状态 | 现有路由加确定性检查；避免反复调用LLM读取状态 |
| 可选研究工具 | search_law、search_guidance、search_rulings | 由模型按当前问题选择；返回统一只读证据结构 |
| 按需事实工具 | read_case_facts、check_fact_gaps | 保留给明确梳理请求或大型案件的分块访问；普通流程可直接用预计算视图 |
| 受控分析 | prepare_analysis | 沿用确认事实、版本、资格与人工审核门槛 |
| 必经交付 | 证据合并、结论与事实/来源映射、生成、去重、语言和引用校验 | 服务端必经步骤，不由模型选择是否跳过 |
| 控制 | finish/需补充/部分交付 | 显式原因和服务端完成检查 |

新增能力优先补“问题—事实—规则—证据覆盖表”和Provider能力元数据，不必立刻增加模型可选工具。建议先作为内部确定性函数；以后只有确有按需成本或访问分块需求时，再暴露为evaluate_case_readiness/check_evidence_coverage等只读工具。

暂不新增任意网页搜索、任意SQL、任意代码执行、自动确认事实、自动批准报告工具。与当前MVP的可追溯研究目标相比，这些不是回答质量问题的优先解法。

## 实施与验收顺序

1. 修复来源类型契约；拆开搜索与访谈推进、答复生成；保留现有身份、版本、哈希、权限保护。
2. 建立结构化覆盖观测与按目的缺口检查；改为证据汇总后一次交付；修复结束条件和预算分配。
3. 再优化子问题检索、裁定命名、按实际能力开放工具；结构分析适配入口作为后续范围。

验收至少复跑：一般条件问题、Case1长案例、只问参与豁免、纯英文、已知月份但无日期、个人主体、缺指引来源、缺裁定来源、多问题检索、事实冲突、明确请求正式内部分析、快捷按钮与auto入口。检查应覆盖实际Provider集成；现有test_tool_harness中“请求kind正确”不能单独证明实际返回来源类型正确。

成功标准包括：无无关重复追问；不会用法条冒充指引；已有资料可回答的部分不被缺事实阻断；回答正文和操作文案语言一致；引用末尾集中且无重复；未知不被当成否；确认/审批门槛不能由模型越过；日志可说明每次工具选择、覆盖变化与停止原因。该标准验证工程行为，不代替税务专家审核。
