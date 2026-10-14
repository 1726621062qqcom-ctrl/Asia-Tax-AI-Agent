import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import type { Case, DomainQuestion } from "../workspace";
import { OutcomeView } from "./DomainResult";
import { useLocale } from "../locale";
import "./structure-panel.css";

type Props = { current: Case; onUpdate: (next: Case) => void };
const sample = {
  template: "holding", currency: "CNY",
  roles: { OP: { loc: "CN", attrs: {} }, ULT: { loc: "HK", attrs: {} } },
  holds: [{ holder: "ULT", held: "OP", ratio: 100, since: "2020-01-01" }],
  flows: { up1: {} }, present: { HOLD: null, financing: "EQUITY", payment: false },
  event: { dividend: 1000000, on: "2026-10-11", as_at: "2026-10-11" }, members: ["OP", "ULT"],
};
function validCalendarDate(year: number, month: number, day: number) {
  if (year < 1 || year > 9999 || month < 1 || month > 12 || day < 1) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day <= days[month - 1];
}
function toIsoDate(value: string): string | null {
  if (!value.trim()) return "";
  const entered = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value.trim());
  const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!entered && !iso) return null;
  const year = Number(entered?.[3] || iso?.[1]);
  const month = Number(entered?.[2] || iso?.[2]);
  const day = Number(entered?.[1] || iso?.[3]);
  if (!validCalendarDate(year, month, day)) return null;
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
function displayDate(value: unknown) {
  if (typeof value !== "string") return "";
  const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  return iso ? `${iso[3]}/${iso[2]}/${iso[1]}` : value;
}
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
const englishErrors: Record<string, string> = {
  revision_conflict: "This case changed elsewhere. Review the latest version and retry.",
  question_changed: "This question is out of date. Use the current question.",
  currency_required: "Enter the currency.", domain_unavailable: "Structure analysis is unavailable. Try again later.",
  domain_execution_failed: "The calculation failed. No partial case update was saved.",
  domain_timeout: "The calculation timed out. No partial update was saved.",
  confirmation_required: "Confirm the current structure facts first.",
  partial_confirmation_required: "Information is missing. Explicitly request a partial draft.",
  domain_result_stale: "The result is out of date. Run the analysis again.", domain_paused: "Resume structure analysis first.",
  review_incomplete: "Evidence or professional gaps do not meet the approval threshold.",
  invalid_facts: "Check the dates, amounts, roles and ownership relationships.",
  invalid_domain_answer: "Use the answer type requested by the question.",
  review_forbidden: "This account cannot perform the final review.",
};
export default function StructurePanel({ current, onUpdate }: Props) {
  const { locale } = useLocale();
  const say = (zh: string, en: string) => locale === "en" ? en : zh;
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
    catch (e) { const code = e instanceof ApiError ? e.code : "service_unavailable"; setError(say(errors[code] || code, englishErrors[code] || code));
      if (code === "revision_conflict") onUpdate(await api.get(current.id)); return false;
    } finally { setBusy(false); }
  }
  function loadExample() { setDraft(JSON.stringify(sample, null, 2)); setBindings({}); }
  async function importFacts() {
    try { const result = await api.domainDraft(current);
      if (result.case) { setDraft(JSON.stringify(result.case, null, 2)); setBindings(result.bindings); }
      setError([...result.gaps.map(x => say("需补充：", "Missing: ") + x), say("尚未转换的字段：", "Unmapped fields: ") + result.unmapped.join(", ")].join("; "));
    } catch { setError(say("无法生成草稿，请检查已收集的案情。", "Could not create a draft. Check the collected case facts.")); }
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
    if (!parsed || Array.isArray(parsed)) { setError(say("请输入有效的案情 JSON。", "Enter valid case facts in JSON format.")); return; }
    const normalized = structuredClone(parsed);
    if (normalized.template === "holding") {
      const paymentDate = toIsoDate(String(normalized.event?.on || ""));
      const asAtDate = toIsoDate(String(normalized.event?.as_at || ""));
      const acquisitionDate = toIsoDate(String(normalized.holds?.[0]?.since || ""));
      if (paymentDate === null || asAtDate === null || acquisitionDate === null) {
        setError(say("请用 dd/mm/yyyy 填写有效日期，例如 13/10/2026。", "Enter a valid date in dd/mm/yyyy format, for example 13/10/2026."));
        return;
      }
      if (normalized.event) {
        normalized.event.on = paymentDate;
        normalized.event.as_at = asAtDate;
      }
      if (normalized.holds?.[0]) normalized.holds[0].since = acquisitionDate || null;
    }
    await run(() => api.domainSetup(current, normalized, approved, crypto.randomUUID(), mode, bindings));
  }
  async function answer(q: DomainQuestion, disposition = "answer", answerValue = value) {
    if (disposition === "answer" && !answerValue.trim()) { setError(say("请填写答案，或选择暂缓。", "Enter an answer or defer this question.")); return; }
    if (await run(() => api.domainAnswer(current, q.key, q.kind, answerValue.trim(), crypto.randomUUID(), q.id, disposition))) setValue("");
  }
  const question = outcome?.questions.find(q => q.id === current.domain_workflow?.pending_question_id);
  const professional = outcome?.questions.filter(q => ["ruling", "library"].includes(q.kind)) || [];
  const modeHelp = mode === "plan_structure"
    ? say("适合尚未付款、希望比较可行安排的情况。先填写现有公司和交易事实，再在高级编辑中说明可调整的关系；结果只比较已建模的候选方案。", "For a payment that has not happened yet, compare possible arrangements. Enter the current companies and transaction facts first, then describe adjustable relationships in the advanced editor. Results cover modeled options only.")
    : mode === "review_paid"
      ? say("适合已经付款并缴税、需要回看当时处理的情况。请核对实际付款日期、已缴税额和凭证；这是实验入口，结果仍需人工复核。", "For a payment and tax already made, review what happened. Check the actual payment date, tax paid and supporting records. This mode is experimental and requires human review.")
      : say("适合想核对现有付款及持股安排的情况。填写实际金额、日期和持股关系；分析不会替你新增公司或改动现有结构。", "For checking an existing payment and ownership arrangement. Enter the actual amount, dates and ownership relationship; the analysis will not add companies or change the current structure.");
  return <div className="structure-panel">
    <p>{say("根据本案已确认的交易事实进行结构测算。金额、比例和时间以明确填写的值为准。", "Assess the structure using confirmed transaction facts. Amounts, percentages and dates must be entered explicitly.")}</p>
    <p className="structure-status">{say("结构分析服务：", "Structure analysis: ")}{ready === null ? say("检查中", "Checking") : ready ? say("可用", "Available") : say("暂不可用", "Unavailable")}</p>
    <label>{say("分析目的", "Analysis goal")}<select aria-label={say("分析目的", "Analysis goal")} value={mode} onChange={e => setMode(e.target.value)}>
      <option value="assess_current">{say("只分析现有结构", "Assess current structure")}</option><option value="plan_structure">{say("比较新结构方案", "Compare structure options")}</option><option value="review_paid">{say("核对已缴税事项（实验入口）", "Review tax already paid (experimental)")}</option>
    </select></label>
    <p className="structure-mode-help" role="status">{modeHelp}</p>
    <details className="structure-guide"><summary>{say("如何使用结构分析", "How to use structure analysis")}</summary>
      <ol>
        <li>{say("选择分析目的，并确认它符合交易所处阶段。", "Choose the goal that matches the stage of your transaction.")}</li>
        <li>{say("填写已知事实；如果持股或付款关系较复杂，请在高级案情编辑中补全，不能让系统猜测。", "Enter known facts. Use the advanced editor for complex ownership or payment relationships; the system cannot infer missing facts.")}</li>
        <li>{say("保存后运行分析。按提示补充缺失信息，核对依据与结果，再决定是否生成研究稿。", "Save and run the analysis. Answer follow-up questions, check sources and results, then decide whether to create a research draft.")}</li>
      </ol>
    </details>
    <div className="structure-actions"><button onClick={loadExample} disabled={busy}>{say("载入合成示例", "Load synthetic example")}</button>
      <button onClick={() => void importFacts()} disabled={busy}>{say("从当前聊天事实生成草稿", "Draft from chat facts")}</button>
      <button onClick={() => setAdvanced(!advanced)}>{advanced ? say("切换基本表单", "Basic form") : say("高级案情编辑", "Advanced case editor")}</button></div>
    {!advanced && (!parsed || parsed.template === "holding") ? <div className="structure-form">
      <label>{say("付款方地区", "Payer jurisdiction")}<select aria-label={say("付款方地区", "Payer jurisdiction")} value={parsed?.roles?.OP?.loc || ""} onChange={e => updateForm("payer", e.target.value)}><option value="">{say("请选择", "Select")}</option><option value="CN">{say("中国内地", "Mainland China")}</option><option value="HK">{say("香港", "Hong Kong")}</option><option value="SG">{say("新加坡", "Singapore")}</option></select></label>
      <details className="structure-guide structure-relationship-help"><summary>{say("付款公司与收款公司如何填写？", "How do I enter the payer and recipient?")}</summary>
        <p>{say("基本表单将付款公司记为 OP、香港收款公司记为 ULT。若两者有直接或间接持股关系，请在高级案情编辑中写明现有关系；留空不会被视为已确认。", "The basic form calls the payer OP and the Hong Kong recipient ULT. If they have a direct or indirect ownership relationship, record the current relationship in the advanced editor. An empty field is not treated as confirmed.")}</p>
      </details>
      <div className="structure-money-row">
        <label>{say("金额", "Amount")}<input aria-label={say("结构股息金额", "Structure dividend amount")} type="number" min="0" value={parsed?.event?.dividend ?? ""} onChange={e => updateForm("amount", e.target.value)} /></label>
        <label>{say("币种", "Currency")}<select aria-label={say("结构币种", "Structure currency")} value={parsed?.currency || ""} onChange={e => updateForm("currency", e.target.value)}><option value="">{say("请选择", "Select")}</option><option value="CNY">CNY</option><option value="HKD">HKD</option><option value="SGD">SGD</option></select></label>
      </div>
      <p className="structure-field-note">{say("目前仅支持 CNY 计算；HKD、SGD 仍需汇率规则。", "Calculations currently support CNY only; HKD and SGD still need exchange-rate rules.")}</p>
      <label>{say("支付日期", "Payment date")}<input aria-label={say("结构支付日期", "Structure payment date")} type="text" inputMode="numeric" placeholder="dd/mm/yyyy" value={displayDate(parsed?.event?.on)} onChange={e => updateForm("date", e.target.value)} /></label>
      <label>{say("持股比例（%）", "Ownership (%)")}<input aria-label={say("结构持股比例", "Structure ownership percentage")} type="number" min="0" max="100" value={parsed?.holds?.[0]?.ratio ?? ""} onChange={e => updateForm("ratio", e.target.value)} /></label>
      <label>{say("取得日期", "Acquisition date")}<input aria-label={say("结构取得日期", "Structure acquisition date")} type="text" inputMode="numeric" placeholder="dd/mm/yyyy" value={displayDate(parsed?.holds?.[0]?.since)} onChange={e => updateForm("since", e.target.value)} /></label>
    </div> : <><label htmlFor="structure-json">{say("结构案情（JSON）", "Structure facts (JSON)")}</label><textarea id="structure-json" rows={12} value={draft} onChange={e => setDraft(e.target.value)} /></>}
    {Object.keys(bindings).length > 0 && <details><summary>{say("确认事实归属后，这些字段将在两边同步", "These fields synchronize after their ownership is confirmed")}</summary><ul>{Object.entries(bindings).map(([f, a]) => <li key={f}>{f} → {a}</li>)}</ul></details>}
    <label className="structure-consent"><input type="checkbox" checked={approved} onChange={e => setApproved(e.target.checked)} />{say("本次仅提交合成研究资料，不含真实客户或个人信息。", "Submit synthetic research data only, without real client or personal information.")}</label>
    <button onClick={() => void save()} disabled={busy || !draft}>{say("保存结构案情", "Save structure facts")}</button>
    {current.domain_case && <div className="structure-actions"><button disabled={busy || !ready} onClick={() => void run(() => api.domainPlan(current, crypto.randomUUID()))}>{say("运行结构规划", "Run structure analysis")}</button>
      <button disabled={busy} onClick={() => void run(() => api.domainControl(current, current.domain_workflow?.status === "paused" ? "resume" : "pause"))}>{current.domain_workflow?.status === "paused" ? say("恢复结构分析", "Resume analysis") : say("暂停结构分析", "Pause analysis")}</button></div>}
    {error && <p role="alert" className="request-error">{error}</p>}
    {outcome && <section aria-label={say("结构分析结果", "Structure analysis result")} className="structure-result">
      {outcome.stale && <p role="status">{say("事实已变化，旧结果与问题已过期；请重新运行。", "Facts have changed. Previous results and questions are out of date; run the analysis again.")}</p>}
      <OutcomeView outcome={outcome} />
      {question && !outcome.stale && current.domain_workflow?.status !== "paused" && <div className="structure-question">
        <strong>{question.prompt}</strong><p>{say("答案类型：", "Answer type: ")}{question.answer_schema?.hint || question.answer_schema?.type} · {question.region.join(" / ")}</p>
        {question.source_hint && <p>{say("建议材料：", "Suggested source: ")}{question.source_hint}</p>}
        {["action", "boolean"].includes(question.answer_schema?.type || "") ? <select aria-label={say("结构问题答案", "Structure question answer")} value={value} onChange={e => setValue(e.target.value)}><option value="">{say("请选择", "Select")}</option><option value={question.kind === "action" ? "yes" : "true"}>{say("是", "Yes")}</option><option value={question.kind === "action" ? "no" : "false"}>{say("否", "No")}</option></select> :
          <input aria-label={say("结构问题答案", "Structure question answer")} value={value} onChange={e => setValue(e.target.value)} />}
        <div className="structure-actions"><button disabled={busy} onClick={() => void answer(question)}>{say("提交并重新计算", "Submit and recalculate")}</button>
          <button disabled={busy} onClick={() => void answer(question, "defer", "")}>{say("暂缓此题", "Defer question")}</button>
          {question.kind !== "action" && <button disabled={busy} onClick={() => void answer(question, "answer", "unknown")}>{say("事实未知", "Fact unknown")}</button>}</div>
      </div>}
      <details><summary>{say("全部待补项", "All open items")} ({outcome.question_count ?? outcome.questions.length})</summary><ul>{outcome.questions.map(q => <li key={q.id}>[{q.kind}] {q.key} · {q.prompt}</li>)}</ul></details>
      {professional.length > 0 && <p>{say(`另有 ${professional.length} 项专业判断或资料维护问题，已保留给有权限的复核者。`, `${professional.length} professional or source-maintenance questions are reserved for authorized reviewers.`)}</p>}
      {canReview && professional.map(q => <details key={q.id}><summary>{say("专业/资料维护：", "Professional/source review: ")}{q.prompt}</summary>
        <label>{say("依据引用对象 JSON", "Source reference JSON")}<textarea aria-label={say("专业依据引用", "Professional source reference")} value={reference} onChange={e => setReference(e.target.value)} /></label>
        <label>{say("专业答复（裁量当前只接受有依据的有利判断 yes；日历填写日期数组）", "Professional answer (a favorable decision requires cited evidence; enter dates as an array)")}<input value={professionalValue} onChange={e => setProfessionalValue(e.target.value)} /></label>
        <button disabled={busy} onClick={() => { try { const ref = JSON.parse(reference); const answer = q.kind === "library" ? JSON.parse(professionalValue) : professionalValue;
          void run(() => api.domainProfessional(current, q.id, answer, ref)); } catch { setError(say("引用或日历必须是有效 JSON。", "References or date lists must be valid JSON.")); } }}>{say("保存依据并重新计算", "Save source and recalculate")}</button></details>)}
      <button disabled={busy || !!outcome.stale} onClick={() => void run(() => api.domainConfirm(current))}>{say("确认当前结构事实", "Confirm current structure facts")}</button>
      <label><input type="checkbox" checked={partial} onChange={e => setPartial(e.target.checked)} />{say("同意按当前信息生成部分研究稿，保留全部缺口。", "Create a partial research draft from current information while retaining every gap.")}</label>
      <button disabled={busy || !!outcome.stale || !current.domain_confirmation} onClick={() => void run(() => api.domainReport(current, partial))}>{say("生成合并研究稿", "Generate combined research draft")}</button>
      {canReview && latestReport?.report_hash && !latestReport.stale && latestReport.review?.status === "pending_final_review" && <details>
        <summary>{say("最终研究稿复核", "Final research draft review")}</summary><label>{say("复核决定", "Review decision")}<select value={reviewDecision} onChange={e => setReviewDecision(e.target.value)}>
          <option value="unable_to_conclude">{say("暂不能形成结论", "Unable to conclude")}</option><option value="changes_requested">{say("退回修改", "Request changes")}</option><option value="approved">{say("批准（需满足证据与完整性门槛）", "Approve (evidence and completeness required)")}</option></select></label>
        <label>{say("复核说明", "Review note")}<textarea value={reviewNote} onChange={e => setReviewNote(e.target.value)} /></label>
        <button disabled={busy || !reviewNote.trim()} onClick={() => void run(() => api.finalReview(current, latestReport.id, latestReport.report_hash!, reviewDecision, reviewNote))}>{say("保存最终复核", "Save final review")}</button>
      </details>}
    </section>}
  </div>;
}
