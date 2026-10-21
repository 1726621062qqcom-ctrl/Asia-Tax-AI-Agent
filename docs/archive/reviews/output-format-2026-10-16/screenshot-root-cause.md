# 截图回复的代码根因

日期：2026-10-16。此次为诊断，未修改业务代码。

## 已验证结论

截图文本可以由现有检索、过滤和模板代码复现，不依赖模型生成。

使用固定 tax engine 发布副本 `Asia-Tax-AI-Agent-tax-engine-source-771e452` 的真实资料库，只读执行实际 exact/BM25 检索，再执行从当前主线 AST 提取的导航、适用性过滤及格式函数。得到与此前线上 P01 记录相同的七个 evidence_id；空白字符标准化后，重建答案与线上正文完全匹配。

这验证了截图的触发链路，不等同于本轮重跑完整 HTTP / 模型 / 部署端到端测试。复现记录见 `screenshot-root-cause-reproduction.json`，此前线上记录见 `live-observations.json` 的 P01。

## 触发链路

1. `packages/agent/hybrid.py:28` 将预设问题改写为固定检索词 `香港境外股息FSIE分析所需事实与官方资料`。
2. `packages/chat/knowledge.py:31-46` 的条款导航没有为该一般准备问题提供定位；实际 `topic_locators(query)` 返回空数组。
3. `apps/knowledge_api/main.py:151-169` 没有取得直接定位结果，采用原生关键词检索的前七条。实际召回 s50A、s15、s15F、s2、sch63、sch16D、s20ACA 的中文片段，未定位到本问题所需的 FSIE 核心条款。
4. `packages/agent/hybrid.py:286` 要求 `jurisdiction=HK, topic=dividend`。资料的实际元数据为 `jurisdiction=HK, topic=None`，请求没有适用日期。
5. `packages/agent/knowledge.py:12-20` 严格检查主题。七条全部因主题不匹配被拒绝；当前案例不能笼统归因为法域错误或适用日期错误。
6. `packages/agent/knowledge.py:50` 每拒绝一条，就将相同诊断文字与 evidence_id 写入 `gaps`。
7. `packages/agent/knowledge.py:137,152,179-183` 将这些内部诊断复制为用户可见的 limitations，用分号拼接到“缺口”之后。摘要和“适用条件”同样是固定模板。
8. `packages/agent/hybrid.py:298-300` 将模板保存为回复；`Conversation.tsx:237` 直接渲染 `message.text`。

## 另一项确定的映射缺陷

`apps/knowledge_api/main.py:198-205` 只将 `hk.cap112.en` 映射为标准 source_id，并基于该 source_id 标注 FSIE 主题。即使检索召回相关的 `hk.cap112.zh#s15K`，中文版本也不会被这段代码标为 `dividend`。

这是双语映射缺陷，但不是说截图中的七条都应被放行。它们本身没有命中所需 FSIE 条款。单独放宽主题校验或把所有 Cap.112 资料标成 dividend，会把不相关证据混入答案。

## 修复应覆盖的三层

1. **任务与检索**：为一般 FSIE 准备/事实清单任务建立明确的依据导航，保留适用范围；检测全部结果被拒绝时的零有效证据状态。检索改写/回退仍需遵守现有次数和时限，不能拿任意法规充数。
2. **证据映射**：按明确的中英文条款身份规范化 source_id 与主题，保留语言、版本、哈希和既有 model/display 权限，不能通过取消过滤解决问题。
3. **用户输出**：内部诊断与用户待补事实分开保存。原始 evidence_id 留在诊断详情。无有效来源时用一句普通语言说明未取得依据，并提供合理下一步；有有效来源时保留正文与末尾引用。不声称用户案情缺失导致了本次检索失败。

## 回归重点

- 三个预设原始问题及实际固定检索词都要覆盖；只测试“经济实质”等已命中导航的查询不能覆盖此次问题。
- 相关中文、英文条款映射一致，非 FSIE 条款仍被拒绝。
- 无日期的 HK 请求下，主题失败可被准确诊断，避免混称日期失败。
- 七条失败只产生一条可理解的用户说明，完整的七条诊断仍可审计。
- 回复正文不出现 `law|...` 等内部 ID；有效引用保留精确来源、原文和版本。
