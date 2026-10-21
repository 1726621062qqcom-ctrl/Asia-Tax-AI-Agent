"use strict";
/* The client's pages (界面.md: one process, five stages). One conversation = one case file; everything shown is derived
   from the case and its run each time it renders. Home: describe -> read-back -> create. Conversation: facts ->
   documents -> review -> questions -> strategies, with the current stage open. Strategy: the steps of one strategy with
   its own assistant. Shared helpers come from app.js (api, esc, control, ...) and execution.js (flowSVG, md, agent). */

const CHAT_DIR = "cases/private/";
const EXAMPLES = [
  "Our Mainland subsidiary paid a dividend of CNY 2,000,000 to our Hong Kong holding company on 30 June 2026; the holding passed it on to our Singapore parent on 15 July 2026.",
  "Our Singapore company lent SGD 5,000,000 to our Hong Kong affiliate in 2025 and receives SGD 250,000 interest on 31 December 2026.",
  "Our Hong Kong subsidiary reduced its capital and returned HKD 3,000,000 to its Mainland parent on 1 September 2026; the parent had paid HKD 2,000,000 for the shares in 2018.",
];
const STAGES = [["facts", "Your facts"], ["documents", "Documents"], ["review", "What the documents say"], ["questions", "A few questions"], ["strategies", "Strategies"]];

function stageOf(ws) {
  const s = ws.status;
  if (s === "review") return "review";
  if (s === "questions") return "questions";
  if (s === "plan") return "strategies";
  return "documents";
}

function stepperHTML(now) {
  const i = STAGES.findIndex(([k]) => k === now);
  return `<div class="stepper">${STAGES.map(([k, l], j) => `<div class="stage ${j < i ? "done" : j === i ? "now" : ""}"><span class="n">${j < i ? "✓" : j + 1}</span>${esc(l)}</div>`).join("")}</div>`;
}

function railHTML(cs, current) {
  const rows = cs.filter(c => c.path.startsWith(CHAT_DIR));
  return `<aside class="rail"><a class="button" href="#/">＋ New conversation</a><div class="rail-list">${rows.length ? rows.map(c => `<div class="rail-item ${c.path === current ? "active" : ""}"><a href="#/chat/${encodeURIComponent(c.path)}"><span class="rail-title">${esc(c.case_id)}</span><span class="pill ${c.status === "plan" ? "ok" : c.status === "error" ? "bad" : c.status === "running" ? "info" : ""}">${esc(STATUSES[c.status] || c.status)}</span></a><button type="button" class="rail-del" data-delete="${esc(c.path)}" title="Delete this conversation" aria-label="Delete">×</button></div>`).join("") : '<p class="small muted" style="padding:6px 10px">No conversations yet.</p>'}</div><p class="rail-foot muted"><a href="#/cases">All case files</a> · <a href="#/new">Structured form</a></p></aside>`;
}

function bindRail(main) {
  $$("[data-delete]", main).forEach(b => b.onclick = async e => {
    e.preventDefault();
    if (!window.confirm("Delete this conversation, its documents and its analysis? This cannot be undone.")) return;
    await api("/api/case/delete", { path: b.dataset.delete });
    toast("Conversation deleted");
    if (location.hash.includes(encodeURIComponent(b.dataset.delete))) location.hash = "#/"; else render();
  });
}

const shell = (cs, current, inner) => `<div class="shell">${railHTML(cs, current)}<section>${inner}</section></div>`;

