"""Source-bound extraction guards. Partial dates never become rule-engine dates."""
from copy import deepcopy
from datetime import date
import re

MONTHS = 'January February March April May June July August September October November December'.split()
TRANSACTION_FIELDS = {
    'payer_entity', 'investee_entity', 'holding_percentage_pct', 'direct_or_indirect_holding',
    'dividend_amount', 'dividend_currency', 'accrual_date', 'receipt_date', 'acquisition_date',
    'receipt_location', 'bank_or_account_path', 'continuous_holding_period_months',
    'payer_jurisdiction', 'dividend_form',
}


def date_span(value, text):
    when = date.fromisoformat(value)
    patterns = [re.escape(value), rf'{when.year}年\s*0?{when.month}月\s*0?{when.day}[日号]',
                rf'\b{MONTHS[when.month-1]}\s+0?{when.day}(?:st|nd|rd|th)?[,]?\s+{when.year}\b',
                rf'\b0?{when.day}(?:st|nd|rd|th)?\s+{MONTHS[when.month-1]}[,]?\s+{when.year}\b']
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group()
    return None


def partial_span(value, text):
    when = date.fromisoformat(value)
    for pattern in (rf'{when.year}年\s*0?{when.month}月', rf'\b{MONTHS[when.month-1]}\s+{when.year}\b',
                    rf'(?<!\d){when.year}-{when.month:02}(?!-\d)'):
        match = re.search(pattern, text, re.I)
        if match:
            return {'year': when.year, 'month': when.month, 'precision': 'month', 'source_quote': match.group()}
    match = re.search(rf'(?<!\d){when.year}(?!\d)', text)
    return {'year': when.year, 'precision': 'year', 'source_quote': match.group()} if match else None


def guard_extraction(patch, text, previous=None):
    patch, context = deepcopy(patch), deepcopy(previous or {})
    context.setdefault('partial_dates', {})
    context.setdefault('sources', {})
    # A clear statement of receipt answers the actual/planned question already.
    receipt = re.search(r'\bwe (?:have )?received\b|\bpaid us a dividend\b|(?:我们|我司|本公司)[^。！？\n]{0,60}收到[^。！？\n]{0,35}(?:股息|分红)', text, re.I)
    if (patch and receipt and not re.search(r'如果|假如|尚未|未收到|计划|\bif\b|\bmight\b|\bwould\b|\bnot yet\b|\bplanning\b',
            text[max(0, receipt.start()-20):receipt.end()], re.I)):
        patch.setdefault('income_event_status', 'occurred')
        context['sources']['income_event_status'] = {'source_quote': receipt.group()}
    for field in ('accrual_date', 'receipt_date', 'acquisition_date'):
        value = patch.get(field)
        if not value or value in ('unknown', 'conflict'):
            continue
        span = date_span(value, text)
        if span:
            context['sources'][field] = {'source_quote': span, 'precision': 'day'}
            context['partial_dates'].pop(field, None)
        else:
            patch.pop(field)
            partial = partial_span(value, text)
            if partial:
                context['partial_dates'][field] = partial
    # A description of operations is not a classification or adequacy finding.
    assertions = {
        'entity_hk_business_status': r'在香港经营|在港经营|(?:carry|carrying|carries|conduct|conducting|conducts|operate|operating|operates).{0,30}(?:business|trade).{0,15}Hong Kong',
        'entity_tax_residency': r'tax.residen|税务居民|稅務居民',
        'mne_group_status': r'multinational|跨国|跨國|\bMNE\b',
        'pure_equity_holding_entity_status': r'纯股权持有实体|pure equity[ -]holding entity|not a pure|非纯股权',
        'hk_adequate_employees': r'足够.{0,6}(?:员工|雇员)|adequate.{0,15}employees',
        'hk_adequate_premises': r'足够.{0,6}(?:处所|场所)|adequate.{0,15}premises',
    }
    for field, expression in assertions.items():
        if field in patch and patch[field] not in ('unknown', 'conflict', None) and not re.search(expression, text, re.I):
            patch.pop(field)
    multi = bool(re.search(r'two steps|two (?:planned |possible )?(?:dividends|payments)|first distinguish|两笔|两步|先区分', text, re.I)
                 and re.search(r'dividend|股息|分红', text, re.I))
    if multi:
        context['transaction_scope'] = {'status': 'multiple_unbound', 'source_quote': text[:6000]}
        # Preserve the described chain, not a flat mixture of its separate payments.
        for field in TRANSACTION_FIELDS:
            patch.pop(field, None)
        patch.setdefault('group_structure_description', text[:1000])
    return patch, context
