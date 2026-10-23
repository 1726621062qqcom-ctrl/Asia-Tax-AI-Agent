"""User-facing explanations of engine output, without new tax assumptions."""
import math
import re

from packages.domain_bridge.question_order import CATALOG, parts


def summary(result, english=False, doc=None):
    def say(zh, en):
        return en if english else zh
    currency = result.get('currency', 'CNY')
    def finite(value):
        return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)
    def amount(value):
        return f'{value:,.2f} {currency}'
    def bound(key):
        value = result.get(key) or {}
        return amount(value['value']) if value.get('status') == 'finite' and finite(value.get('value')) else say('尚不能确定', 'not determined')
    if result['status'] == 'unsupported':
        return say('当前计算引擎只支持人民币（CNY）。本次没有换汇，也没有计算税额。', 'This engine currently calculates in CNY only. No currency conversion or tax calculation was performed.')
    if result['status'] == 'blocked':
        return say('本次结构暂时无法计算。', 'The engine could not calculate this structure. ') + result.get('note', '')
    regions = {'CN': say('中国内地', 'Mainland China'), 'HK': say('香港', 'Hong Kong'), 'SG': say('新加坡', 'Singapore')}
    levies = {'income': say('所得税', 'income tax'), 'WHT': say('预提税', 'withholding tax'),
              'VAT': say('增值税', 'VAT'), 'GST': say('消费税', 'GST'), 'STAMP': say('印花税', 'stamp duty')}
    lines = [say('### 1. 税额试算结果', '### 1. Tax estimate'),
             say(f"当前模型试算区间：**{bound('lower')}–{bound('upper')}**。", f"Estimated range within this model: **{bound('lower')}–{bound('upper')}**."),
             say('这是已保存结构在未决条件下的区间，不是已确定的应缴税额，也不是概率预测。',
                 'This is a conditional range for the saved structure, not a final payable amount or a probability forecast.'),
             say('### 2. 区间由哪些金额组成', '### 2. What makes up the range')]
    # Only explain a total when the returned in-group components reconcile with
    # that exact bound. Never guess missing credits or add regional minima.
    explained = False
    if result.get('mode') in ('assess_current', 'review_paid'):
        for key, side, zh, en in [('lower', 'best', '下限', 'Lower bound'), ('upper', 'guaranteed', '上限', 'Upper bound')]:
            total = result.get(key) or {}
            rows = [row for region in result.get('regions', []) for row in region.get(side, [])]
            valid = rows and all(len(row) >= 7 and finite(row[4]) for row in rows)
            included = [row for row in rows if row[6] is True] if valid else []
            if total.get('status') != 'finite' or not finite(total.get('value')) or not included or abs(sum(row[4] for row in included) - total['value']) > .01:
                continue
            explained = True
            components = ' + '.join(f"{regions.get(row[1], row[1])}{' ' if english else ''}{levies.get(row[2], row[2])} {amount(row[4])}" for row in included)
            lines.append(f"- **{say(zh, en)}**：{components} = **{amount(total['value'])}**")
    lines.append(say('以上组成直接来自引擎的对应情景。优惠、豁免及已缴税款的处理仍取决于资料；不能据此认定已获优惠，也不要在该结果上自行重复减去境外税款。',
                     'These components come directly from the engine scenarios. Relief, exemptions and treatment of taxes paid remain conditional; this does not establish eligibility or justify deducting foreign tax again.') if explained else
                 say('引擎目前没有返回可与总额完整核对的分项明细，因此本次不推测上下限的具体组成。', 'The returned components do not fully reconcile with the totals. No breakdown has been inferred.'))
    lines.append(say('### 3. 本次采用的案例信息', '### 3. Case information used'))
    structure = result.get('structure') or {}
    locations = {e[0]: e[1] for e in structure.get('entities', [])}
    def company(key):
        return regions.get(locations.get(key), key) + say('公司', ' company')
    for flow in structure.get('flows', []):
        income = say('股息', 'dividend') if flow[1] == 'DIVIDEND' else flow[1]
        lines.append(f"- {company(flow[2])} → {company(flow[3])}：{income} {amount(flow[4])}；{flow[5]}")
    for hold in structure.get('holds', []):
        lines.append(say(f'- {company(hold[0])}直接持有{company(hold[1])} {hold[2]:g}% 股份。',
                         f'- {company(hold[0])} directly holds {hold[2]:g}% of {company(hold[1])}.'))
    records = (doc or {}).get('canonical_fact_records', {})
    for key, record in records.items():
        if record.get('status') in ('unknown', 'conflict', 'deferred'):
            continue
        if key.startswith('hold:') and key.endswith('.since') and record.get('value'):
            holder, held = key[5:-6].split('>', 1)
            lines.append(say(f"- {company(holder)}取得{company(held)}股份日期：{record['value']}。", f"- Acquisition date ({company(holder)} → {company(held)}): {record['value']}."))
        if key.endswith('.reinvested_in_cn') and record.get('value') is False:
            flow_id = key.partition(':')[2].partition('.')[0]
            flow = next((f for f in structure.get('flows', []) if f[0] == flow_id), None)
            if flow:
                lines.append(say(f'- 已记录：{company(flow[2])} → {company(flow[3])}的这笔收入不在内地再投资；跳过再投资细节。',
                                 f'- Recorded: this income from {company(flow[2])} to {company(flow[3])} is not reinvested in Mainland China; reinvestment details are skipped.'))
    lines.append(say('上述为已记录资料，不代表已完成证据核验。', 'These are recorded facts, not a statement that supporting evidence has been verified.'))
    lines.append(say('### 4. 哪些事项仍需复核', '### 4. Matters still requiring review'))
    professional = [q for q in result.get('questions', []) if q['kind'] in ('ruling', 'library') and q.get('interview_status') != 'not_applicable']
    for index, q in enumerate(professional, 1):
        meta = CATALOG.get(parts(q['key'])[2], {})
        label = meta.get('en' if english else 'zh') or q.get('prompt_en' if english else 'prompt') or say('待核对事项', 'Review item')
        label = re.sub(r'[（(]' + re.escape(q['key']) + r'[）)]', '', label)
        source = meta.get('source_en' if english else 'source_zh') or q.get('source_hint_en' if english else 'source_hint')
        region = ' / '.join(regions.get(r, r) for r in q.get('region', []))
        lines.append(f"{index}. **{label}**" + (f"（{region}）" if region else '') + (say(f'；需核对：{source}。', f'; supporting material: {source}.') if source else ''))
    if professional:
        lines.append(say('这些是引擎保留的待复核条件，不是已经认定存在的问题；当前输出没有量化每项对税额的单独影响。',
                         'These are unresolved engine conditions, not adverse findings. The output does not quantify the separate tax effect of each item.'))
    else:
        lines.append(say('当前输出未列出专业复核项；这不等于所有缺失事实都已补齐。', 'No professional review items are listed in this output; missing facts may still remain.'))
    if result.get('unmodelled'):
        lines.append(say('另有引擎尚未覆盖的事项，需要单独复核。', 'Some matters are outside the model and require separate review.'))
    return '\n\n'.join(lines)
