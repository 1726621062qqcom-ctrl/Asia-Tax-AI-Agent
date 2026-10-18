'use strict';
const $ = (id) => document.getElementById(id);
let sessionReady = false, busy = false, expired = false, retryRequest = null;
const modeNames = {local_research:'本地资料模式',model_research:'AI 研究草稿',model_fallback:'本地回退模式'};
function el(tag, cls, text) { const node=document.createElement(tag); if(cls)node.className=cls; if(text!==undefined)node.textContent=text; return node; }
function status(text, error=false) { $('status').className='status'+(error?' error':''); $('status').textContent=text; }
async function api(path, method='GET', body) {
  const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-FSIE-Demo':'1'},credentials:'same-origin',body:body===undefined?undefined:JSON.stringify(body)});
  const data=await response.json();
  if(!response.ok) { const err=new Error(typeof data.detail==='string'?data.detail:'输入格式有误，请检查后重试。'); err.status=response.status; throw err; }
  return data;
}
function scrollBottom() { $('conversation').scrollTop=$('conversation').scrollHeight; }
function setBusy(value) {busy=value; $('send').disabled=value; $('send').textContent=value?'研究中…':'发送 ↑'; $('new-chat').disabled=value; $('mobile-new').disabled=value;}
function safeLink(url,text) {const a=el('a','',text);const parsed=new URL(url,location.origin);if(parsed.protocol==='https:'&&['www.ird.gov.hk','www.elegislation.gov.hk'].includes(parsed.hostname)){a.href=url;a.target='_blank';a.rel='noopener noreferrer';}return a;}
function renderFacts(facts) {
  $('facts').replaceChildren();
  if(!facts.length){$('facts').append(el('p','empty-facts','尚未记录公司事实。一般法律问题无需提供公司资料。'));return;}
  for(const fact of facts){const card=el('div','fact-card'+(fact.status==='conflict'?' conflict':''));card.append(el('h3','',fact.label),el('p','',fact.value),el('div','fact-tag',fact.status==='conflict'?'描述有差异 · 请明确更正':'用户描述 · 待核实'));const details=el('details');details.append(el('summary','',`查看依据 · 第 ${fact.turn} 轮`),el('p','',fact.quote));for(const old of fact.previous){details.append(el('p','',`此前第 ${old.turn} 轮：${old.value}`));}card.append(details);$('facts').append(card);}
}
function renderAnswer(answer) {
  const article=el('article','assistant-message');
  const label=el('div','assistant-label','TAXRORA');label.append(el('b','',modeNames[answer.mode]||answer.mode));article.append(label);
  const sources=new Map(answer.citations.map((c,i)=>[c.id,{...c,num:i+1}]));
  for(const section of answer.sections){const block=el('section','answer-section');block.append(el('h3','',section.title));for(const item of section.paragraphs){const p=el('p','',item.text);for(const cid of item.citations){const c=sources.get(cid);if(!c)continue;const a=el('a','citation-link',String(c.num));a.href=`#source-${answer.turn}-${c.num}`;a.setAttribute('aria-label',`查看来源 ${c.num}：${c.title}`);a.addEventListener('click',()=>{article.querySelector('.sources').open=true;});p.append(a);}block.append(p);}article.append(block);}
  if(answer.questions.length){const block=el('div','questions');block.append(el('h3','','接下来，先确认这些信息'));for(const q of answer.questions){const button=el('button','',q);button.type='button';button.addEventListener('click',()=>{$('message').value=q+'\n我的补充：';$('message').focus();});block.append(button);}article.append(block);}
  if(sources.size){const refs=el('details','sources');refs.append(el('summary','',`官方参考资料 · ${sources.size} 项`));for(const c of sources.values()){const card=el('div','source-card');card.id=`source-${answer.turn}-${c.num}`;card.append(safeLink(c.url,`${c.num}. ${c.title} ↗`),el('p','',`${c.source_type==='primary_legislation'?'香港电子法例':'IRD 官方指引'} · ${c.locator} · 未经专业验证`));const detail=el('details');detail.append(el('summary','','展开该版本的原文'),el('blockquote','',c.excerpt));card.append(detail,el('p','',`相关法例定位：${c.statute_reference}`),safeLink(c.statute_url,'打开《税务条例》Cap.112（另行核对条文）'),el('p','',`抓取：${c.retrieved_at.slice(0,10)} · 原文 SHA-256：${c.text_sha256.slice(0,16)}…`));refs.append(card);}article.append(refs);}
  const notes=el('div','warnings');for(const warning of answer.warnings)notes.append(el('p','',warning));article.append(notes);$('messages').append(article);renderFacts(answer.facts);scrollBottom();
}
async function sendMessage(event){
  event?.preventDefault(); if(busy)return;
  const message=$('message').value.trim();if(!message){status('请先输入一个问题。',true);$('message').focus();return;}
  if(expired){status('对话已过期或云服务已重启，请先新建对话。',true);return;}
  if(!$('synthetic-ack').checked){status('请确认本次仅讨论一般问题或虚构案例。',true);$('synthetic-ack').focus();return;}
  setBusy(true);status('正在整理事实与查找官方依据…');
  const request=retryRequest?.message===message?retryRequest:{message,request_id:crypto.randomUUID()};
  let userNode;
  try {
    if(!sessionReady){await api('/api/session','POST',{synthetic_acknowledged:true});sessionReady=true;}
    $('welcome').hidden=true;userNode=el('div','user-message',message);$('messages').append(userNode);$('message').value='';scrollBottom();
    const answer=await api('/api/chat','POST',request);retryRequest=null;renderAnswer(answer);status(answer.mode==='local_research'?'当前为本地资料模式：展示检索结果与固定研究提示，未调用模型。':answer.mode==='model_fallback'?'模型暂不可用或回答未通过校验，本轮已回退到本地资料。':'已完成本轮研究。');
  }catch(err){userNode?.remove();$('message').value=message;retryRequest=request;if(err.status===401){sessionReady=false;expired=true;}status(err.message==='Failed to fetch'?'连接失败，内容已保留。云服务可能正在唤醒，请稍后重试。':err.message,true);if(!expired){const retry=el('button','','重试');retry.type='button';retry.addEventListener('click',()=>sendMessage());$('status').append(retry);}}
  finally{setBusy(false);$('message').focus();}
}
async function clearChat(){try{await api('/api/session','DELETE');sessionReady=false;expired=false;retryRequest=null;$('messages').replaceChildren();$('welcome').hidden=false;$('message').value='';renderFacts([]);status('已清空对话和公司事实。');$('clear-dialog').close();}catch(err){status(err.message,true);$('clear-dialog').close();}}
function requestClear(){if(busy)return;if(!$('messages').children.length){$('message').value='';return;}$('clear-dialog').showModal();}
$('chat-form').addEventListener('submit',sendMessage);
$('message').addEventListener('keydown',(e)=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();sendMessage();}});
$('message').addEventListener('input',()=>{$('counter').textContent=$('message').value.length?`${$('message').value.length} / 4000`:'Enter 发送 · Shift + Enter 换行';});
for(const button of document.querySelectorAll('[data-prompt]'))button.addEventListener('click',()=>{$('message').value=button.dataset.prompt;$('message').focus();status('示例已填入，你可以修改后发送。');});
$('new-chat').addEventListener('click',requestClear);$('mobile-new').addEventListener('click',requestClear);
$('cancel-clear').addEventListener('click',()=>$('clear-dialog').close());$('confirm-clear').addEventListener('click',clearChat);
$('facts-toggle').addEventListener('click',()=>{const open=$('facts-panel').classList.toggle('open');$('facts-toggle').setAttribute('aria-expanded',String(open));$('facts-toggle').textContent=open?'收起公司事实':'查看公司事实';});
$('about-toggle').addEventListener('click',()=>{const hidden=!$('about-detail').hidden;$('about-detail').hidden=hidden;$('about-toggle').setAttribute('aria-expanded',String(!hidden));});
async function loadConfig(){try{const c=await api('/api/config');$('mode').textContent=c.mode==='model_research'?'● 模型已连接':'● 本地资料模式';if(c.mode==='model_research')$('mode').classList.add('online');$('coverage').textContent=`法律覆盖基线 ${c.legal_coverage_cutoff}。`;$('about-detail').textContent=`资料 ${c.corpus_version}；抓取 ${c.retrieved_at.slice(0,10)}。${c.drift?'新快照存在内容漂移，待法律变更复核。':''}${c.mode==='local_research'?'尚未启用模型，使用本地检索与固定研究提示。':'使用已配置模型生成候选研究回答。'}对话最多 20 轮，1 小时无操作过期；刷新页面不恢复历史，云服务休眠或重启会清空对话。`;status(c.mode==='local_research'?'本地资料模式已就绪；可查询、补充和更正虚构案例。':'已就绪。');}catch(err){$('mode').textContent='连接失败';status('无法连接研究服务。云服务可能正在唤醒，请稍后刷新页面。',true);}}
loadConfig();
// Optional imperative WebMCP surface; it stages a question without sending any data.
if(document.modelContext?.registerTool){
  const lifecycle=new AbortController();
  try{Promise.resolve(document.modelContext.registerTool({
    name:'stage_fsie_question',title:'填写 FSIE 研究问题',
    description:'Fill the visible question box. Does not send the message, accept data terms, or call a model.',
    inputSchema:{type:'object',properties:{message:{type:'string',minLength:1,maxLength:4000}},required:['message'],additionalProperties:false},
    annotations:{readOnlyHint:false,untrustedContentHint:true},
    execute(input){if(!input||typeof input.message!=='string'||!input.message.trim()||input.message.length>4000||Object.keys(input).some(k=>k!=='message'))throw new Error('请输入 1–4000 字的问题。');if(busy)throw new Error('上一条消息仍在处理中。');$('message').value=input.message;$('message').focus();status('问题已填入，请检查后发送。');return {staged:true,sent:false};}
  },{signal:lifecycle.signal})).catch(()=>{});}catch(_){/* Optional API unsupported. */}
  window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
}
