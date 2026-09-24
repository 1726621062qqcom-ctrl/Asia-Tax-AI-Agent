"""Conservative local extraction and provenance-preserving conversation updates."""
from __future__ import annotations

import re
from packages.consultation.schemas import Fact, FactCandidate

LABELS = {
    'company_location':'公司所在地', 'hk_business':'香港业务', 'group_structure':'集团关系',
    'income_type':'收入类型', 'holding_percentage':'持股比例与主体', 'holding_period':'持有期间',
    'accrual_date':'收入累算时间', 'receipt_route':'收取路径', 'distribution_form':'分派形式',
    'foreign_tax':'境外税项', 'economic_substance':'香港实际活动', 'commercial_purpose':'商业目的',
}
QUESTIONS = {
    'group_structure':'收款公司属于怎样的集团？其他集团实体或常设机构位于哪些地区？',
    'accrual_date':'这笔股息在哪个日期或年度累算？请与预计收取日期分开说明。',
    'receipt_route':'股息将如何收取或使用？是否汇入香港、偿还香港业务债务或购买带入香港的资产？',
    'hk_business':'收款公司在香港实际开展哪些业务？',
    'holding_period':'收款公司持有派息公司的比例及连续持有期间分别是多少？',
    'economic_substance':'香港有哪些人员、场所和管理活动？是否由外包方承担，如何监督？',
    'foreign_tax':'股息和底层利润分别涉及哪些境外税项、税率或豁免？是否有评税或完税资料？',
    'commercial_purpose':'拟议安排的商业目的是什么？除了税务因素，还有哪些业务约束？',
}
CORRECTION = re.compile(r'说错|更正|改为|纠正|不是.+而是|不是.+是|actually|correction|not .+ but', re.I)
OUTSIDE = re.compile(r'消费税|增值税|个人所得税|薪俸税|遗产税|日本.*(?:税|申报)|韩国.*(?:税|申报)|\b(?:VAT|GST|JCT|payroll tax)\b',re.I)
NON_DIVIDEND = re.compile(r'利息|特许权|知识产权|处置收益|interest|royalt|disposal gain',re.I)
ANCHOR = re.compile(r'FSIE|境外|海外|股息|分红|持股|税务|税法|避税|筹划|香港|免税|抵免|税率|15[H-S]|dividend|Hong Kong|participation|substance',re.I)


def intent_for(message: str, has_context: bool) -> str:
    if OUTSIDE.search(message):
        return 'out_of_scope'
    if NON_DIVIDEND.search(message) and not re.search(r'股息|分红|dividend',message,re.I):
        return 'out_of_scope'
    if CORRECTION.search(message):
        return 'correction' if has_context or ANCHOR.search(message) else 'unknown'
    if re.search(r'筹划|避税|节税|方案|安排|优化|planning|options',message,re.I):
        return 'planning' if has_context or ANCHOR.search(message) else 'unknown'
    if re.search(r'我们|我司|本公司|一家|my company|our company',message,re.I):
        return 'case' if has_context or ANCHOR.search(message) else 'unknown'
    if ANCHOR.search(message):
        return 'law'
    return 'case' if has_context else 'unknown'


PATTERNS = {
    'company_location':r'(?:香港|境外|海外|Hong Kong).{0,12}(?:注册|成立|公司|incorporat)',
    'hk_business':r'(?:香港|Hong Kong).{0,18}(?:经营|业务|贸易|business)',
    'group_structure':r'集团|母公司|子公司|跨国|MNE|subsidiar|parent company',
    'income_type':r'股息|分红|dividend',
    'holding_percentage':r'(?:持有|持股|持有比例|holds?).{0,35}\d+(?:\.\d+)?\s*[%％]',
    'holding_period':r'(?:持有|持股|held).{0,35}(?:\d+\s*(?:年|个月|months|years)|自\s*\d{4})',
    'accrual_date':r'(?:累算|accru).{0,25}\d{4}|\d{4}.{0,25}(?:累算|accru)',
    'receipt_route':r'汇入|汇回|汇款|账户|偿还|债务|带入|remit|account|debt',
    'distribution_form':r'实物股息|现金股息|分派.{0,10}股份|分派.{0,10}现金|in.kind dividend|cash dividend',
    'foreign_tax':r'预提税|企业所得税|境外税|完税|withholding|corporate.{0,10}tax',
    'economic_substance':r'雇员|员工|人员|办公室|外包|开支|employees|premises|outsourc',
    'commercial_purpose':r'商业目的|业务目的|business purpose|commercial purpose',
}


def local_candidates(message: str) -> list[FactCandidate]:
    candidates = []
    sentences = [s.strip() for s in re.split(r'[。；;\n]',message) if s.strip()]
    for key, pattern in PATTERNS.items():
        for sentence in reversed(sentences):
            # Questions are not assertions. Preserve the statement verbatim instead of inventing an entity.
            if re.search(r'[？?]|是否|哪些|怎么|多少|能否',sentence):
                continue
            if re.search(pattern,sentence,re.I):
                quote = sentence[:400]
                clauses = re.split(r'[，,]',sentence)
                matching = [c.strip() for c in clauses if re.search(pattern,c,re.I)]
                value = (matching[-1] if matching else sentence)[:400]
                if key == 'income_type':
                    value = re.search(r'股息|分红|dividend',sentence,re.I).group()
                candidates.append(FactCandidate(key=key,value=value,quote=quote))
                break
    return candidates


def merge_facts(previous: list[Fact], candidates: list[FactCandidate], message: str, turn: int) -> list[Fact]:
    facts = {f.key:f.model_copy(deep=True) for f in previous}
    correcting = bool(CORRECTION.search(message))
    for candidate in candidates:
        if candidate.quote not in message:
            raise ValueError('candidate fact is not grounded in current user turn')
        prior = facts.get(candidate.key)
        if prior and prior.value == candidate.value:
            continue
        history = [] if prior is None else prior.previous + [dict(value=prior.value,quote=prior.quote,turn=prior.turn,status=prior.status)]
        # Local mode is deliberately conservative: changed assertions need explicit correction.
        status = 'conflict' if prior and not correcting else 'user_stated'
        facts[candidate.key] = Fact(key=candidate.key,label=LABELS[candidate.key],value=candidate.value,
            quote=candidate.quote,turn=turn,status=status,previous=history[-8:])
    return list(facts.values())


def followups(facts: list[Fact], intent: str) -> list[str]:
    if intent not in ('case','planning','correction'):
        return []
    conflicts = [f'关于“{f.label}”出现了不同描述，请明确哪一项需要更正：{f.value}' for f in facts if f.status=='conflict']
    keys = {f.key for f in facts if f.status != 'conflict' and not re.search(r'未知|不清楚|不知道|不确定|unknown',f.value,re.I)}
    return (conflicts + [question for key,question in QUESTIONS.items() if key not in keys])[:3]
