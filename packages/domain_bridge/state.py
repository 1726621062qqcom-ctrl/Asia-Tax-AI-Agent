"""One revisioned fact source; B facts and Li cases are derived projections."""
from copy import deepcopy
from hashlib import sha256
import json
import re

VERSION = '2.0.0'
MAP_VERSION = 'li-b-map-2026-10-11'


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                             allow_nan=False).encode()).hexdigest()


def ensure(doc):
    if doc.get('schema_version') == VERSION:
        return
    doc['schema_version'] = VERSION
    doc['migration'] = {'from': '1', 'facts_snapshot': deepcopy(doc.get('facts', {})),
                        'at_revision': doc['revision'], 'map_version': MAP_VERSION}
    doc['canonical_fact_records'] = {}
    doc['legacy_bindings'] = {}
    for field, record in doc.get('facts', {}).items():
        write(doc, 'legacy.' + field, record['value'], record.get('origin', 'migration'),
              revision=record.get('revision', doc['revision']), metadata=record)
    if doc.get('domain_case'):
        install(doc, doc['domain_case'], {})


def write(doc, address, value, source, *, revision=None, metadata=None, unit=None):
    records = doc['canonical_fact_records']
    if value is None:
        records.pop(address, None)
        return
    status = 'unknown' if value == 'unknown' else 'conflict' if value == 'conflict' else 'candidate' if source == 'model' else 'user_entered'
    if unit is None:
        unit = 'EUR' if address.endswith('_eur') else 'percent' if address.endswith(('_rate', '.ratio')) else None
    records[address] = {**(metadata or {}), 'address': address, 'value': deepcopy(value),
                        'origin': source, 'status': status, 'unit': unit,
                        'revision': doc['revision'] + 1 if revision is None else revision,
                        'confirmed_at': None}


def legacy_write(doc, field, value, origin, message_id=None):
    ensure(doc)
    address = doc['legacy_bindings'].get(field, 'legacy.' + field)
    write(doc, address, value, origin, metadata={'message_id': message_id})
    sync(doc)


def _usable(record):
    return record is not None and record['status'] not in ('unknown', 'conflict', 'deferred')


def install(doc, case, bindings):
    """Replace the graph, then bind only explicitly confirmed legacy field addresses."""
    from packages.domain_bridge.bridge import DomainCase
    from packages.chat.facts import catalog
    ensure(doc)
    case = DomainCase.model_validate(case).model_dump(mode='json')
    previous = deepcopy(doc.get('facts', {}))
    old_bindings = deepcopy(doc.get('legacy_bindings', {}))
    # Detach old bindings before replacing the domain graph; preserve legacy values.
    for field, record in previous.items():
        write(doc, 'legacy.' + field, record['value'], record.get('origin', 'user'), metadata=record)
    doc['legacy_bindings'] = {}
    records = doc['canonical_fact_records']
    for address in list(records):
        if not address.startswith('legacy.'):
            records.pop(address)
    definition = {k: deepcopy(case[k]) for k in ('template', 'currency', 'present', 'members', 'settled', 'closed', 'subject', 'notes')}
    definition['roles'] = {key: {'type': role['type']} for key, role in case['roles'].items()}
    definition['holds'] = [{'holder': h['holder'], 'held': h['held']} for h in case['holds']]
    definition['flows'] = list(case['flows'])
    write(doc, 'case.currency', case['currency'], 'user')
    for role, values in case['roles'].items():
        write(doc, role + '.loc', values['loc'], 'user')
        for key, value in values['attrs'].items():
            write(doc, role + '.' + key, value, 'user')
    for hold in case['holds']:
        prefix = f"hold:{hold['holder']}>{hold['held']}."
        for key in ('ratio', 'since', 'cost'):
            write(doc, prefix + key, hold[key], 'user', unit='percent' if key == 'ratio' else case['currency'] if key == 'cost' else None)
    for flow, attrs in case['flows'].items():
        for key, value in attrs.items():
            write(doc, 'flow:' + flow + '.' + key, value, 'user')
    for key, value in case['event'].items():
        write(doc, 'event.' + key, value, 'user', unit=case['currency'] if isinstance(value, (int, float)) and key != 'years' else None)
    allowed = {f['field_name'] for f in catalog()}
    safe_bindings = {'payer_jurisdiction': r'[A-Z_]+\.loc', 'holding_percentage_pct': r'hold:[A-Z_]+>[A-Z_]+\.ratio',
                     'acquisition_date': r'hold:[A-Z_]+>[A-Z_]+\.since', 'dividend_amount': r'event\.dividend',
                     'receipt_date': r'event\.on', 'dividend_currency': r'case\.currency'}
    for field, address in bindings.items():
        if field not in allowed or field not in safe_bindings or not re.fullmatch(safe_bindings[field], address) or address not in records or field not in previous:
            raise ValueError('invalid or missing legacy binding')
        if previous[field]['value'] != records[address]['value'] and old_bindings.get(field) != address:
            raise ValueError('binding facts conflict; explicitly resolve values first')
        if address in doc['legacy_bindings'].values():
            raise ValueError('duplicate binding')
        doc['legacy_bindings'][field] = address
        records.pop('legacy.' + field, None)
    doc['domain_definition'] = definition
    sync(doc)


