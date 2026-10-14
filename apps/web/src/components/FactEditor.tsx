import { useState } from "react";
import { useLocale } from "../locale";
import { fieldLabel, type Case, type FieldSpec, type FactValue } from "../workspace";
import type { FactPatch } from "../api";

const steps = [
  { title: ["收款主体", "Recipient"], hint: ["先确认是谁收款，以及它所在的集团。", "Start with the recipient and its group."], domains: ["entity_and_group", "intake_context"] },
  { title: ["收入情况", "Income"], hint: ["填写收入种类、金额与发生时间。", "Describe the income, amount and timing."], domains: ["dividend_identity"] },
  { title: ["收款路径", "Receipt"], hint: ["说明资金到哪里、何时到账，以及是否经过抵销或现金池。", "Record where and when the payment was received."], domains: ["receipt_path"] },
  { title: ["持股关系", "Ownership"], hint: ["核对直接或间接持股、比例和持有期间。", "Check ownership, percentage and holding period."], domains: ["participation_holding"] },
  { title: ["境外税务", "Foreign tax"], hint: ["记录已知的境外征税情况，是否可抵免留待核对。", "Record known foreign-tax facts; eligibility still needs review."], domains: ["foreign_taxation"] },
  { title: ["香港经营", "Hong Kong activity"], hint: ["说明在港开展的活动、人员和场所。", "Describe Hong Kong activities, staff and premises."], domains: ["hk_economic_substance"] },
  { title: ["安排与资料", "Arrangement and records"], hint: ["补充商业背景、特殊安排和可提供的凭证。", "Add commercial background, special arrangements and available records."], domains: ["commercial_purpose_anti_abuse", "evidence_documents"] },
] as const;

const starterFields = [
  "entity_hk_business_status", "mne_group_status", "income_type", "dividend_amount",
  "dividend_currency", "accrual_date", "receipt_location", "receipt_date",
  "direct_or_indirect_holding", "holding_percentage_pct",
];
const prompts: Record<string, [string, string]> = {
  entity_hk_business_status: ["收款公司在香港经营业务吗？", "Does the recipient carry on business in Hong Kong?"],
  mne_group_status: ["收款公司属于跨国企业集团吗？", "Is the recipient part of a multinational enterprise group?"],
  income_type: ["这笔收入是什么类型？", "What type of income is this?"],
  dividend_amount: ["这笔股息的金额是多少？", "What is the dividend amount?"],
  dividend_currency: ["使用哪种币种？", "What is the currency?"],
  accrual_date: ["收入在什么时候累算？", "When did the income accrue?"],
  receipt_location: ["股息在哪里收取？", "Where was the dividend received?"],
  receipt_date: ["实际或视为收取日期是什么时候？", "When was it received or deemed received?"],
  direct_or_indirect_holding: ["与派息公司是什么持股关系？", "How does the recipient hold the payer?"],
  holding_percentage_pct: ["持股比例是多少？", "What is the ownership percentage?"],
};
function belongsTo(field: FieldSpec, domains: readonly string[]) {
  return domains.includes(field.domain || "intake_context");
}