// ---------------------------------------------------------------- facts
function factsHTML(c) {
  const prov = c.provenance || {}, names = c.names || {}, nm = id => names[id] || id;
  const q = k => prov[k]?.quote ? `<span class="quote">“${esc(prov[k].quote)}”</span>` : "";
  const comp = Object.entries(c.roles || {}).map(([id, r]) => `<span class="co-chip">${esc(nm(id))}<small>${esc(JUR[r.loc] || r.loc)}${c.members?.includes(id) ? "" : " · outside the total"}</small></span>`).join("");
  const holds = (c.holds || []).map(h => `<div class="own-line">${esc(nm(h.holder))}<span class="arrow">→</span>${esc(nm(h.held))}<span class="pill">${num(h.ratio)}%</span>${h.since ? `<span class="muted">since ${esc(h.since)}</span>` : ""}${q(`holds.${h.holder}>${h.held}.ratio`)}</div>`).join("");
  const tx = Object.entries(c.transactions || {}).map(([id, t]) => `<tr><td>${esc(nm(t.payer))} <span class="arrow">→</span> ${esc(nm(t.payee))}${q(`transactions.${id}.amount`)}</td><td>${esc(SCHEMA.transaction_types?.[t.income] || t.income)}</td><td class="num">${amount(t.amount, c)}</td><td>${esc(t.on)}</td><td>${c.settled?.[id] ? esc(Object.entries(c.settled[id]).map(([j, v]) => (JUR[j] || j) + " " + num(v)).join(", ")) : "—"}</td></tr>`).join("");
  return `<div class="chips">${comp}</div>${holds ? `<h3 style="margin:18px 0 6px;font-size:14px">Ownership</h3>${holds}` : ""}<h3 style="margin:18px 0 6px;font-size:14px">Payments</h3><table class="pay-table"><thead><tr><th>From → to</th><th>Kind</th><th class="num">Amount</th><th>Date</th><th>Tax already paid</th></tr></thead><tbody>${tx}</tbody></table><p class="small muted" style="margin-top:10px">Assessed as at ${esc(c.event?.as_at || "—")} · amounts in ${esc(c.currency)} · values read from your description show the sentence they came from.</p>`;
}

function draftReadbackHTML(r, d) {
  const co = id => d.companies.find(x => x.id === id)?.name || id || "?";
  return `<h2>This is what I read</h2><p class="sub">Check it; nothing is saved until you confirm.</p><div class="chips">${d.companies.map(c => `<span class="co-chip">${esc(c.name || "(unnamed)")}<small>${esc(JUR[c.loc] || "jurisdiction not stated")}</small></span>`).join("")}</div>${d.ownership.length ? `<h3 style="margin:18px 0 6px;font-size:14px">Ownership</h3>${d.ownership.map(h => `<div class="own-line">${esc(co(h.holder))}<span class="arrow">→</span>${esc(co(h.held))}<span class="pill">${h.ratio !== "" ? h.ratio + "%" : "% not stated"}</span>${h.since ? `<span class="muted">since ${esc(h.since)}</span>` : ""}<span class="quote">“${esc(r.quotes["ownership." + h.holder + ">" + h.held] || "")}”</span></div>`).join("")}` : ""}<h3 style="margin:18px 0 6px;font-size:14px">Payments</h3><table class="pay-table"><thead><tr><th>From → to</th><th>Kind</th><th class="num">Amount</th><th>Date</th></tr></thead><tbody>${d.transactions.filter(t => t.income).map(t => `<tr><td>${esc(co(t.payer))} <span class="arrow">→</span> ${esc(co(t.payee))}<span class="quote">“${esc(r.quotes["transactions." + t.id] || "")}”</span></td><td>${esc(SCHEMA.transaction_types[t.income] || t.income)}</td><td class="num">${t.amount !== "" ? num(t.amount) + " " + esc(d.currency || "") : "not stated"}</td><td>${t.on ? esc(t.on) : "not stated"}${Object.keys(t.paid || {}).length ? `<div class="small muted">tax paid: ${esc(Object.entries(t.paid).map(([j, v]) => JUR[j] + " " + num(v)).join(", "))}</div>` : ""}</td></tr>`).join("")}</tbody></table>${r.missing.length ? `<div class="callout" style="margin-top:16px"><strong>Still needed:</strong> ${esc(r.missing.join("; "))}. Add them in the form.</div>` : ""}${r.rejected.length ? `<details class="small" style="margin-top:10px"><summary>Left out (${r.rejected.length})</summary><ul>${r.rejected.map(m => `<li>${esc(m)}</li>`).join("")}</ul></details>` : ""}${r.documents.length ? `<p class="small muted" style="margin-top:10px">Documents you mentioned: ${esc(r.documents.join("; "))} — attach them after confirming.</p>` : ""}<div class="actions"><button type="button" class="button" id="chat-confirm" ${r.missing.length ? "disabled" : ""}>Looks right — create the conversation</button><button type="button" class="button secondary" id="chat-correct">Edit in the form</button></div>`;
}

