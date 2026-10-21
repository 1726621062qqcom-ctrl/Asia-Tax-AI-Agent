import fields from './engine-fields.json' with { type: 'json' };
import glossary from './engine-glossary.json' with { type: 'json' };
import type { Locale } from './locale';

const english: Record<string, string> = {
  ...glossary,
  '当前已验证的计算单位为 CNY；其他币种需要明确汇率来源和税额折算规则，未执行计算。': 'The validated calculation currency is CNY. Other currencies require an exchange-rate source and tax conversion rules. No calculation was performed.',
  '香港': 'Hong Kong', '内地': 'Mainland China', '新加坡': 'Singapore',
  '只分析明确给出的现有结构；未决事实与专业判断保留为条件。': 'Only the stated existing structure is assessed. Missing facts and professional judgments remain conditions.',
  '现有结构与安排不一致：本次固定结构分析不允许新增或迁移公司。': 'The arrangements do not match the existing structure. This analysis cannot add or relocate companies.',
  '现有结构需明确这些安排（不猜默认值）：': 'These arrangements must be specified; no defaults are assumed: ',
  '相互依赖的未决项过多，不能给出精确上下界：': 'Too many interdependent questions remain to calculate precise bounds: ',
  '缺少模板要求的主体：': 'Required entities are missing: ',
  '新设公司（若有）按方案设计视为只有所列各笔流；改为有其他业务时须重新运行。': 'New entities, if any, are assumed to have only the listed flows. Rerun the analysis if they have other business.',
  '没有候选结构能保留已缴税的那几笔流。': 'No candidate structure preserves the flows on which tax has already been paid.',
  '无法给出方案：': 'No viable plan: ',
  '集团外（由方案选定所在地）': 'Outside the group (location selected by the plan)',
  '集团外': 'Outside the group', '转出所持股权后清算注销': 'Liquidated after transferring its shares',
  '该年假期表官方尚未公布，按名义日期；公布后可能顺延': 'Official holidays for this year are not yet published. The nominal deadline may be extended once published.',
  '该年假期表缺失（已向人索取）': 'The holiday calendar is missing and has been requested.',
  '已确认': 'Confirmed', '待确认': 'Awaiting confirmation', '设计': 'Planned',
  '方案设计（全资新设）': 'Designed arrangement (new wholly owned entity)',
  '迁移或重新安排': 'Relocated or rearranged', '承接原持股': 'Existing ownership carried over',
  '案例陈述': 'As stated in the case', '现有': 'Existing', '新设': 'Newly established',
  '是否已取得税务机关对以下事项的书面裁定或确认：': 'Has the tax authority provided a written ruling or confirmation on the following? ',
  '能否做到：': 'Can this requirement be met? ', '请提供：': 'Please confirm: ',
  '——须与': ' — This must hold together with ', '同时成立才有影响': ' to affect the result',
  '是/否': 'Yes / No', '税务机关认定': 'Tax authority determination', '金额': 'Amount',
  '日期': 'Date', '年度': 'Year', '月数': 'Months', '天数': 'Days', '枚举': 'Choice',
  '数值': 'Number', '法域': 'Jurisdiction', '比值': 'Ratio', '比率': 'Ratio',
};
const entries = Object.entries(english).sort(([a], [b]) => b.length - a.length);
const terms: Record<string, [string, string]> = {
  CN: ['中国内地', 'Mainland China'], HK: ['香港', 'Hong Kong'], SG: ['新加坡', 'Singapore'],
  OP: ['经营公司', 'Operating company'], ULT: ['最终持股公司', 'Ultimate holding company'], HOLD: ['中间控股公司', 'Intermediate holding company'],
  DIVIDEND: ['股息', 'Dividend'], INTEREST: ['利息', 'Interest'], ROYALTY: ['特许权使用费', 'Royalty'],
  SERVICE: ['服务费', 'Service fee'], EQUITY: ['股本', 'Equity'], DEBT: ['债务', 'Debt'],
  group: ['集团', 'Group'], blocking: ['必需事实', 'Required fact'], income: ['所得税', 'Income tax'],
  boolean: ['是 / 否', 'Yes / No'], action: ['行动确认', 'Action confirmation'],
  data: ['事实信息', 'Fact'], ruling: ['专业裁定', 'Professional ruling'], library: ['资料维护', 'Source maintenance'],
  WHT: ['预提所得税', 'Withholding tax'], CIT: ['企业所得税', 'Corporate income tax'], VAT: ['增值税', 'VAT'],
  STAMP: ['印花税', 'Stamp duty'], GST: ['消费税', 'GST'],
  number: ['数值', 'Number'], date: ['日期', 'Date'], text: ['文字', 'Text'], string: ['文字', 'Text'],
  pending_final_review: ['待最终复核', 'Pending final review'], approved: ['已批准', 'Approved'],
  changes_requested: ['需修改', 'Changes requested'], unable_to_conclude: ['暂不能形成结论', 'Unable to conclude'],
};
export function engineText(value: unknown, locale: Locale): string {
  if (value == null) return '';
  if (Array.isArray(value)) return value.map(x => engineText(x, locale)).join(' · ');
  if (typeof value === 'object') return Object.entries(value).map(([k,v]) => `${engineText(k, locale)}: ${engineText(v, locale)}`).join('; ');
  let text = String(value);
  if (terms[text]) return terms[text][locale === 'en' ? 1 : 0];
  text = text.replace(/(?:flow:|hold:)?[A-Za-z0-9_]+\.([a-z][a-z0-9_]+)/g, (address, field: string) => {
    const name = (fields as Record<string, string>)[field] || (fields as Record<string, string>)[field.replace(/_(cn|hk|sg)$/, '')];
    if (!name) return address;
    const scope = address.slice(0, address.lastIndexOf('.'));
    const target = scope.startsWith('flow:') ? `${locale === 'en' ? 'Cash flow' : '资金流'} ${scope.match(/\d+$/)?.[0] || ''}` : engineText(scope.replace(/^hold:/, ''), locale);
    const region = /_(cn|hk|sg)$/.exec(field)?.[1].toUpperCase();
    return `${target}${region ? ` (${engineText(region, locale)})` : ''}: ${name}`;
  });
  if (locale === 'en') for (const [source, target] of entries) text = text.split(source).join(target);
  return text.replace(/\b[A-Z][A-Z_]+\b/g, token => terms[token]?.[locale === 'en' ? 1 : 0] ?? token);
}
export function questionText(question: { prompt: string; key: string; prompt_en?: string }, locale: Locale) {
  if (locale === 'en' && question.prompt_en) return question.prompt_en;
  // Internal addresses belong to the API, not the question shown to the user.
  const escaped = question.key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return engineText(question.prompt.replace(new RegExp(`[（(]${escaped}[）)]`, 'g'), ''), locale);
}