def project_case(doc):
    definition = doc.get('domain_definition')
    if not definition:
        return None
    records = doc['canonical_fact_records']
    def values(prefix):
        return {key[len(prefix):]: deepcopy(record['value']) for key, record in records.items()
                if key.startswith(prefix) and _usable(record)}
    case = {k: deepcopy(definition[k]) for k in ('template', 'currency', 'present', 'members', 'settled', 'closed', 'subject', 'notes')}
    case['currency'] = (records.get('case.currency') or {}).get('value')
    case['roles'] = {}
    for role, meta in definition['roles'].items():
        attrs = values(role + '.')
        loc = attrs.pop('loc', None)
        case['roles'][role] = {'loc': loc, 'type': meta['type'], 'attrs': attrs}
    case['holds'] = [{**edge, **{'ratio': None, 'since': None, 'cost': None},
                      **values(f"hold:{edge['holder']}>{edge['held']}.")}
                     for edge in definition['holds']]
    case['flows'] = {flow: values('flow:' + flow + '.') for flow in definition['flows']}
    case['event'] = values('event.')
    return case


def answers(doc):
    result = deepcopy(doc.get('domain_answers') or {'actions': {}, 'rulings': {}, 'library': {}})
    result['data'] = {key: record['value'] if record['status'] == 'unknown' else {'value': record['value'], 'source': record['origin']} for key, record in
                      doc['canonical_fact_records'].items() if not key.startswith(('legacy.', 'event.', 'case.'))
                      and not key.endswith('.loc') and record['status'] != 'deferred'}
    return result


def sync(doc):
    if doc.get('schema_version') != VERSION:
        return
    fields = {key[7:] for key in doc['canonical_fact_records'] if key.startswith('legacy.')} | set(doc['legacy_bindings'])
    facts = {}
    for field in fields:
        record = doc['canonical_fact_records'].get(doc['legacy_bindings'].get(field, 'legacy.' + field))
        if record:
            facts[field] = {k: deepcopy(record.get(k)) for k in ('value', 'origin', 'status', 'message_id', 'revision')}
    doc['facts'] = facts
    doc['domain_case'] = project_case(doc)
    if doc.get('domain_definition'):
        doc['domain_answers'] = answers(doc)


def confirm(doc):
    for record in doc['canonical_fact_records'].values():
        if _usable(record):
            record['confirmed_at'] = doc['revision'] + 1


def draft_from_legacy(doc):
    """Only mechanical quantities/dates; legal conclusions remain unmapped."""
    facts = {key: record['value'] for key, record in doc.get('facts', {}).items()}
    payer = facts.get('payer_jurisdiction')
    if payer not in ('CN', 'HK', 'SG') or facts.get('analysis_jurisdiction') != 'HK':
        return {'case': None, 'bindings': {}, 'gaps': ['需先明确付款方地区与香港收款方'], 'unmapped': list(facts)}
    case = {'template': 'holding', 'currency': facts.get('dividend_currency'),
            'roles': {'OP': {'loc': payer, 'attrs': {}}, 'ULT': {'loc': 'HK', 'attrs': {}}},
            'holds': [{'holder': 'ULT', 'held': 'OP', 'ratio': facts.get('holding_percentage_pct'), 'since': facts.get('acquisition_date')}],
            'flows': {'up1': {}}, 'event': {'dividend': facts.get('dividend_amount'), 'on': facts.get('receipt_date'),
                                          'as_at': facts.get('receipt_date')}, 'members': ['OP', 'ULT']}
    mapping = {'payer_jurisdiction': 'OP.loc', 'holding_percentage_pct': 'hold:ULT>OP.ratio',
               'acquisition_date': 'hold:ULT>OP.since', 'dividend_amount': 'event.dividend',
               'receipt_date': 'event.on', 'dividend_currency': 'case.currency'}
    bindings = {field: address for field, address in mapping.items() if facts.get(field) not in (None, 'unknown', 'conflict')}
    gaps = ['present：需明确确认现有结构变量（直接/间接持股等）'] + [field for field in ('dividend_amount', 'dividend_currency', 'receipt_date', 'holding_percentage_pct')
            if facts.get(field) in (None, 'unknown', 'conflict')]
    return {'case': case, 'bindings': bindings, 'gaps': gaps,
            'unmapped': [field for field in facts if field not in bindings], 'map_version': MAP_VERSION}
