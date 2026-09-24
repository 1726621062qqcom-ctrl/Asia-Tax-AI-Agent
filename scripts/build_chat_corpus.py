"""Build the versioned chat corpus from a saved official overview snapshot.

No network calls; existing source manifest and historical snapshots are preserved.
"""
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup,Tag
import argparse
root=Path(__file__).resolve().parents[1]
import sys
if str(root) not in sys.path: sys.path.insert(0,str(root))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--snapshot',type=Path,default=root/'knowledge/hong_kong/fsie/raw/demo/overview.html')
parser.add_argument('--statute-snapshot',type=Path,help='Optional Cap.112 XML snapshot; hash must match the existing manifest')
parser.add_argument('--output',type=Path,default=root/'knowledge/hong_kong/fsie/chat_corpus.json')
args=parser.parse_args()
raw=args.snapshot
html=raw.read_bytes(); soup=BeautifulSoup(html,'html.parser')
# Curated Chinese research notes paired with the actual official section, not model-generated conclusions.
notes={
'a02':('income','覆盖的境外收入',['股息','分红','dividend','生效','2023','2024'], '先区分收入种类和累算时间。IRD 指引列明境外股息从 2023 年 1 月 1 日起纳入新机制的相关范围；是否征税仍需继续检查纳税主体、在港收取及例外条件。','s.15H'),
'a04':('scope','哪些企业属于适用范围',['跨国','集团','mne','香港公司','主体','范围'], '先核实收款实体是否属于跨国企业集团，以及是否在香港经营业务。香港注册、海外持股或单个持股比例，不能独自完成全部适用范围判断。','s.15H / s.15I'),
'a05':('timing','累算年度与收取年度',['累算','时间','日期','收到','accrual','receipt','征税','条文'], '分析需分开记录收入累算和在香港收取的时间。经济实质、参与等例外的相关条件应按收入累算年度检查；不能把裁定日期或汇款日期自动当作累算日期。','s.15I'),
'a06':('receipt','何时视为在香港收取',['汇款','收取','账户','境外账户','债务','实物','股份','现金','remit','received'], 'IRD 列明三类在港收取情形：汇入或带入香港、用于清偿香港业务债务，以及用于购买其后带入香港的动产。仅说钱放在境外账户还不足以排除视为收取；股份分派也需要逐步核对资产和交易路径。','s.15H'),
'a07':('exceptions','股息的例外路径',['豁免','免税','条件','exemption','路径','筹划','合规','避税'], '境外股息可研究经济实质要求或参与要求这两条例外路径；应按各自完整条件检查。不能仅凭“境外收入”或“持股超过某比例”承诺免税。','s.15K / s.15M'),
'a08':('substance','经济实质与外包要求',['经济实质','人员','雇员','办公室','开支','外包','纯控股','substance'], '经济实质路径区分纯股权持有实体与其他实体。需核实香港实际活动、人员、场所或开支及相关合规要求；“是否足够”取决于事实，不能用自造人数或金额阈值代替判断。外包必须满足在香港开展、足够监督及资源等要求，不能只是纸面安排。','s.15K'),
'a10':('participation','参与要求与反滥用规则',['参与','持股','比例','12个月','5%','税率','15%','预提税','反避税','商业目的','participation','withholding'], '参与路径需检查香港居民身份，或非居民在香港有常设机构且收入归属于该机构的条件，以及收入累算前连续至少 12 个月持有至少 5% 股权等条件；同时适用 subject-to-tax 转换、反混合错配和主要目的规则。企业所得税和股息预提税须分别记录，不能只见一个税率就决定是否满足条件。','s.15M / s.15N'),
'a13':('credit','避免双重征税与税收抵免',['抵免','双重征税','境外税','已缴税','credit'], '若相关境外收入须在香港纳税，可进一步核查境外类似税项的抵免或扣除。抵免受居民身份、税项、税额上限等条件限制；底层利润税的抵免另有持股条件，不能与参与路径的持股门槛混用。','税收抵免相关条文须按具体路径另核'),
'a14':('obligations','申报与记录保存',['申报','报税','记录','期限','filing'], '应分别核对累算年度和收取年度的申报义务，并保存证明持股、收款、境外税和实际活动的资料。例外路径的研究不等于可以忽略申报或记录保存。','Taxpayer’s Obligations'),
'a15':('advance','事先裁定',['裁定','确定性','advance','ruling'], '对经济实质条件存在不确定性时，可以研究向税务局申请事先裁定。申请资格、程序和裁定覆盖范围需要按官方说明核实，其他公司的裁定不能直接作为本公司的结论。','s.88A（程序入口）'),
}
units=[]
for anchor,(topic,title,tags,note,statute) in notes.items():
    p=soup.find(id=anchor).find_parent('p')
    chunks=[]
    for node in p.next_siblings:
        if not isinstance(node,Tag): continue
        if node.find('a',id=re.compile('^a[0-9]+$')): break
        if node.name=='hr' or node.select('.arrowtop'): continue
        text=' '.join(node.get_text(' ',strip=True).split())
        if text: chunks.append(text)
    body='\n\n'.join(chunks)
    assert len(body)>50,(anchor,body)
    units.append(dict(id='ird-fsie-'+topic,source_id='hk_ird_fsie_landing',title=title,topic=topic,tags=tags,
        url='https://www.ird.gov.hk/eng/tax/bus_fsie.htm#'+anchor,source_type='official_guidance',
        locator=anchor,statute_reference=statute,statute_url='https://www.elegislation.gov.hk/hk/cap112!en',
        text=body,text_sha256=hashlib.sha256(body.encode()).hexdigest(),research_note_zh=note,
        effective_from=None,effective_to=None,temporal_status='current_page_snapshot_not_historical_law',
        professional_validation_status='unverified'))