// ---------------------------------------------------------------- home
async function chatHome(main, cs) {
  CURRENT = null;
  const key = "taxgraph.chat.new", saved = readLocal(key, { text: "" });
  main.innerHTML = shell(cs, null, `<div class="hero"><h1>Tell us what happened, or what you plan</h1><p class="lead">In your own words: the companies and where each is incorporated, who holds what share of whom, and each payment — who pays whom, what kind, how much, when. Add any tax already paid and the documents you have.</p><div class="examples">${EXAMPLES.map((x, i) => `<button type="button" class="example" data-example="${i}">${esc(x.slice(0, 70))}…</button>`).join("")}</div><textarea id="chat-text" placeholder="e.g. Shanghai Anxin (Mainland China) is wholly owned by Best China (Hong Kong) since 2019, which is wholly owned by EKH (Singapore). On 30 June 2026 Shanghai Anxin paid a dividend of CNY 2,000,000 to Best China…">${esc(saved.text || "")}</textarea><div class="actions"><button type="button" class="button" id="chat-read">Read my case</button><span class="small muted" id="chat-status"></span></div><p class="error-text" id="chat-error" role="alert"></p><div class="cover"><div><strong>Covered</strong>Mainland China, Hong Kong and Singapore companies; dividends, interest, capital reductions and liquidation distributions; income tax only.</div><div><strong>What you get</strong>Candidate strategies ranked by guaranteed tax, each with its steps, deadlines and documents, and an assistant to carry it out.</div><div><strong>How it works</strong>Rules from the official texts do the calculation; AI only reads your description and documents, and every value shows its source. Nothing is saved until you confirm.</div></div></div><div id="chat-result"></div>`);
  bindRail(main);
  const ta = $("#chat-text", main); ta.oninput = () => writeLocal(key, { text: ta.value });
  $$("[data-example]", main).forEach(b => b.onclick = () => { ta.value = EXAMPLES[Number(b.dataset.example)]; ta.dispatchEvent(new Event("input")); ta.focus(); });
  $("#chat-read", main).onclick = e => submit(e.currentTarget, $("#chat-error", main), async () => {
    const text = ta.value.trim(); if (text.length < 20) throw Error("Describe the case in a few sentences first");
    $("#chat-status", main).textContent = "Reading…";
    try {
      const r = await api("/api/describe", { text, options: settings }); const d = r.draft;
      $("#chat-result", main).innerHTML = `<div class="panel" style="margin-top:16px">${draftReadbackHTML(r, d)}</div>`;
      $("#chat-result", main).scrollIntoView({ behavior: "smooth", block: "start" });
      const draft = Object.assign({}, d, { from_description: true, quotes: r.quotes, missing: r.missing, description: text });
      $("#chat-correct", main).onclick = () => { writeLocal("taxgraph.structure.new", draft); location.hash = "#/new"; };
      const btn = $("#chat-confirm", main);
      if (btn) btn.onclick = () => submit(btn, $("#chat-error", main), async () => {
        const created = await api("/api/case/create", Object.assign({}, d, { case_id: d.case_id || ("Conversation " + new Date().toISOString().slice(0, 16).replace("T", " ")), quotes: r.quotes, description: text }));
        removeLocal(key); toast("Conversation created. Attach documents, then start the analysis.");
        location.hash = "#/chat/" + encodeURIComponent(created.saved);
      });
    } finally { $("#chat-status", main).textContent = ""; }
  });
}