export default function FactEditor({ current, fields, busy, onSave, onConfirm }: {
  current: Case;
  fields: FieldSpec[];
  busy: boolean;
  onSave: (patch: FactPatch) => void;
  onConfirm: () => void;
}) {
  const { t, locale } = useLocale();
  const say = (zh: string, en: string) => locale === "en" ? en : zh;
  const initial = Object.fromEntries(Object.entries(current.facts).map(([key, record]) => [key, record.value]));
  const [draft, setDraft] = useState<Record<string, FactValue>>(initial);
  const [extra, setExtra] = useState<string[]>([]);
  const [step, setStep] = useState(0);
  const [useStarter] = useState(Object.keys(initial).length === 0 && current.questions.length === 0);
  const patch: FactPatch = {};
  for (const [key, value] of Object.entries(draft)) {
    const type = fields.find(field => field.field_name === key)?.data_type;
    let normalized: FactValue | null = typeof value === "string" ? value.trim() : value;
    if (normalized === "") normalized = null;
    else if (typeof normalized === "string" && !["unknown", "conflict"].includes(normalized)) {
      if (type === "list") normalized = normalized.split(",").map(item => item.trim()).filter(Boolean);
      else if (["integer", "decimal"].includes(type || "") && Number.isFinite(Number(normalized))) normalized = Number(normalized);
    }
    if (JSON.stringify(normalized) !== JSON.stringify(initial[key] ?? null)) patch[key] = normalized;
  }
  const dirty = Object.keys(patch).length > 0;
  const keys = new Set([...Object.keys(draft), ...current.questions, ...extra]);
  if (useStarter) starterFields.forEach(key => keys.add(key));
  const visible = fields.filter(field => keys.has(field.field_name));
  const currentStep = steps[step];
  const review = step === steps.length;
  const stepFields = review ? [] : visible.filter(field => belongsTo(field, currentStep.domains));
  const remaining = review ? [] : fields.filter(field => belongsTo(field, currentStep.domains) && !keys.has(field.field_name));
  const conflicts = Object.values(current.facts).filter(record => record.value === "conflict").length +
    Object.entries(patch).filter(([key, value]) => value === "conflict" && current.facts[key]?.value !== "conflict").length;
  function label(field: FieldSpec) {
    const prompt = prompts[field.field_name];
    return prompt ? prompt[locale === "en" ? 1 : 0] : fieldLabel(field, locale);
  }
  function change(key: string, value: FactValue) {
    setDraft(all => ({ ...all, [key]: value }));
  }
  function displayValue(value: string | number) {
    const translated = t(`value:${value}`);
    return translated.startsWith("value:") ? String(value) : translated;
  }
  function renderField(field: FieldSpec) {
    const key = field.field_name;
    const value = draft[key] ?? "";
    const numeric = ["integer", "decimal"].includes(field.data_type);
    return <div key={key} className="fact-field">
      <label htmlFor={`fact-${key}`}>{label(field)}</label>
      {field.data_type === "enum" ? <select id={`fact-${key}`} value={String(value)} disabled={busy} onChange={event => change(key, event.target.value)}>
        <option value="">{t("待补充")}</option>
        {[...new Set([...(field.enum_values || []), "unknown", "conflict"])].map(option =>
          <option value={option} key={option}>{displayValue(option)}</option>)}</select> :
        <input id={`fact-${key}`} disabled={busy} aria-label={label(field)}
          value={Array.isArray(value) ? value.join(", ") : value} inputMode={numeric ? "decimal" : undefined}
          maxLength={1000} placeholder={field.data_type === "date" ? "YYYY-MM-DD" : t("待补充")}
          onChange={event => change(key, event.target.value)} />}
      <div className="fact-tools"><span>{current.facts[key]?.origin === "model" ? t("模型提取，待核对") : t("手工记录")}</span>
        <button type="button" disabled={busy} onClick={() => change(key, "unknown")}>{t("暂不清楚")}</button></div>
      {value === "conflict" && <p className="fact-conflict">{say("此项存在冲突，请核对后选择正确值。", "This fact conflicts with another value. Check it before continuing.")}</p>}
    </div>;
  }
  return <div className="facts-guide">
    <div className="facts-intro">
      <p className="facts-kicker">{say("案例事实模板", "Case facts template")}</p>
      <h3>{review ? say("核对后再提交", "Review before submitting") : currentStep.title[locale === "en" ? 1 : 0]}</h3>
      <p>{review ? say("以下是本案已记录和本次填写的内容。未填写的项目不会被猜测。", "These are the facts recorded or entered for this case. Missing values will not be inferred.") : currentStep.hint[locale === "en" ? 1 : 0]}</p>
      <p className="facts-progress">{say(`第 ${step + 1} 步，共 ${steps.length + 1} 步`, `Step ${step + 1} of ${steps.length + 1}`)}</p>
    </div>
    <nav className="facts-steps" aria-label={say("填写步骤", "Fact entry steps")}>
      {[...steps.map(item => item.title[locale === "en" ? 1 : 0]), say("核对提交", "Review")].map((title, index) =>
        <button key={title} type="button" className={index === step ? "active" : ""} aria-current={index === step ? "step" : undefined}
          onClick={() => setStep(index)}>{String(index + 1).padStart(2, "0")} <span>{title}</span></button>)}
    </nav>
    <div className="facts-step-content">
      {!review && <>
        {stepFields.length ? <div className="facts-field-grid">{stepFields.map(renderField)}</div> :
          <p className="facts-empty">{say("这一部分暂时没有待核对事实；如有需要，可在下方添加。", "No facts to review in this section yet. Add one below if needed.")}</p>}
        {remaining.length > 0 && <label className="facts-add-field">{say("补充这一部分的其他事实", "Add another fact in this section")}
          <select value="" disabled={busy} onChange={event => { if (event.target.value) setExtra(all => [...all, event.target.value]); }}>
            <option value="">{t("选择需要补充的事实")}</option>
            {remaining.map(field => <option key={field.field_name} value={field.field_name}>{label(field)}</option>)}
          </select></label>}
      </>}
      {review && <>
        {visible.length ? <div className="facts-review-list">{steps.map((item, index) => {
          const group = visible.filter(field => belongsTo(field, item.domains));
          if (!group.length) return null;
          return <section key={item.title[0]}><div className="facts-review-heading"><h4>{item.title[locale === "en" ? 1 : 0]}</h4>
            <button type="button" onClick={() => setStep(index)}>{say("修改", "Edit")}</button></div>
            <dl>{group.map(field => { const value = draft[field.field_name]; return <div key={field.field_name}>
              <dt>{label(field)}</dt><dd>{value == null || value === "" ? say("未填写", "Not entered") : Array.isArray(value) ? value.join(", ") : displayValue(value)}</dd>
            </div>; })}</dl></section>;
        })}</div> : <p className="facts-empty">{say("还没有记录任何事实。请先完成前面的步骤。", "No facts recorded yet. Complete the earlier steps first.")}</p>}
        {conflicts > 0 && <p className="fact-conflict" role="alert">{say("存在冲突事实，须先修正才能确认分析。", "Resolve conflicting facts before confirming the analysis.")}</p>}
        <div className="facts-submit"><button className="primary-button" disabled={busy || !dirty} onClick={() => onSave(patch)}>{t("保存事实")}</button>
          <p className="panel-note">{t("确认将锁定当前事实版本；后续修改会使旧分析过期。")}</p>
          <button className="primary-button" disabled={busy || dirty || !Object.keys(current.facts).length || conflicts > 0} onClick={onConfirm}>{t("确认事实并分析")}</button>
          {dirty && <small>{t("请先保存修改，再确认。")}</small>}</div>
      </>}
      <div className="facts-navigation">
        <button type="button" disabled={step === 0} onClick={() => setStep(index => index - 1)}>{say("上一步", "Back")}</button>
        {!review && <button type="button" className="primary-button" onClick={() => setStep(index => index + 1)}>
          {step === steps.length - 1 ? say("核对并提交", "Review and submit") : say("下一步", "Continue")}</button>}
      </div>
    </div>
  </div>;
}
