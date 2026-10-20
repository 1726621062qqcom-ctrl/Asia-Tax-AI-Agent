# 结合现有数据库的工具调整方案

实施更新：相关第一阶段代码调整及验证已记录于 [实施记录](2026-10-18-database-tool-implementation.md)。下文保留审查时的现状和分阶段建议。
日期：2026-10-18。范围：当前本地代码、固定Li资料库只读查询、已配置PostgreSQL只读聚合查询。没有读取私人对话内容，没有修改数据库、迁移或业务代码。

## 一、实查结果

### 固定版本SQLite：官方知识发布包

通过release_path定位official/official.sqlite，以mode=ro连接。该发布包共有8,438个clause行，覆盖多个地区；不能将总量当作香港FSIE覆盖量。

香港doc分类包括4份law、22份guidance、1份example、3份page等。对应香港clause行：law 1,700、guidance 466、example 15、page 5；还包括表格、税率、协定等内容。这些是类型/地区统计，尚未逐条验证FSIE相关性或入模权限。

已有结构：doc（jur/type/issued/effective_from/effective_to/lang/sha256/text_status/alias_of等），clause（cite_id/doc_id/kind/label/parent/text），expression（语言、版本、有效期、canonical、alias_of等），clause_meta、clause_time、unit、edge、param及FTS/向量相关表。表存在不代表每个索引都已使用：当前知识API明确使用exact、bm25渠道。

该库由固定发布摘要保护，不能原地补字段或修改条文，否则破坏版本校验。应用层适配、旁路索引或新发布包应分别处理。

### 云端PostgreSQL

public共有16个业务/迁移表。sources有21条：香港14条、内地7条。内地7条均registered，未生成legal_units，只有资料目录基础。

香港已解析13条来源，另1条out_of_scope。资料聚合如下：

| source_type | 已解析来源数 | legal_units行数 |
| --- | ---: | ---: |
| official_advance_ruling | 4 | 28 |
| official_advance_ruling_guidance | 1 | 45 |
| official_examples | 1 | 136 |
| official_faq | 1 | 101 |
| official_guidance | 2 | 349 |
| official_web_page | 1 | 280 |
| ordinance_material | 1 | 62 |
| structured_legislation_xml | 2 | 88 |

legal_units合计1,089条，全部language=en。其中guidance_block有909条、ruling_block有28条、faq_item仅2条。可见很多FAQ/示例内容以通用guidance_block存储，不能仅靠unit_type判断官方内容类别。

sources中4条有effective_from、10条有topic_tags，professional_validation_status='verified'为0条。日期缺失不等于过期，抓取时间也不能当成法律生效时间。

rule_sets、rule_nodes、evaluation_cases均为0条。当前规则分析代码从Git知识包load_rules_payload读取，不能改成只读这些空表。

### 案件数据

现有事实范式表facts/fact_versions与当前网页运行的chat_cases.document是不同路径。ChatStore把facts、fact_history、confirmed_facts、analyses等存在owner/revision保护的document中。新增工具应读现有projected状态，不能误以为网页事实已经全部写进facts表；也不能把整数cases.id与字符串chat_cases.id直接关联。

## 二、先改路由和适配，不先重建数据库

| 工具 | 推荐数据路径 | 约束 |
| --- | --- | --- |
| read_case_facts | 已授权chat_cases.document的当前projected事实 | 不对模型开放任意SQL；保留owner、revision和确认状态 |
| check_fact_gaps | 上述事实+Git规则/访谈要求 | 按当前问题的issue检查，不强制完整分析所有字段 |
| search_law | 固定SQLite法条为主要来源 | 依据doc.type/版本元数据筛选，并保持精确条文定位；其他来源按显式缺口策略使用 |
| search_guidance | 先接入PostgreSQL现有FSIE指引/FAQ/示例，再按明确覆盖策略调用固定库的指引 | 两边来源须区分、合并去重；不能发生法条冒充指引 |
| search_rulings | PostgreSQL的4个官方裁定 | 返回裁定上下文、适用案件和材料限制，不当作普遍法律规则 |
| prepare_analysis | 现有确认事实快照+版本化Git规则+Provider证据 | 云端规则表为空，不切换规则真源；继续人工复核 |

建议把RoutedKnowledgeProvider从law/rulings两个槽位扩成按受控来源类型路由的适配器，支持law/guidance/ruling，并返回真实能力。指引优先使用现有PG路径是阶段性方案，因为其已有FSIE清单约束；固定库并非没有指引，完成主题、有效期、权限适配后也可提供。不能在一个Provider发生技术故障后静默切换并伪装成同一份完整结果。

## 三、让已有字段真正参与检索

