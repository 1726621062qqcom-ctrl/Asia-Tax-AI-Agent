import type { DomainOutcome, Analysis } from '../workspace';
import { engineText, questionText } from '../engine-language';
import Passages from './Passages';
import { useLocale } from '../locale';

export function OutcomeView({ outcome: o }: { outcome: DomainOutcome }) {
  const { locale } = useLocale();
  const label = (value: unknown) => engineText(value, locale);
  const say = (zh: string, en: string) => locale === 'en' ? en : zh;
  const amount = (bound?: { value: number | null; status: string }) => bound?.status === 'finite' ? bound.value?.toLocaleString() : say('未界定', 'Not defined');
  return <>
    <p>{say('模式：', 'Mode: ')}{o.mode === 'assess_current' ? say('现有结构分析', 'Current structure') : o.mode === 'review_paid' ? say('已缴事项核对', 'Paid-tax review') : say('结构方案比较', 'Structure comparison')} · {say('币种 ', 'Currency ')}{o.currency}</p>
    <p>{say('状态：', 'Status: ')}{o.status === 'ready' ? say('已有计算结果', 'Calculated') : o.status === 'needs_input' ? say('需要补充信息', 'Needs input') : o.status === 'unsupported' ? say('当前不支持计算', 'Unsupported') : say('无法形成方案', 'No viable plan')}; {say('候选结构 ', 'Candidate structures ')}{o.candidate_count}; {say('分析日期 ', 'Analysis date ')}{o.today}</p>
    {o.note && <p>{label(o.note)}</p>}
    {o.upper && <p>{say('本模型范围内税额下界：', 'Tax lower bound within this model: ')}{amount(o.lower)}; {say('上界：', 'upper bound: ')}{amount(o.upper)}.</p>}
    {o.structure && <>
      <h3>{say('结构与资金流', 'Structure and cash flows')}</h3>
      <ul>{o.structure.entities.map(e => <li key={e[0]}>{label(e[0])} · {label(e[1])} · {label(e[2])}</li>)}</ul>
      <ul>{o.structure.holds.map((h, i) => <li key={i}>{label(h[0])} → {label(h[1])}：{h[2]}%（{label(h[3])}）</li>)}</ul>
      <ul>{o.structure.flows.map((f, i) => <li key={i}>{label(f[2])} → {label(f[3])} · {label(f[1])} · {f[4].toLocaleString()} · {f[5]}</li>)}</ul>
    </>}
    {o.regions?.map((r, i) => <details key={i}>
      <summary>{r.jurisdictions.map(label).join(' / ')} {say('的税额、行动和条件', 'tax, actions and conditions')}</summary>
      <ul>{r.guaranteed.map((t, j) => <li key={j}>{label(t[0])} · {label(t[2])} · {label(t[3])} {say('承担', 'bears')} {t[4].toLocaleString()} {o.currency}; {say('依据', 'sources')} {t[5].join(', ')}{t[6] ? '' : say('（集团外，不计入合计）', ' (outside the group, excluded from total)')}</li>)}</ul>
      {[[say('行动', 'Actions'), r.actions], [say('未决条件', 'Open conditions'), r.conditions], [say('期限', 'Deadlines'), r.deadlines]].map(([title, items]) =>
        <ul key={String(title)}>{(items as unknown[]).map((x, j) => <li key={j}>{String(title)}：{label(x)}</li>)}</ul>)}
    </details>)}
    {o.unmodelled?.length ? <details open><summary>{say('未建模事项', 'Unmodelled items')}</summary><ul>{o.unmodelled.map((x, i) => <li key={i}>{label(x)}</li>)}</ul></details> : null}
    {o.notes?.map((n, i) => <p key={i}>{label(n)}</p>)}
  </>;
}

export default function DomainResult({ result }: { result: Analysis }) {
  const { locale } = useLocale();
  const label = (value: unknown) => engineText(value, locale);
  const say = (zh: string, en: string) => locale === 'en' ? en : zh;
  if (!result.outcome) return null;
  return <article className={`analysis-result ${result.stale ? 'is-stale' : ''}`}>
    <strong>{result.stale ? say('研究稿已过期', 'Research draft is out of date') : `${say('合并编排研究稿', 'Combined research draft')} · ${label(result.review?.status) || say('待专业复核', 'Pending professional review')}`}</strong>
    <OutcomeView outcome={result.outcome} />
    {result.fsie_assessment && <details open><summary>{say('香港 FSIE 规则核对（同一案情）', 'Hong Kong FSIE rule check (same case)')}</summary>
      <ul>{result.fsie_assessment.nodes.map(n => <li key={n.node}>{n.node}：{n.output}</li>)}</ul></details>}
    <details open><summary>{say('待补问题', 'Open questions')}</summary><ul>{result.outcome.questions.map(q => <li key={q.id}>[{label(q.kind)}] {questionText(q, locale)}</li>)}</ul></details>
    <details><summary>{say('本次依据原文', 'Source excerpts')}</summary><Passages passages={result.passages} /></details>
    <p>{say('引擎版本 ', 'Engine version ')}{result.rule_version.slice(0, 8)}; {say('事实版本 ', 'Facts revision ')}{result.confirmed_revision}; {say('专业核验待完成。', 'professional verification pending.')}</p>
    <button type="button" onClick={() => {
      const url = URL.createObjectURL(new Blob([result.markdown || ''], { type: 'text/markdown;charset=utf-8' }));
      const a = document.createElement('a'); a.href = url; a.download = `research-${result.id}.md`; a.click(); URL.revokeObjectURL(url);
    }}>{say('下载研究稿', 'Download research draft')}</button>
  </article>;
}