// ---------------------------------------------------------------- conversation
function chatPage(main, ws, cs) {
  CURRENT = ws;
  const c = ws.case, path = ws.path, s = ws.status, now = stageOf(ws);
  const open = (k, title, body, sub = "") => `<div class="panel" id="stage-${k}"><h2>${esc(title)}</h2>${sub ? `<p class="sub">${sub}</p>` : ""}${body}</div>`;
  const folded = (k, title, body) => `<details class="panel quiet" id="stage-${k}"><summary>${esc(title)}</summary><div style="margin-top:12px">${body}</div></details>`;
  const parts = [stepperHTML(now)];
  const factsBody = factsHTML(c) + `<div class="actions"><a class="button secondary" href="#/structure/${encodeURIComponent(path)}">Edit the facts</a><a class="button quiet" href="#/case/${encodeURIComponent(path)}">Full case page</a></div>`;
  parts.push(now === "documents" && !ws.materials?.length && s === "none" ? open("facts", "Your facts", factsBody, c.description ? "Read from your description and confirmed." : "") : folded("facts", "Your facts", factsBody));
  const docs = (ws.materials || []).map(d => `<div class="doc-item">📄 ${esc(d.name)}<span class="pill ok">attached</span></div>`).join("");
  const docsBody = s === "running" ? `<div class="working"><div class="spinner"></div><div>Reading the documents, checking the registers, applying the rules… <span class="small muted">This page updates itself when your input is needed.</span></div></div>`
    : `${s === "stale" ? '<div class="callout">The facts or documents changed since the last analysis. Start it again.</div>' : s === "error" ? `<div class="callout"><strong>The analysis stopped.</strong> ${esc(ws.error?.message || "")}</div>` : ""}<div class="dropzone" id="dropzone">Drop documents here or <label for="chat-attach" style="text-decoration:underline;cursor:pointer">choose files</label><input type="file" id="chat-attach" class="visually-hidden" accept=".pdf,.txt,.md" multiple><div class="small" style="margin-top:6px">Text PDFs, UTF-8 text or Markdown · up to 15 MB each · board resolutions, accounts, bank statements, certificates</div></div><div class="doc-list">${docs || '<p class="small muted">No documents yet. You can start without them; what is missing will be asked.</p>'}</div><div class="actions"><button type="button" class="button" id="chat-analyse">${s === "error" || s === "stale" ? "Start the analysis again" : "Start the analysis"}</button><span class="small muted" id="chat-upload"></span></div>`;
  parts.push(now === "documents" ? open("documents", "Documents and analysis", docsBody) : folded("documents", `Documents (${(ws.materials || []).length})`, docsBody));
  if (now === "review") parts.push(open("review", "What the documents say", '<div id="chat-step"></div>', "Confirm, correct or reject each finding. Only what you confirm is used."));
  if (now === "questions") parts.push(open("questions", "A few questions", '<div id="chat-step"></div>', "These decide the tax. Answer what you can; choose “I don't know” where you cannot — nothing is assumed."));
  if (now === "strategies") parts.push(open("strategies", "Your strategies", strategiesHTML2(ws), "Lowest guaranteed tax first. Each strategy opens with its steps, its documents and its own assistant."));
  main.innerHTML = shell(cs, path, parts.join(""));
  bindRail(main);
  if (now === "review") reviewStep($("#chat-step", main), ws);
  if (now === "questions") questionsWizard($("#chat-step", main), ws);
  const analyse = $("#chat-analyse", main);
  if (analyse) analyse.onclick = e => submit(e.currentTarget, $("#chat-upload", main), async () => { await api("/api/pipeline/run", { case: path, options: settings }); await render(); });
  const upload = async files => {
    const msg = $("#chat-upload", main);
    for (const file of files) {
      try {
        if (file.size > 15 * 1024 * 1024) throw Error("Choose a file smaller than 15 MB");
        msg.textContent = `Adding ${file.name}…`;
        const content = await new Promise((resolve, reject) => { const rd = new FileReader(); rd.onload = () => resolve(String(rd.result).split(",")[1]); rd.onerror = () => reject(Error("Could not read file")); rd.readAsDataURL(file); });
        await api("/api/materials", { path, name: file.name, content });
      } catch (x) { msg.textContent = `${file.name}: ${x.message}`; return; }
    }
    await render();
  };
  if ($("#chat-attach", main)) $("#chat-attach", main).onchange = e => upload([...e.currentTarget.files]);
  const dz = $("#dropzone", main);
  if (dz) { dz.ondragover = e => { e.preventDefault(); dz.classList.add("over"); }; dz.ondragleave = () => dz.classList.remove("over"); dz.ondrop = e => { e.preventDefault(); dz.classList.remove("over"); upload([...e.dataTransfer.files]); }; }
  if (s === "running") POLL = setTimeout(render, 3000);
}

