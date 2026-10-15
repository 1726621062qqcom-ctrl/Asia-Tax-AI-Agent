"use strict";

function reviewStep(el, ws) {
  const rows = new Map();
  for (const finding of ws.read || []) rows.set(finding.path, {...finding,found:true});
  for (const conflict of ws.conflicts || []) rows.set(conflict.path, {...rows.get(conflict.path),...conflict,conflict:true});
  for (const violation of ws.violations || []) rows.set(violation.path, {...rows.get(violation.path),...violation,violation:true});
  const entries = [...rows.values()].sort((a,b)=>a.path.localeCompare(b.path));
  const prior = ws.review_data || {};
  const atPath = path => {
    const parts=path.split(".");let obj=ws.input_case;
    if(parts[0]==="holds") {const [holder,held]=parts[1].split(">");obj=(obj.holds||[]).find(h=>h.holder===holder&&h.held===held);return {exists:!!obj&&Object.hasOwn(obj,parts[2]),value:obj?.[parts[2]]};}
    for(const p of parts.slice(0,-1))obj=obj?.[p];
    return {exists:!!obj&&Object.hasOwn(obj,parts.at(-1)),value:obj?.[parts.at(-1)]};
  };
  const core = path => path.endsWith(".loc") || path.startsWith("event.") || path.startsWith("transactions.") || path.startsWith("holds.")&&path.endsWith(".ratio");
  const models=entries.map((r,i)=>{
    const stored=atPath(r.path),saved=prior.data?.[r.path];
    let decision=prior.decisions?.[r.path] || ((saved==="unknown"||saved?.value==="unknown")?"unknown":saved&&!saved.accepted_extracted?"correct":r.conflict||r.violation?"":stored.exists&&JSON.stringify(stored.value)!==JSON.stringify(r.value)?"keep":"accept");
    if(decision.startsWith("option:")&&!r.options?.[Number(decision.slice(7))])decision="";
    const value=saved&&typeof saved==="object"&&!saved.accepted_extracted?saved.value:r.value??stored.value??"";
    const spec={...field(r.path)};
    if(typeof value==="boolean")spec.kind="bool";else if(typeof value==="number"&&!spec.options?.length)spec.kind="number";
    if(r.path.endsWith(".loc")){spec.kind="enum";spec.options=Object.keys(JUR);}
    return {r,i,stored,saved,decision,value,spec};
  });
  el.innerHTML=`<div class="card accent-card"><div class="eyebrow">Document review</div><h2>${entries.length?"Check and correct document findings":"Continue with the recorded facts"}</h2><p class="small muted" style="margin-top:12px">${entries.length?"Accept a finding, keep your saved input, enter a correction or mark the fact unknown. Original evidence is kept with the review.":"No additional values were extracted. You can add supporting documents and analyse again, or continue with the recorded facts. Remaining gaps will be asked explicitly."}</p><form id="findings-form">${models.map(({r,i,stored,saved,decision,value,spec})=>`<section class="review-finding"><div class="q-title">${esc(fieldLabel(r.path))}</div>${r.found?`<div class="review-values"><span class="muted">Document finding</span><strong>${esc(display(r.value))}</strong>${stored.exists&&JSON.stringify(stored.value)!==JSON.stringify(r.value)?`<span class="muted">Saved input</span><strong>${esc(display(stored.value))}</strong>`:""}</div>`:""}${r.violation?`<p class="notice warning">${esc(r.why||r.ask||"This value does not fit the other recorded facts.")}</p>`:""}${r.conflict?`<p class="notice warning">The documents give different values. Select the supported value or enter your own correction.</p>${(r.options||[]).map((o,n)=>`<details class="small"><summary>Finding ${n+1}: ${esc(display(o.value))} · ${esc(o.doc||"Source not recorded")}</summary><blockquote class="quote">${esc(o.quote||"No excerpt recorded")}</blockquote></details>`).join("")}`:""}${r.source||r.quote?`<details class="review-evidence"><summary>View original evidence · ${esc(r.source||"Recorded extraction")}</summary>${r.quote?`<blockquote class="quote">${esc(r.quote)}</blockquote>`:'<p class="small muted">No verbatim excerpt recorded.</p>'}</details>`:""}<label class="field" style="margin-top:14px">Review decision<select id="decision-${i}" data-draft="decision-${i}" required><option value="">Choose a decision</option>${r.found&&!r.violation?'<option value="accept">Accept document finding</option>':""}${(r.options||[]).map((o,n)=>`<option value="option:${n}">Use finding ${n+1}: ${esc(display(o.value))}</option>`).join("")}${stored.exists?'<option value="keep">Keep saved input</option>':""}<option value="correct">Enter corrected value</option>${!core(r.path)?'<option value="unknown">Mark as unknown / reject finding</option>':""}</select></label><div class="review-correction" id="correction-${i}" hidden><div class="form-grid" style="margin-top:14px"><label class="field">Corrected value${control(r.path,value,"corrected-"+i,spec)}</label><label class="field">Source supporting this value<input id="corrected-source-${i}" data-draft="corrected-source-${i}" value="${esc(saved?.source||r.source||"")}" placeholder="Document and page, or another record"></label><label class="field full">Supporting excerpt, if available<textarea id="corrected-quote-${i}" data-draft="corrected-quote-${i}" rows="2" placeholder="Paste the exact supporting text">${esc(saved&&!saved.accepted_extracted?saved.quote||"":"")}</textarea><small>Leave blank if this is a sourced human entry rather than a verbatim document quote.</small></label></div></div><label class="field review-reason" id="reason-wrap-${i}" style="margin-top:12px" hidden>Reason for correction or rejection<input id="reason-${i}" data-draft="reason-${i}" value="${esc(saved?.note||(prior.notes||[]).find(n=>n.startsWith(`Marked unknown: ${r.path}. `))?.slice(`Marked unknown: ${r.path}. `.length)||"")}" placeholder="Explain the change or why this finding is unsupported"></label><p class="small muted" id="review-state-${i}" style="margin-top:9px"></p></section>`).join("")}<div class="form-footer"><button type="submit" class="button">${ws.status==="review"?(entries.length?"Save review and continue":"Continue with recorded facts"):"Save review and reassess"}</button><span class="draft" data-draft-status></span></div><p id="findings-error" class="error-text" role="alert"></p></form></div>`;
  const form=$("#findings-form",el);
  for(const m of models)$("#decision-"+m.i,form).value=m.decision;
  const clear=draft(form,ws.path+".findings."+ws.run.run_id);
  const sync=()=>models.forEach(({i})=>{
    const d=$("#decision-"+i,form).value,correct=d==="correct",reason=correct||d==="unknown";
    $("#correction-"+i,form).hidden=!correct;$("#reason-wrap-"+i,form).hidden=!reason;
    for(const e of $$("input,select,textarea",$("#correction-"+i,form)))e.disabled=!correct;
    $("#corrected-"+i,form).required=correct;$("#corrected-source-"+i,form).required=correct;
    $("#reason-"+i,form).required=reason;$("#reason-"+i,form).disabled=!reason;
    $("#review-state-"+i,form).textContent=d==="unknown"?"The extracted or previously filled value will be removed from the calculation. Unknown is not No.":d==="keep"?"The original saved case input will be used.":d==="accept"?"This document value and its original evidence will be used.":"";
  });
  form.addEventListener("change",sync);sync();
  form.onsubmit=e=>{e.preventDefault();submit($("button[type=submit]",form),$("#findings-error",form),async()=>{
    const data={},decisions={},notes=[];
    for(const {r,i,spec} of models) {
      const decision=$("#decision-"+i,form).value;
      if(!decision)throw Error("Review every finding before continuing");
      decisions[r.path]=decision;
      if(decision==="unknown") {const note=$("#reason-"+i,form).value.trim();data[r.path]={value:"unknown",source:"",quote:"",note};notes.push(`Marked unknown: ${r.path}. ${note}`);}
      else if(decision==="correct") {
        const value=readControl($("#corrected-"+i,form),spec);
        if(value==="unknown")throw Error("Choose Mark as unknown to reject a finding");
        data[r.path]={value,source:$("#corrected-source-"+i,form).value.trim(),quote:$("#corrected-quote-"+i,form).value.trim(),note:$("#reason-"+i,form).value.trim()};
      } else if(decision.startsWith("option:")) {
        const option=r.options[Number(decision.slice(7))];
        data[r.path]={value:option.value,source:option.doc,quote:option.quote};
      }
    }
    await api("/api/proceed",{path:ws.path,data,decisions,notes,review:true,run_id:ws.run.run_id,revision:ws.input_revision,options:settings});clear();await render();
  });};
}
