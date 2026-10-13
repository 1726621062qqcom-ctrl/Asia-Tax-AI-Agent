import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Case, DomainQuestion } from "../workspace";
import { OutcomeView } from "./DomainResult";
import "./structure-panel.css";

type Props = { current: Case; onUpdate: (next: Case) => void };
const sample = {
  template: "holding", currency: "CNY",
  roles: { OP: { loc: "CN", attrs: {} }, ULT: { loc: "HK", attrs: {} } },
  holds: [{ holder: "ULT", held: "OP", ratio: 100, since: "2020-01-01" }],
  flows: { up1: {} }, present: { HOLD: null, financing: "EQUITY", payment: false },
  event: { dividend: 1000000, on: "2026-10-11", as_at: "2026-10-11" }, members: ["OP", "ULT"],
};
const errors: Record<string, string> = {
  revision_conflict: "案件已被其他操作更新，已重新读取。请核对后重试。",
  question_changed: "这个问题已过期，请使用当前问题。",
  currency_required: "请明确填写币种。", domain_unavailable: "结构分析服务暂不可用，请稍后重试。",
  domain_execution_failed: "引擎未完成计算，案件没有保存半次更新。请查看测试说明。",
  domain_timeout: "本轮计算超时，案件没有部分更新。",
  confirmation_required: "请先确认当前结构事实。", partial_confirmation_required: "仍有缺口；请明确选择生成部分研究稿。",
  domain_result_stale: "结果已过期，请重新运行。", domain_paused: "结构分析已暂停，请先恢复。",
  review_incomplete: "证据或专业缺口尚未满足批准门槛；可退回修改或记录暂不能形成结论。",
  invalid_facts: "案情格式或字段不符合要求，请核对日期、金额、角色与持股关系。",
  invalid_domain_answer: "答案类型不正确，请按问题提示填写。", review_forbidden: "当前账号没有复核权限。",
};
export default function StructurePanel({ current, onUpdate }: Props) {
  const [draft, setDraft] = useState(current.domain_case ? JSON.stringify(current.domain_case, null, 2) : "");
  const [mode, setMode] = useState(current.domain_workflow?.mode || "assess_current");
  const [bindings, setBindings] = useState(current.legacy_bindings || {});
  const [approved, setApproved] = useState(current.data_approved);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [value, setValue] = useState("");
  const [ready, setReady] = useState<boolean | null>(null), [advanced, setAdvanced] = useState(false);
  const [partial, setPartial] = useState(false), [canReview, setCanReview] = useState(false);
  const [reviewNote, setReviewNote] = useState(""), [reviewDecision, setReviewDecision] = useState("unable_to_conclude");
  const [reference, setReference] = useState(""), [professionalValue, setProfessionalValue] = useState("yes");
  useEffect(() => { void api.domainCapabilities().then(x => setReady(x.ready)).catch(() => setReady(false));
    void api.session().then(x => setCanReview(!!x.can_review)).catch(() => {}); }, []);
  const saved = JSON.stringify(current.domain_case);
  useEffect(() => { setDraft(current.domain_case ? JSON.stringify(current.domain_case, null, 2) : "");
    setBindings(current.legacy_bindings || {}); setMode(current.domain_workflow?.mode || "assess_current"); }, [current.id, saved]);
  const outcome = current.domain_outcome;
  const latestReport = current.analyses.filter(a => a.report_kind).at(-1);
  async function run(operation: () => Promise<Case>) {
    setBusy(true); setError("");
    try { onUpdate(await operation()); return true; }
    catch (e) { const code = e instanceof ApiError ? e.code : "service_unavailable"; setError(errors[code] || code);
      if (code === "revision_conflict") onUpdate(await api.get(current.id)); return false;
    } finally { setBusy(false); }
  }
  function loadExample() { setDraft(JSON.stringify(sample, null, 2)); setBindings({}); }
  async function importFacts() {
    try { const result = await api.domainDraft(current);
      if (result.case) { setDraft(JSON.stringify(result.case, null, 2)); setBindings(result.bindings); }
      setError([...result.gaps.map(x => "需补充：" + x), "尚未转换的字段：" + result.unmapped.join("、")].join("；"));
    } catch { setError("无法生成草稿，请检查已收集的案情。"); }
  }
  let parsed: Record<string, any> | null = null;
  try { parsed = draft ? JSON.parse(draft) : null; } catch { /* editable JSON may be temporarily incomplete */ }
  function updateForm(field: string, text: string) {
    const data = parsed || { template: "holding", currency: null,
      roles: { OP: { loc: "", attrs: {} }, ULT: { loc: "HK", attrs: {} } },
      holds: [{ holder: "ULT", held: "OP", ratio: null, since: null }],
      flows: { up1: {} }, present: {}, event: {}, members: ["OP", "ULT"] };
    if (field === "amount") data.event.dividend = text === "" ? null : Number(text);
    if (field === "date") { data.event.on = text; data.event.as_at = text; }
    if (field === "ratio") data.holds[0].ratio = text === "" ? null : Number(text);
    if (field === "since") data.holds[0].since = text || null;
    if (field === "payer") data.roles.OP.loc = text;
    if (field === "currency") data.currency = text;
    setDraft(JSON.stringify(data, null, 2));
  }
  async function save() {
    if (!parsed || Array.isArray(parsed)) { setError("请输入有效的案情 JSON。"); return; }
    await run(() => api.domainSetup(current, parsed!, approved, crypto.randomUUID(), mode, bindings));
  }
  async function answer(q: DomainQuestion, disposition = "answer", answerValue = value) {
    if (disposition === "answer" && !answerValue.trim()) { setError("请填写答案，或选择暂缓。"); return; }
    if (await run(() => api.domainAnswer(current, q.key, q.kind, answerValue.trim(), crypto.randomUUID(), q.id, disposition))) setValue("");
  }
  const question = outcome?.questions.find(q => q.id === current.domain_workflow?.pending_question_id);
  const professional = outcome?.questions.filter(q => ["ruling", "library"].includes(q.kind)) || [];
  return <div className="structure-panel">
    <p>根据本案已确认的交易事实进行结构测算。金额、比例和时间以明确填写的值为准。</p>
    <p className="structure-status">结构分析服务：{ready === null ? "检查中" : ready ? "可用" : "暂不可用"}</p>
    <label>分析目的<select aria-label="分析目的" value={mode} onChange={e => setMode(e.target.value)}>
      <option value="assess_current">只分析现有结构</option><option value="plan_structure">比较新结构方案</option><option value="review_paid">核对已缴税事项（实验入口）</option>
    </select></label>
    <div className="structure-actions"><button onClick={loadExample} disabled={busy}>载入合成示例</button>
      <button onClick={() => void importFacts()} disabled={busy}>从当前聊天事实生成草稿</button>
      <button onClick={() => setAdvanced(!advanced)}>{advanced ? "切换基本表单" : "高级案情编辑"}</button></div>
    {!advanced && (!parsed || parsed.template === "holding") ? <div className="structure-form">
      <label>付款方地区<select aria-label="付款方地区" value={parsed?.roles?.OP?.loc || ""} onChange={e => updateForm("payer", e.target.value)}><option value="">请选择</option><option value="CN">中国内地</option><option value="HK">香港</option><option value="SG">新加坡</option></select></label>
      <p>此表单绑定 OP 为付款公司、ULT 为香港收款公司；请在高级编辑中明确现有直接/间接关系（present），不能依据空字段推断结构。</p>
      <label>金额<input aria-label="结构股息金额" type="number" min="0" value={parsed?.event?.dividend ?? ""} onChange={e => updateForm("amount", e.target.value)} /></label>
      <label>币种<select aria-label="结构币种" value={parsed?.currency || ""} onChange={e => updateForm("currency", e.target.value)}><option value="">请选择</option><option value="CNY">CNY（当前计算支持）</option><option value="HKD">HKD（需补汇率规则）</option><option value="SGD">SGD（需补汇率规则）</option></select></label>
      <label>支付日期<input aria-label="结构支付日期" type="date" value={parsed?.event?.on || ""} onChange={e => updateForm("date", e.target.value)} /></label>
      <label>持股比例（%）<input aria-label="结构持股比例" type="number" min="0" max="100" value={parsed?.holds?.[0]?.ratio ?? ""} onChange={e => updateForm("ratio", e.target.value)} /></label>
      <label>取得日期<input aria-label="结构取得日期" type="date" value={parsed?.holds?.[0]?.since || ""} onChange={e => updateForm("since", e.target.value)} /></label>
    </div> : <><label htmlFor="structure-json">结构案情（JSON）</label><textarea id="structure-json" rows={12} value={draft} onChange={e => setDraft(e.target.value)} /></>}
    {Object.keys(bindings).length > 0 && <details><summary>确认事实归属后，这些字段将在两边同步</summary><ul>{Object.entries(bindings).map(([f, a]) => <li key={f}>{f} → {a}</li>)}</ul></details>}
    <label className="structure-consent"><input type="checkbox" checked={approved} onChange={e => setApproved(e.target.checked)} />本次仅提交合成研究资料，不含真实客户或个人信息。</label>
    <button onClick={() => void save()} disabled={busy || !draft}>保存结构案情</button>
    {current.domain_case && <div className="structure-actions"><button disabled={busy || !ready} onClick={() => void run(() => api.domainPlan(current, crypto.randomUUID()))}>运行结构规划</button>
      <button disabled={busy} onClick={() => void run(() => api.domainControl(current, current.domain_workflow?.status === "paused" ? "resume" : "pause"))}>{current.domain_workflow?.status === "paused" ? "恢复结构分析" : "暂停结构分析"}</button></div>}
    {error && <p role="alert" className="request-error">{error}</p>}
    {outcome && <section aria-label="结构分析结果" className="structure-result">
      {outcome.stale && <p role="status">事实已变化，旧结果与问题已过期；请重新运行。</p>}
      <OutcomeView outcome={outcome} />
      {question && !outcome.stale && current.domain_workflow?.status !== "paused" && <div className="structure-question">
        <strong>{question.prompt}</strong><p>答案类型：{question.answer_schema?.hint || question.answer_schema?.type} · {question.region.join(" / ")}</p>
        {question.source_hint && <p>建议材料：{question.source_hint}</p>}
        {["action", "boolean"].includes(question.answer_schema?.type || "") ? <select aria-label="结构问题答案" value={value} onChange={e => setValue(e.target.value)}><option value="">请选择</option><option value={question.kind === "action" ? "yes" : "true"}>是</option><option value={question.kind === "action" ? "no" : "false"}>否</option></select> :
          <input aria-label="结构问题答案" value={value} onChange={e => setValue(e.target.value)} />}
        <div className="structure-actions"><button disabled={busy} onClick={() => void answer(question)}>提交并重新计算</button>
          <button disabled={busy} onClick={() => void answer(question, "defer", "")}>暂缓此题</button>
          {question.kind !== "action" && <button disabled={busy} onClick={() => void answer(question, "answer", "unknown")}>事实未知</button>}</div>
      </div>}
      <details><summary>全部待补项（{outcome.question_count ?? outcome.questions.length}）</summary><ul>{outcome.questions.map(q => <li key={q.id}>[{q.kind}] {q.key} · {q.prompt}</li>)}</ul></details>
      {professional.length > 0 && <p>另有 {professional.length} 项专业判断或资料维护问题，已保留给有权限的复核者。</p>}
      {canReview && professional.map(q => <details key={q.id}><summary>专业/资料维护：{q.prompt}</summary>
        <label>依据引用对象 JSON<textarea aria-label="专业依据引用" value={reference} onChange={e => setReference(e.target.value)} /></label>
        <label>专业答复（裁量当前只接受有依据的有利判断 yes；日历填写日期数组）<input value={professionalValue} onChange={e => setProfessionalValue(e.target.value)} /></label>
        <button disabled={busy} onClick={() => { try { const ref = JSON.parse(reference); const answer = q.kind === "library" ? JSON.parse(professionalValue) : professionalValue;
          void run(() => api.domainProfessional(current, q.id, answer, ref)); } catch { setError("引用或日历必须是有效 JSON。"); } }}>保存依据并重新计算</button></details>)}
      <button disabled={busy || !!outcome.stale} onClick={() => void run(() => api.domainConfirm(current))}>确认当前结构事实</button>
      <label><input type="checkbox" checked={partial} onChange={e => setPartial(e.target.checked)} />同意按当前信息生成部分研究稿，保留全部缺口。</label>
      <button disabled={busy || !!outcome.stale || !current.domain_confirmation} onClick={() => void run(() => api.domainReport(current, partial))}>生成合并研究稿</button>
      {canReview && latestReport?.report_hash && !latestReport.stale && latestReport.review?.status === "pending_final_review" && <details>
        <summary>最终研究稿复核</summary><label>复核决定<select value={reviewDecision} onChange={e => setReviewDecision(e.target.value)}>
          <option value="unable_to_conclude">暂不能形成结论</option><option value="changes_requested">退回修改</option><option value="approved">批准（需满足证据与完整性门槛）</option></select></label>
        <label>复核说明<textarea value={reviewNote} onChange={e => setReviewNote(e.target.value)} /></label>
        <button disabled={busy || !reviewNote.trim()} onClick={() => void run(() => api.finalReview(current, latestReport.id, latestReport.report_hash!, reviewDecision, reviewNote))}>保存最终复核</button>
      </details>}
    </section>}
  </div>;
}