manifest=json.loads((root/'knowledge/hong_kong/fsie/source_manifest.json').read_text())
old=next(s for s in manifest['sources'] if s['source_id']=='hk_ird_fsie_landing')['content_sha256']
actual=hashlib.sha256(html).hexdigest()
for unit in units:
    unit['source_sha256']=actual
    unit['source_retrieved_at']=datetime.fromtimestamp(raw.stat().st_mtime,timezone.utc).isoformat()
    unit['source_drift']=actual!=old
statute_meta=None
if args.statute_snapshot:
    from packages.knowledge_pipeline.segment import segment_cap112
    content=args.statute_snapshot.read_bytes()
    law_source=next(s for s in manifest['sources'] if s['source_id']=='hk_hkel_iro_cap112')
    law_hash=hashlib.sha256(content).hexdigest()
    if law_hash!=law_source['content_sha256']:
        raise ValueError('Statute differs from manifest; review and version it before inclusion')
    groups={}
    for draft in segment_cap112(content):
        section=draft.statute_locator.split('(')[0]
        groups.setdefault(section,[]).append(draft)
    specs={
      's.15H':('scope','定义与在港收取','定义、MNE、指定境外收入与在港收取需按第 15H 条的具体措辞核对；第 15H(5) 条列出视为在港收取的情形。'),
      's.15I':('timing','境外收入视为源自香港','第 15I 条规定相关收入在港收取时的视同来源及适用条件，并受后续例外条文限制。判断不能停留在本条而忽略例外。'),
      's.15K':('substance','经济实质例外','第 15K(2) 条把经济实质检查放在收入累算年度，区分纯股权持有实体与其他实体；人员、场所或开支是否足够涉及税务局的判断。'),
      's.15M':('participation','参与条件例外','第 15M(2) 条列出累算前连续至少 12 个月持有至少 5% 股权的条件；同时要满足第 15M(1) 条的身份及收入归属等条件，并受第 15N 条限制。'),
      's.15N':('participation','参与例外的限制','第 15N 条规定参与例外的限制，涉及合资格类似税、混合错配及主要目的等。第 15N(7) 条的 15% 是参考税率，不能单凭预提税数字判断整条路径。'),
      's.15O':('participation','直接及间接被投实体','第 15O 条为第 15N 条补充直接、间接被投实体的定义，分析底层利润税时需要核对投资链条。'),
      's.15S':('obligations','记录保存','第 15S 条规定相关记录保存要求；即使研究某项例外，也应核实适用的记录保存期限与证明资料。'),
    }
    retrieved=datetime.fromtimestamp(args.statute_snapshot.stat().st_mtime,timezone.utc).isoformat()
    statute_meta=dict(source_id=law_source['source_id'],source_sha256=law_hash,retrieved_at=retrieved,drift=False)
    for section,(topic,title,note) in specs.items():
        drafts=groups[section]
        body='\n\n'.join(d.text for d in drafts)
        units.append(dict(id='cap112-'+section[2:],source_id=law_source['source_id'],title='《税务条例》'+section+' · '+title,
            topic=topic,tags=[section,section[2:],title],url=law_source['url'],source_type='primary_legislation',
            locator=section,subsection_locators=[d.statute_locator for d in drafts],statute_reference=section,statute_url=law_source['url'],
            text=body,text_sha256=hashlib.sha256(body.encode()).hexdigest(),research_note_zh=note,
            effective_from=None,effective_to=None,temporal_status='manifest_matched_snapshot_not_historical_law',
            professional_validation_status='unverified',source_sha256=law_hash,source_retrieved_at=retrieved,source_drift=False))
data=dict(version='chat-corpus-0.2.0',retrieved_at=datetime.fromtimestamp(raw.stat().st_mtime,timezone.utc).isoformat(),
    legal_coverage_cutoff=manifest['legal_coverage_cutoff'],
    coverage_note='Snapshot acquisition is not a legal currency review. Historical/future applicability must be checked separately.',
    source_sha256=actual,source_manifest_sha256=old,drift_from_manifest=actual!=old,
    statute_snapshot=statute_meta,review_status='engineering_curated_unverified',units=units)
args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Built',len(units),'units;',sum(len(u['text']) for u in units),'characters; guidance drift:',actual!=old)
