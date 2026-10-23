import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import { useLocale } from "../locale";
import { engineText, questionText } from "../engine-language";
import type { Case } from "../workspace";

export default function CalculationFacts({ current, onUpdate, busy }: {
  current: Case; onUpdate: (doc: Case) => void; busy: boolean;
}) {
  const { locale } = useLocale();
  const say = (zh: string, en: string) => locale === "en" ? en : zh;
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const retry = useRef({ payload: "", id: "" });
  const outcome = current.domain_outcome;
  const questions = outcome?.questions.filter(q => q.interview_status === "ready" &&
    ["data", "blocking", "joint", "action"].includes(q.kind)) || [];
  const blocked = busy || saving || !!outcome?.stale || current.domain_workflow?.status === "paused";
  const answers = questions.filter(q => values[q.id]?.trim()).map(q => ({
    key: q.key, kind: q.kind, question_id: q.id, value: values[q.id].trim(),
  }));
  async function submit() {
    const payload = JSON.stringify([current.revision, answers]);
    if (retry.current.payload !== payload) retry.current = { payload, id: crypto.randomUUID() };
    setSaving(true); setError("");
    try {
      const next = await api.domainAnswers(current, answers, retry.current.id, locale);
      onUpdate(next); setValues({});
    } catch (e) {
      const code = e instanceof ApiError ? e.code : "network_error";
      setError(code === "question_changed" || code === "revision_conflict"
        ? say("案例已更新，请刷新后核对最新问题再提交。", "The case changed. Refresh and review the latest questions before submitting.")
        : code === "invalid_domain_answer"
          ? say("有一项填写格式不正确，请核对数字、日期或选项。整批内容尚未保存。", "Check the numbers, dates and choices. No answers in this batch were saved.")
          : say("提交未完成，请重试。已填写内容仍保留。", "Submission did not complete. Your entries are retained; please retry."));
    } finally { setSaving(false); }
  }
  return <section className="calculation-facts">
    <h3>{say("集中补充计算资料", "Complete calculation details")}</h3>
    <p>{say("可一次填写多项，再统一提交计算。留空表示暂不填写；不确定请选择“暂不清楚”，不会被当成“否”或零。", "Fill in several items and submit once to recalculate. Leave items blank to skip them, or choose Unknown. Missing facts are never treated as no or zero.")}</p>
    {outcome?.stale && <p role="alert">{say("事实已变更，请先在结构分析中重新计算以更新问题。", "Facts have changed. Recalculate in Structure analysis to refresh these questions.")}</p>}
    {current.domain_workflow?.status === "paused" && <p>{say("计算已暂停，请先在结构分析中恢复。", "Calculation is paused. Resume it in Structure analysis first.")}</p>}
    <div className="facts-field-grid">
      {questions.map(q => {
        const type = q.answer_schema?.type || "text";
        const value = values[q.id] || "";
        const set = (v: string) => setValues(all => ({ ...all, [q.id]: v }));
        return <div className="fact-field" key={q.id}>
          <label htmlFor={`batch-${q.id}`}>{questionText(q, locale)}</label>
          <small>{engineText(q.key.split(".")[0].replace(/^interview:/, "").replace(/^flow:(.*)$/, say("资金流 $1", "Cash flow $1")), locale)} · {q.region.map(r => engineText(r, locale)).join(" / ")}</small>
          {type === "boolean" || q.kind === "action" ? <select id={`batch-${q.id}`} disabled={blocked} value={value} onChange={e => set(e.target.value)}>
            <option value="">{say("待填写", "Select")}</option>
            <option value="yes">{say("是", "Yes")}</option><option value="no">{say("否", "No")}</option>
            {q.kind !== "action" && <option value="unknown">{say("暂不清楚", "Unknown")}</option>}
          </select> : <>
            {value === "unknown" ? <p>{say("暂不清楚", "Unknown")}</p> : <input id={`batch-${q.id}`} disabled={blocked} value={value}
              type={type === "date" ? "date" : type === "number" ? "number" : "text"} min={type === "number" ? 0 : undefined} step="any" maxLength={1000}
              onChange={e => set(e.target.value)} />}
            <div className="fact-tools"><button type="button" disabled={blocked} onClick={() => set(value === "unknown" ? "" : "unknown")}>
              {value === "unknown" ? say("重新填写", "Enter a value") : say("暂不清楚", "Unknown")}</button></div>
          </>}
        </div>;
      })}
    </div>
    {!questions.length && <p>{say("当前没有可直接填写的问题。未决条件及专业复核事项请查看结构分析结果。", "There are no directly answerable questions now. See Structure analysis for unresolved conditions and professional review items.")}</p>}
    <p>{say("只有前提明确后，才会显示对应细节；未填写项目不会阻止查看当前条件下的试算结果。", "Dependent details appear only after their prerequisites are established. You can still view the conditional estimate without completing every item.")}</p>
    {error && <p role="alert" className="fact-conflict">{error}</p>}
    <button className="primary-button" disabled={blocked || !answers.length} onClick={submit}>
      {saving ? say("正在统一计算…", "Recalculating…") : say(`提交 ${answers.length} 项并重新计算`, `Submit ${answers.length} items and recalculate`)}
    </button>
  </section>;
}
