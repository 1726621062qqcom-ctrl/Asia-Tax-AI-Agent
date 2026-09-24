"""Run synthetic grounded extraction evaluation (no DB, no tax conclusions)."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from packages.intake.grounded import GroundedFacts, PROMPT_VERSION, extract_grounded
from packages.model_adapter.client import OpenAICompatibleClient

DEFAULT_SUITE = Path(__file__).resolve().parents[2] / 'tests/fsie/extraction_benchmark/cases.v1.json'


def semantic_key(observation):
    # Normalize Pydantic defaults. Evidence wording may differ while the fact is identical.
    payload = observation.model_dump(exclude={'evidence'})
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def compare(expected: GroundedFacts, actual: GroundedFacts, paragraphs: dict) -> dict:
    expected.check_evidence(paragraphs)
    actual.check_evidence(paragraphs)
    gold = Counter(semantic_key(o) for o in expected.observations)
    predicted = Counter(semantic_key(o) for o in actual.observations)
    matched = sum((gold & predicted).values())
    missing = list((gold - predicted).elements())
    extra = list((predicted - gold).elements())
    # Extra predictions need review; not every additional correct fact is a hallucination.
    return dict(expected_count=sum(gold.values()), predicted_count=sum(predicted.values()),
                matched=matched, missing=[json.loads(x) for x in missing],
                unexpected=[json.loads(x) for x in extra], exact_match=not missing and not extra)


def load_suite(path: Path) -> dict:
    suite = json.loads(path.read_text(encoding='utf-8'))
    seen = set()
    for case in suite['cases']:
        if case.get('synthetic') is not True:
            raise ValueError('benchmark contains non-synthetic case')
        if case['case_id'] in seen:
            raise ValueError('duplicate case ID')
        seen.add(case['case_id'])
        expected = GroundedFacts.model_validate(case['expected'])
        expected.check_evidence(case['paragraphs'])
    if not seen:
        raise ValueError('empty suite')
    return suite


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, default=DEFAULT_SUITE)
    parser.add_argument('--run-model', action='store_true', help='Send synthetic paragraphs to configured model')
    parser.add_argument('--output', type=Path, default=Path('reports/extraction-benchmark.json'))
    args = parser.parse_args(argv)
    suite = load_suite(args.suite)
    if not args.run_model:
        print(f"Validated {len(suite['cases'])} synthetic fixtures; no model called.")
        return 0
    client = OpenAICompatibleClient()
    results = []
    for case in suite['cases']:
        try:
            actual = extract_grounded(case['paragraphs'], synthetic=case['synthetic'], client=client)
            result = compare(GroundedFacts.model_validate(case['expected']), actual, case['paragraphs'])
            result['actual'] = actual.model_dump()
        except Exception as exc:
            # Do not persist provider response bodies or potential echoed credentials.
            result = {'exact_match': False, 'error_type': type(exc).__name__}
        results.append({'case_id': case['case_id'], **result})
    report = dict(suite_version=suite['version'], suite_sha256=hashlib.sha256(args.suite.read_bytes()).hexdigest(),
                  prompt_version=PROMPT_VERSION, model=client.config.model_name,
                  generated_at=datetime.now(timezone.utc).isoformat(),
                  exact_match_count=sum(r['exact_match'] for r in results),
                  case_count=len(results), results=results,
                  scope='Engineering extraction agreement, not tax accuracy or expert validation')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"{report['exact_match_count']}/{report['case_count']} exact matches; report: {args.output}")
    return 0 if all(r['exact_match'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
