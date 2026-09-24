"""Meaningful failure cases for evidence, entity direction, dates and data policy."""
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.intake.benchmark import DEFAULT_SUITE, compare, load_suite
from packages.intake.grounded import GroundedFacts, extract_grounded


def first_case():
    return load_suite(DEFAULT_SUITE)['cases'][0]


class Stub:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat_json(self, system, user, **kwargs):
        self.calls.append((system, user))
        return self.response


def test_public_rulings_rejected_before_model_call():
    client = Stub({})
    with pytest.raises(ValueError, match='synthetic'):
        extract_grounded({'2(a)': 'Public source'}, synthetic=False, client=client)
    assert client.calls == []


def test_exact_quotes_and_structured_result():
    case = first_case()
    client = Stub(case['expected'])
    result = extract_grounded(case['paragraphs'], synthetic=True, client=client)
    assert len(result.observations) == 2
    assert 'expected' not in client.calls[0][1]


@pytest.mark.parametrize('mode', ['quote', 'paragraph'])
def test_fabricated_evidence_rejected(mode):
    case = first_case()
    answer = copy.deepcopy(case['expected'])
    answer['observations'][0]['evidence'][0][mode] = 'fabricated'
    with pytest.raises(ValueError):
        extract_grounded(case['paragraphs'], synthetic=True, client=Stub(answer))


@pytest.mark.parametrize('value', [True, -1, 101, float('nan'), float('inf'), '25'])
def test_invalid_rate_rejected(value):
    answer = first_case()['expected']
    answer['observations'][0]['value'] = value
    with pytest.raises(ValidationError):
        GroundedFacts.model_validate(answer)


def test_year_precision_does_not_allow_invented_day():
    case = next(c for c in load_suite(DEFAULT_SUITE)['cases'] if c['case_id']=='SYN-HOLD-01')
    answer = copy.deepcopy(case['expected'])
    answer['observations'][1]['value'] = '2001-01-01'
    with pytest.raises(ValidationError):
        GroundedFacts.model_validate(answer)


@pytest.mark.parametrize('mutation', ['swap_rates', 'drop', 'duplicate'])
def test_scoring_detects_wrong_missing_and_extra_facts(mutation):
    case = first_case()
    expected = GroundedFacts.model_validate(case['expected'])
    actual = expected.model_copy(deep=True)
    if mutation == 'swap_rates':
        actual.observations[0].value, actual.observations[1].value = 8, 23
    elif mutation == 'drop':
        actual.observations.pop()
    else:
        actual.observations.append(actual.observations[0].model_copy(deep=True))
    result = compare(expected, actual, case['paragraphs'])
    assert not result['exact_match']
    assert result['missing'] or result['unexpected']


def test_reversed_event_direction_is_not_a_match():
    case = next(c for c in load_suite(DEFAULT_SUITE)['cases'] if c['case_id']=='SYN-EVENT-01')
    expected = GroundedFacts.model_validate(case['expected'])
    actual = expected.model_copy(deep=True)
    event = actual.observations[0]
    event.subject, event.object = event.object, event.subject
    assert not compare(expected, actual, case['paragraphs'])['exact_match']


def test_all_frozen_fixtures_validate_without_network():
    suite = load_suite(DEFAULT_SUITE)
    assert len(suite['cases']) == 12
    for case in suite['cases']:
        expected = GroundedFacts.model_validate(case['expected'])
        assert compare(expected, expected, case['paragraphs'])['exact_match']


def test_reviewed_annotations_preserve_boundaries_and_provenance():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root/'knowledge/hong_kong/fsie/reviewed_fact_annotations.json').read_text())
    manifest = json.loads((root/'knowledge/hong_kong/fsie/source_manifest.json').read_text())
    sources = {s['source_id']:s for s in manifest['sources']}
    assert [len(c['annotations']) for c in data['cases']] == [8,9]
    for case in data['cases']:
        assert case['synthetic'] is False
        assert case['model_input_authorized'] is False
        assert case['professional_validation_status'] == 'unverified'
        for annotation in case['annotations']:
            source = sources[annotation['evidence']['source_id']]
            assert source['content_sha256'] == case['source_manifest_sha256']
            assert annotation['review_status'] == 'user_assisted_confirmed'
            assert annotation['structured_candidate']


def test_grounded_schema_matches_versioned_contract():
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root/'packages/contracts/json_schemas/grounded_extraction.v1.schema.json').read_text())
    assert schema == GroundedFacts.model_json_schema()


def test_missing_value_cannot_claim_a_number():
    case = next(c for c in load_suite(DEFAULT_SUITE)['cases'] if c['case_id']=='SYN-MISSING-01')
    answer = copy.deepcopy(case['expected'])
    answer['observations'][0]['value'] = 100
    with pytest.raises(ValidationError):
        GroundedFacts.model_validate(answer)


def test_suite_rejects_public_inputs(tmp_path):
    suite = load_suite(DEFAULT_SUITE)
    suite['cases'][0]['synthetic'] = False
    path = tmp_path/'suite.json'
    path.write_text(json.dumps(suite))
    with pytest.raises(ValueError, match='non-synthetic'):
        load_suite(path)


def test_model_evaluation_counts_errors_and_preserves_run_metadata(tmp_path, monkeypatch):
    from packages.intake import benchmark
    class FakeClient:
        class config:
            model_name = 'offline-stub'
    monkeypatch.setattr(benchmark, 'OpenAICompatibleClient', FakeClient)
    calls = []
    def fail(paragraphs, *, synthetic, client):
        assert synthetic is True
        calls.append(paragraphs)
        raise ValueError('private provider response must not be persisted')
    monkeypatch.setattr(benchmark, 'extract_grounded', fail)
    output = tmp_path/'report.json'
    assert benchmark.main(['--run-model', '--output', str(output)]) == 1
    report = json.loads(output.read_text())
    assert report['case_count'] == len(calls) == 12
    assert report['exact_match_count'] == 0
    assert len(report['suite_sha256']) == 64
    assert report['model'] == 'offline-stub'
    assert 'private provider' not in output.read_text()
    assert all(r['error_type'] == 'ValueError' for r in report['results'])
