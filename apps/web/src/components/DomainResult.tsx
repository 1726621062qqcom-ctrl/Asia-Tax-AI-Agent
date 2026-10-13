import type { DomainOutcome, Analysis } from '../workspace';
import Passages from './Passages';

export function OutcomeView({ outcome: o }: { outcome: DomainOutcome }) {
  const amount = (bound?: { value: number | null; status: string }) => bound?.status === 'finite' ? bound.value?.toLocaleString() : '未界定';
  return <>
    <p>模式：{o.mode === 'assess_current' ? '现有结构分析' : o.mode === 'review_paid' ? '已缴事项核对' : '结构方案比较'} · 币种 {o.currency}</p>
    <p>状态：{o.status === 'ready' ? '已有计算结果' : o.status === 'needs_input' ? '需要补充信息' : o.status === 'unsupported' ? '当前不支持计算' : '无法形成方案'}；候选结构 {o.candidate_count} 个；分析日期 {o.today}</p>
    {o.note && <p>{o.note}</p>}
    {o.upper && <p>本模型范围内税额下界：{amount(o.lower)}；上界：{amount(o.upper)}。</p>}
    {o.structure && <>
      <h3>结构与资金流</h3>
      <ul>{o.structure.entities.map(e => <li key={e[0]}>{e[0]} · {e[1]} · {e[2]}</li>)}</ul>
      <ul>{o.structure.holds.map((h, i) => <li key={i}>{h[0]} → {h[1]}：{h[2]}%（{h[3]}）</li>)}</ul>
      <ul>{o.structure.flows.map((f, i) => <li key={i}>{f[0]}：{f[2]} → {f[3]} · {f[1]} · {f[4].toLocaleString()} · {f[5]}</li>)}</ul>
    </>}
    {o.regions?.map((r, i) => <details key={i}>
      <summary>{r.jurisdictions.join(' / ')} 的税额、行动和条件</summary>
      <ul>{r.guaranteed.map((t, j) => <li key={j}>{t[0]} · {t[2]} · {t[3]} 承担 {t[4].toLocaleString()} {o.currency}；依据 {t[5].join(', ')}{t[6] ? '' : '（集团外，不计入合计）'}</li>)}</ul>
      {[['行动', r.actions], ['未决条件', r.conditions], ['期限', r.deadlines]].map(([title, items]) =>
        <ul key={String(title)}>{(items as unknown[]).map((x, j) => <li key={j}>{String(title)}：{Array.isArray(x) ? x.map(String).join(' · ') : String(x)}</li>)}</ul>)}
    </details>)}
    {o.unmodelled?.length ? <details open><summary>未建模事项</summary><ul>{o.unmodelled.map((x, i) => <li key={i}>{JSON.stringify(x)}</li>)}</ul></details> : null}
    {o.notes?.map((n, i) => <p key={i}>{n}</p>)}
  </>;
}

export default function DomainResult({ result }: { result: Analysis }) {
  if (!result.outcome) return null;
  return <article className={`analysis-result ${result.stale ? 'is-stale' : ''}`}>
    <strong>{result.stale ? '研究稿已过期' : `合并编排研究稿 · ${result.review?.status || '待专业复核'}`}</strong>
    <OutcomeView outcome={result.outcome} />
    {result.fsie_assessment && <details open><summary>香港 FSIE 规则核对（同一案情）</summary>
      <ul>{result.fsie_assessment.nodes.map(n => <li key={n.node}>{n.node}：{n.output}</li>)}</ul></details>}
    <details open><summary>待补问题</summary><ul>{result.outcome.questions.map(q => <li key={q.id}>[{q.kind}] {q.prompt}</li>)}</ul></details>
    <details><summary>本次依据原文</summary><Passages passages={result.passages} /></details>
    <p>引擎版本 {result.rule_version.slice(0, 8)}；事实版本 {result.confirmed_revision}；专业核验待完成。</p>
    <button type="button" onClick={() => {
      const url = URL.createObjectURL(new Blob([result.markdown || ''], { type: 'text/markdown;charset=utf-8' }));
      const a = document.createElement('a'); a.href = url; a.download = `research-${result.id}.md`; a.click(); URL.revokeObjectURL(url);
    }}>下载研究稿</button>
  </article>;
}
