"""Offline consultation behavior check; deliberately makes no model calls."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from packages.consultation.service import ConsultationService


def main():
    service=ConsultationService()
    cases=json.loads((ROOT/'tests/consultation/scenarios.json').read_text())['scenarios']
    failures=[]
    for case in cases:
        facts=[];history=[]
        for turn,message in enumerate(case['messages'],1):
            answer=service.reply(message,facts,history,turn,synthetic_acknowledged=True)
            facts=answer.facts;history.append(message)
        topics={service.knowledge.by_id[c.id]['topic'] for c in answer.citations}
        passed=(answer.intent==case['intent'] and set(case['required_topics'])<=topics
                and bool(answer.questions)==case['questions'] and answer.research_only)
        print(('PASS' if passed else 'FAIL')+' '+case['id'])
        if not passed:failures.append(case['id'])
    print(f'{len(cases)-len(failures)}/{len(cases)} offline behavior scenarios passed; no model quality score.')
    return bool(failures)


if __name__=='__main__': raise SystemExit(main())