1. 先做主题和权限约束：jurisdiction=HK、FSIE来源/条款白名单、已解析可读、允许入模和展示，保留drift/验证状态；跨境案例中派息地为SG不等于要检索新加坡税法。
2. 法条按source_type/doc.type和locator双重识别；指引按源类型识别，不能以“没有statute_locator”作为唯一分类标准。
3. 单独识别FAQ、官方示例、裁定说明页和裁定本身。PG中很多内容同属guidance_block，需要通过sources.source_type区分；必要时后续逐步细化unit_type，但不是第一阶段前提。
4. 日期使用待分析收入的适用期间；月份精度保留为月份/区间，不能补造具体日期或默认用今天。没有effective_from的指引可用于一般解释，但须标注历史适用性未确定，不自动与法条一样认定适用。
5. 显式条号先精确定位；子问题用现有关键词/FTS检索，再取小节与邻近上下文。别先把整页大量文本送给模型，也不必立即重建向量库。
6. 跨库去重采用规范来源映射、版本、locator/父子关系和文本哈希。相同文本不同版本/时期不能直接混为一条；多个显示子片段不能算作多个独立来源。

## 四、补“问题—资料覆盖”映射，先做版本化配置

现有NODE_LOCATORS、规则required_facts/required_evidence及manifest.rule_nodes是起点，尚不足以成为完整覆盖证明。建议添加版本化的issue_evidence_map（首版文件配置）：

issue_id → 对应分析目标 → 所需事实 → 主法条定位 → 解释资料候选 → 可选裁定 → 需要人工判断项。

例如participation_basic使用现有s.15M映射；foreign_tax_switchover使用现有s.15N相关映射。具体指引段落与规则含义须逐条核对后登记，不能让模型凭名称生成映射。

搜索返回应包含：covered_issue_ids、uncovered_issue_ids、来源类型、可引用reference、适用期间状态及覆盖判断原因。区分已定位、已读取、引用校验通过、命题支持待复核、专业已验证。当前professional verified为0，不能因命中足够数量就升级到专业验证通过。

## 五、哪些地方需要改表

### 第一阶段：无需数据库迁移

- 复用sources和legal_units现有字段进行准确分类与筛选；增加Provider能力和返回契约。
- 搜索只返回证据，不推进访谈、不生成最终答复；缺口计算基于现有案件状态。
- issue_evidence_map及canonical source映射先随Git发布，审核明确后再考虑数据库管理。
- 继续使用独立JSONL日志；不把详细执行事件塞回chat_cases.document。

### 第二阶段：根据真实需求逐步新增

- source_versions / legal_unit_versions：PG当前sources.source_id唯一、legal_units按source+unit_ref唯一，不是完整的多版本原文归档。若需要长期回放历史答案，建立不可变版本及快照引用；旧引用指向旧版本，不能更新原文后重新解释旧哈希。固定SQLite仍按发布包版本引用。
- issue_evidence_links：当映射维护量或审核协作需求上来后再入库；至少记录issue、source版本、unit引用、关联类型、映射版本、验证状态、审核者/时间，不能只有issue与自由文本。
- case_transactions：当多个收入事件需要独立事实与分析时再迁移，或先在document内明确transaction_id。当前facts表的income_event_id不能解决唯一约束(case_id,field_name)无法表达多笔同名字段的问题，且它尚非网页事实存储主路径。
- 检索索引：先看EXPLAIN与延迟，再为PG的筛选/全文或trigram增加针对性索引；不能仅因当前使用ILIKE就直接断言必须新建向量索引。

不建议本轮统一搬迁SQLite到PG、填充空规则表并立刻切换运行、或同步维护两套案件事实真源。

## 六、落地顺序和验收

1. 增加只读能力/覆盖盘点，修正source_type语义和guidance路由。验证返回的真实来源类别，而非只验证请求kind。
2. 基于现有规则/条号建立小范围issue映射；改造统一工具结果及最终汇总流程，保留用户确认和引用保护。
3. 对Case1在网页重测：至少能够定位法条并查到与所问问题相关的现有指引，列出关键缺口；如无相关指引，应如实说明，不能硬凑数量。对同一命题的引用去重，英语输入时正文和跟进操作文案语言一致。
4. 补充来源缺失、日期不确定、多笔交易和Provider故障测试；日志区分检索数量、唯一来源数、覆盖项、重复项、事实阻断和技术失败。
5. 通过这些测试后，再决定不可变版本、映射管理和多交易数据模型的迁移范围。

结论：数据库已有相当多可用素材，第一步应让工具准确调用并返回这些素材的结构化覆盖信息。现阶段主要缺口是路由、主题/来源分类、版本适用性和案件状态衔接，不是再建一个资料库。
