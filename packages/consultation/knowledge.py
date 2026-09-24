"""Deterministic multilingual lexical retrieval over versioned official passages."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from collections import Counter
from urllib.parse import urlparse

from packages.consultation.schemas import Citation

CORPUS_PATH = Path(__file__).resolve().parents[2] / 'knowledge/hong_kong/fsie/chat_corpus.json'


def tokens(text: str) -> list[str]:
    text = text.lower()
    english = re.findall(r'[a-z0-9]+(?:\.[0-9a-z]+)?', text)
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    return english + [part[i:i+2] for part in chinese for i in range(max(1, len(part)-1))]


class KnowledgeBase:
    def __init__(self, path: Path = CORPUS_PATH):
        self.data = json.loads(path.read_text(encoding='utf-8'))
        self.units = self.data['units']
        self.by_id = {u['id']:u for u in self.units}
        if len(self.by_id) != len(self.units):
            raise ValueError('duplicate knowledge IDs')
        for unit in self.units:
            if hashlib.sha256(unit['text'].encode()).hexdigest() != unit['text_sha256']:
                raise ValueError('knowledge text hash mismatch')
            for url in (unit['url'], unit['statute_url']):
                parsed = urlparse(url)
                if parsed.scheme != 'https' or parsed.netloc not in ('www.ird.gov.hk', 'www.elegislation.gov.hk'):
                    raise ValueError('non-official citation URL')
            if unit['source_type'] not in ('official_guidance','primary_legislation'):
                raise ValueError('only curated general guidance and legislation can enter model context')
        self.docs = [Counter(tokens(' '.join([u['title'], ' '.join(u['tags']), u['research_note_zh'], u['text']]))) for u in self.units]
        self.df = Counter(token for doc in self.docs for token in doc)

    def search(self, query: str, *, intent: str, limit: int = 8) -> list[dict]:
        query_tokens = set(tokens(query))
        required = []
        if intent == 'planning':
            required = ['exceptions','substance','participation','credit','advance']
        elif intent in ('case','correction'):
            required = ['scope','receipt','timing']
            if re.search(r'持股|持有|holding|[％%]',query,re.I):
                required.append('participation')
        elif intent == 'law' and re.search(r'有哪些规定|哪些豁免|有哪些条件|overview|FSIE.*规定',query,re.I):
            required = ['scope','exceptions','receipt','substance','participation','timing']
        for section,topic in [('15H','scope'),('15I','timing'),('15K','substance'),('15M','participation'),('15N','participation')]:
            if section.lower() in query.lower() and topic not in required:
                required.insert(0,topic)
        scored = []
        for unit, doc in zip(self.units, self.docs):
            score = sum((1 + math.log(doc[t])) * math.log(1+len(self.units)/self.df[t])
                        for t in query_tokens if t in doc)
            score += sum(7 for tag in unit['tags'] if tag.lower() in query.lower())
            # Explicitly documented topic boosts keep essential context with short follow-ups.
            if intent in ('case','correction') and unit['topic'] in ('scope','receipt','timing'):
                score += 8
            if intent == 'planning' and unit['topic'] in ('exceptions','substance','participation','credit','advance'):
                score += 14
            if intent == 'law' and unit['topic'] in ('scope','exceptions'):
                score += 5
            if score > 0:
                scored.append((score,unit['id'],unit))
        ranked = [item[2] for item in sorted(scored, key=lambda x:(-x[0],x[1]))]
        pinned = [next(u for u in self.units if u['topic']==topic) for topic in required]
        law_mentions = re.findall(r'15[H-S]',query,re.I)
        law_ids = ['cap112-'+m.upper() for m in law_mentions]
        if 'cap112-15M' in law_ids:
            law_ids.append('cap112-15N')
        primary = [self.by_id[id] for id in dict.fromkeys(law_ids) if id in self.by_id]
        chosen = primary + [u for u in pinned if u not in primary]
        return (chosen + [u for u in ranked if u not in chosen])[:limit]

    def citation(self, unit: dict) -> Citation:
        return Citation(id=unit['id'], source_id=unit['source_id'], title=unit['title'],
            url=unit['url'], source_type=unit['source_type'], locator=unit['locator'],
            excerpt=unit['text'], text_sha256=unit['text_sha256'],
            retrieved_at=unit.get('source_retrieved_at',self.data['retrieved_at']), professional_validation_status='unverified',
            statute_reference=unit['statute_reference'], statute_url=unit['statute_url'])