// ---------------------------------------------------------------- questions, one card each, grouped by jurisdiction
function questionsWizard(el, ws) {
  const qs = ws.questions || [];
  const groups = new Map();
  for (const q of qs) { const k = (q.region || []).map(j => JUR[j] || j).join(" and ") || "General"; (groups.get(k) || groups.set(k, []).get(k)).push(q); }
  const KIND = { blocking: "Needed before the tax can be computed", joint: "Needed: too many open items interact", data: "A fact that can lower the guaranteed tax", action: "Something you would do under the plan", ruling: "A determination of the tax authority", library: "Material the library lacks" };
  const idx = new Map(qs.map((q, i) => [q.key, i]));
  const card = q => {
    const i = idx.get(q.key), choice = ["action", "ruling"].includes(q.kind), sp = q.schema || field(q.key);
    const prompt = explainCodes(String(q.prompt).replace(/\s*[(（][^()（）]*[:.][^()（）]*[)）]\s*$/, ""));
    const help = [KIND[q.kind] || "", q.source_hint ? `Usually found in: ${esc(q.source_hint)}` : "", q.impact ? `<span class="impact">Could lower the guaranteed tax by ${amount(q.impact)}</span>` : ""].filter(Boolean).join(" · ");
    const body = choice
      ? `<div class="choice" role="radiogroup">${[["yes", q.kind === "ruling" ? "Yes — we hold the ruling" : "Yes"], ["no", "No"], ["unknown", q.kind === "ruling" ? "Not confirmed" : "Unknown"]].map(([v, l]) => `<label><input type="radio" name="q-${i}" value="${v}" data-draft="q-${i}-${v}"><span>${l}</span></label>`).join("")}</div><label class="field" style="margin-top:12px">${q.kind === "ruling" ? "Basis of your answer (required)" : "Note (optional)"}<input id="reason-${i}" data-draft="reason-${i}" placeholder="${q.kind === "ruling" ? "the ruling or evidence, or why it is not confirmed" : ""}"></label>${q.kind === "ruling" ? '<p class="small muted" style="margin-top:6px">Only confirm a ruling you actually hold. “Not confirmed” keeps both outcomes as separate strategies.</p>' : ""}`
      : `<div class="q-row"><label class="field">${q.kind === "library" ? "Answer" : "Value"}${control(q.key, "", "answer-" + i, sp, false)}${sp.kind === "number" ? `<small>Unit: ${esc(sp.unit === "amount" ? (ws.case.currency || "case currency") : sp.unit || "number")}</small>` : ""}</label>${q.kind !== "library" ? `<label class="field">Source<input id="source-${i}" data-draft="source-${i}" placeholder="document, page or record"><small>Required for a known fact.</small></label>` : ""}</div>${!sp.options?.length && sp.kind !== "bool" ? `<label class="q-unknown"><input type="checkbox" id="unknown-${i}" data-draft="unknown-${i}">I don't know / not available</label>` : ""}`;
    return `<div class="q-card" data-q="${i}"><p class="q-title">${i + 1}. ${esc(prompt)}</p><p class="q-help">${help}</p>${body}</div>`;
  };
  el.innerHTML = `<form id="questions-form"><div class="progress"><i id="q-progress" style="width:0"></i></div><p class="small muted" id="q-count"></p>${[...groups].map(([g, list]) => `<div class="q-group"><h3>${esc(g)}</h3>${list.map(card).join("")}</div>`).join("")}<p class="small muted">Amounts shown as “could lower” can overlap; they are not additive and promise no saving.</p><div class="actions"><button type="submit" class="button">Save answers and continue</button><span class="draft" data-draft-status></span></div><p id="question-error" class="error-text" role="alert"></p></form>`;
  const form = $("#questions-form", el), clear = draft(form, ws.path + ".questions." + ws.run.run_id + "." + qs.map(q => q.key).join("|"));
  const state = () => qs.map((q, i) => {
    if (["action", "ruling"].includes(q.kind)) return !!form.querySelector(`input[name="q-${i}"]:checked`);
    const a = $("#answer-" + i, form), u = $("#unknown-" + i, form);
    return !!(u?.checked || (a && a.value !== ""));
  });
  const refresh = () => { const st = state(); const n = st.filter(Boolean).length; $("#q-progress", form).style.width = (100 * n / Math.max(1, qs.length)) + "%"; $("#q-count", form).textContent = `${n} of ${qs.length} answered`; st.forEach((ok, i) => form.querySelector(`[data-q="${i}"]`)?.classList.toggle("answered", ok)); qs.forEach((q, i) => { const a = $("#answer-" + i, form), u = $("#unknown-" + i, form), src = $("#source-" + i, form); if (a && u) a.disabled = u.checked; if (src) src.disabled = !!(u?.checked || a?.value === "unknown"); }); };
  form.addEventListener("change", refresh); form.addEventListener("input", refresh); refresh();
  form.onsubmit = e => { e.preventDefault(); submit($("button[type=submit]", form), $("#question-error", form), async () => {
    const answers = { data: {}, actions: {}, rulings: {}, library: {} };
    qs.forEach((q, i) => {
      const sec = ({ action: "actions", ruling: "rulings", library: "library" })[q.kind] || "data";
      if (sec === "actions" || sec === "rulings") {
        const v = form.querySelector(`input[name="q-${i}"]:checked`)?.value; if (!v) throw Error(`Question ${i + 1}: choose an answer`);
        const why = $("#reason-" + i, form)?.value.trim(); if (sec === "rulings" && !why) throw Error(`Question ${i + 1}: state the basis of your answer`);
        answers[sec][q.key] = why ? { value: v, reason: why } : v; return;
      }
      const a = $("#answer-" + i, form), u = $("#unknown-" + i, form);
      if (u?.checked || a.value === "unknown") { answers[sec][q.key] = "unknown"; return; }
      if (a.value === "") throw Error(`Question ${i + 1}: enter a value or tick “I don't know”`);
      const value = readControl(a, q.schema || field(q.key));
      if (sec === "data") { const src = $("#source-" + i, form)?.value.trim(); if (!src) throw Error(`Question ${i + 1}: give the source of this fact`); answers.data[q.key] = { value, source: src }; }
      else answers[sec][q.key] = value;
    });
    await api("/api/proceed", { path: ws.path, run_id: ws.run.run_id, revision: ws.input_revision, answers, options: settings }); clear(); await render();
  }); };
}

// ---------------------------------------------------------------- strategies as cards
function strategyRows(p) {
  return p.strategies?.length ? p.strategies : [{ id: 1, guaranteed: p.guaranteed, best: p.best, cand: p.cand, assumes_favourable: [], baseline: true, labels: {}, reasons: {}, fallback: null, plan: p }];
}
function strategiesHTML2(ws) {
  const p = ws.plan, rows = strategyRows(p), path = ws.path, c = ws.case;
  return `<div class="strategy-grid">${rows.map((r, i) => `<div class="s-card ${i === 0 ? "best" : ""}"><div class="rank">${r.baseline ? "Baseline" : "Strategy " + r.id}${i === 0 ? " · lowest guaranteed tax" : ""}</div><div class="amount">${amount(r.guaranteed, c)}<small>guaranteed</small></div><div class="takes">${r.assumes_favourable?.length ? `Counts on: <b>${esc(r.assumes_favourable.map(k => r.labels?.[k] || k).join("; "))}</b>` : "Takes every open ruling against you; no further confirmation needed."}${r.fallback ? `<br>If one fails → strategy ${r.fallback}.` : ""}</div><div class="foot"><span class="small muted">${esc(Object.entries(r.cand || {}).map(([k, v]) => k + "=" + (v === null ? "none" : v)).join(", ") || "the recorded structure")}</span><a class="button compact" href="#/strategy/${encodeURIComponent(path)}/${r.id}">Open</a></div></div>`).join("")}</div><p class="small muted" style="margin-top:14px">Rulings you answered “Not confirmed” fork the strategies. Resolve one in practice, answer it Yes or No, and reassess: the list shrinks. <a href="/api/report?path=${encodeURIComponent(path)}">Download the full report</a>.</p>`;
}

// ---------------------------------------------------------------- one strategy: steps, documents, assistant
function strategyPage(main, ws, sid) {
  CURRENT = ws;
  const c = ws.case, path = ws.path, p = ws.plan;
  if (ws.status !== "plan" || !p) { main.innerHTML = `<a class="back" href="#/chat/${encodeURIComponent(path)}">← Conversation</a><div class="panel"><h2>No completed analysis yet</h2><p class="sub">Finish the analysis in the conversation first.</p></div>`; return; }
  const rows = strategyRows(p), st = rows.find(s => s.id === sid) || rows[0], sp = st.plan || p, e = sp.execution, fb = st.fallback ? rows.find(s => s.id === st.fallback) : null;
  const doneKey = `taxgraph.done.${path}.${st.id}`, done = new Set(readLocal(doneKey, []));
  const numbered = new Map(e.steps.map((s, i) => [s.id, i + 1])), byId = new Map(e.steps.map(s => [s.id, s]));
  const next = byId.get(e.next_action);
  const labels = { todo: "To do", conditional: "Conditional", check_now: "Check now", confirmed_input: "Confirmed in inputs" };
  const stepHTML = s => `<div class="step ${done.has(s.id) ? "done" : ""}" id="execution-${esc(s.id)}"><input type="checkbox" data-done="${esc(s.id)}" ${done.has(s.id) ? "checked" : ""} aria-label="Done"><div><div class="step-title"><h4>${numbered.get(s.id)}. ${esc(s.title)}</h4><span class="pill ${s.status === "check_now" ? "warn" : s.status === "conditional" ? "info" : ""}">${esc(labels[s.status] || s.status)}</span></div>${s.why ? `<p class="step-why">${esc(explainCodes(s.why, c))}</p>` : ""}<p class="step-action">${esc(explainCodes(s.action, c))}</p><div class="step-meta"><span>Owner: ${esc(explainCodes(s.owner, c))}</span>${s.due ? `<span class="pill ${s.status === "check_now" ? "warn" : ""}">by ${esc(s.due)}</span>` : ""}${s.depends_on?.length ? `<span>after step${s.depends_on.length > 1 ? "s" : ""} ${s.depends_on.map(d => numbered.get(d)).filter(Boolean).join(", ")}</span>` : ""}</div>${s.documents?.length ? `<ul class="step-docs">${s.documents.map(d => `<li>${esc(d)}</li>`).join("")}</ul>` : ""}<p class="small muted" style="margin:8px 0 0"><strong>Done when:</strong> ${esc(s.completion)}${s.basis?.length ? ` · ${ruleButton(s.basis)}` : ""}</p></div></div>`;
  const phases = e.phases?.length ? e.phases : [{ title: "Steps", steps: e.steps.map(s => s.id) }];
  main.innerHTML = `<a class="back" href="#/chat/${encodeURIComponent(path)}">← Conversation</a><div class="sv-head"><div><div class="eyebrow">${st.baseline ? "Baseline" : "Strategy " + st.id} of ${rows.length} · ${esc(c.case_id || "")}</div><h1>${st.assumes_favourable?.length ? "Counts on: " + esc(st.assumes_favourable.map(k => st.labels?.[k] || k).join("; ")) : "Every open ruling taken against you"}</h1><div class="sv-nums"><div class="sv-num"><b>${amount(st.guaranteed, c)}</b><span>guaranteed tax</span></div><div class="sv-num"><b>${amount(st.best, c)}</b><span>if every open item turns out favourable</span></div>${fb ? `<div class="sv-num"><b><a href="#/strategy/${encodeURIComponent(path)}/${fb.id}">Strategy ${fb.id}</a></b><span>fallback if a ruling fails (${amount(fb.guaranteed, c)})</span></div>` : ""}</div></div><div class="actions" style="margin:0"><a class="button secondary" href="/api/report?path=${encodeURIComponent(path)}&strategy=${st.id}">Download this strategy</a><button class="button quiet" id="print-strategy">Print / Save PDF</button></div></div><div class="sv-layout"><div>${next ? `<div class="callout ${next.status === "check_now" ? "" : "green"}"><strong>Start here:</strong> step ${numbered.get(next.id)} — ${esc(next.title)}.${next.status === "check_now" ? " A modelled date has already passed: check whether it was done before anything else." : ""}</div>` : ""}<div class="panel"><h2>What this strategy achieves</h2><p class="sub">${esc(explainCodes(e.recommended_course || e.summary, c))}</p>${e.tax_position?.length ? `<table class="pay-table"><thead><tr><th>Jurisdiction</th><th class="num">Guaranteed</th><th class="num">If treatments are supported</th><th>Made up of</th></tr></thead><tbody>${e.tax_position.map(t => `<tr><td>${esc(t.label)}</td><td class="num">${amount(t.conservative, c)}</td><td class="num">${amount(t.favourable, c)}</td><td class="small">${esc(t.items || "—")}</td></tr>`).join("")}</tbody></table>` : ""}<details style="margin-top:14px"><summary class="small">Show the flow of steps</summary>${flowSVG(e)}</details></div>${phases.map((ph, k) => `<div class="phase"><h3><span class="n">${k + 1}</span>${esc(ph.title)}</h3>${ph.steps.map(id => stepHTML(byId.get(id))).join("")}</div>`).join("")}${e.decision_paths?.length ? `<div class="panel"><h2>If a ruling goes the other way</h2>${e.decision_paths.map(d => `<p class="small"><strong>${esc(explainCodes(d.condition, c))}:</strong> if supported, ${esc(explainCodes(d.if_supported, c))} Otherwise: ${esc(explainCodes(d.otherwise, c))}</p>`).join("")}</div>` : ""}<p class="small muted">${esc(e.completion_note || "")}</p></div><div class="sv-assistant">${agentHTML(st)}</div></div>`;
  $("#print-strategy", main).onclick = () => print();
  agentBind(main, ws, st);
  $$("[data-done]", main).forEach(cb => cb.onchange = () => { cb.checked ? done.add(cb.dataset.done) : done.delete(cb.dataset.done); writeLocal(doneKey, [...done]); cb.closest(".step").classList.toggle("done", cb.checked); });
  $$("[data-step]", main).forEach(n => n.onclick = () => $("#execution-" + CSS.escape(n.dataset.step))?.scrollIntoView({ behavior: "smooth", block: "center" }));
  $$("[data-strategy]", main).forEach(b => b.onclick = ev => { ev.preventDefault(); location.hash = `#/strategy/${encodeURIComponent(path)}/${b.dataset.strategy}`; });
  $$("[data-rule]", main).forEach(b => b.onclick = () => submit(b, null, async () => { const ev = await api("/api/evidence?rule=" + encodeURIComponent(b.dataset.rule)); modal(`<h2>Legal basis</h2><p class="small muted">${esc(ev.effect)}</p>${ev.sources.map(s => `<h3>${esc(s.title)}</h3><p class="small muted">${esc(s.label)}</p>${(s.excerpts || []).map(q => `<blockquote class="quote">${esc(q)}</blockquote>`).join("")}<details class="small"><summary>Read full provision</summary><blockquote class="quote">${esc(s.text)}</blockquote></details>${/^https?:\/\//.test(s.url) ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">Official source</a>` : ""}`).join("")}`); }));
}
