# Evidence-bearing extraction benchmark v1

This is an engineering extraction benchmark, not a tax gold set. It uses a new
research-only interface in `packages.intake.grounded`; the existing flat intake,
43-field dictionary and deterministic rules remain separate. No new tax decision
or automatic projection into the rule engine is introduced.

## Reviewed public references

`knowledge/hong_kong/fsie/reviewed_fact_annotations.json` preserves the 17 claims
reviewed with the user on 2026-09-21. Each has a paragraph locator, source ID,
manifest hash, review status and structured candidate transcription. The latter
is an engineering transcription, not an additional user approval. References are
locators, not claimed verbatim quotations; no current webpage hash verification
is implied. The review was assisted and not exhaustive or expert validation.
Public cases remain `synthetic=false`, `model_input_authorized=false`.
Ruling dates/assessment years are metadata only, never transaction dates.

## New research contract

An observation contains predicate, subject, optional object, value, disclosure
status, event ID, asset, date precision, modality and exact paragraph evidence.
Enterprise income tax and dividend withholding have distinct predicates. Dates
retain year/month/day precision. Share distributions preserve sender, recipient,
share issuer, event order and same-day relationships. Missing values are null
with `not_disclosed` only if explicitly described as missing. Otherwise omit.
Evidence spans must literally occur in the input paragraph. This check cannot
prove that a quote entails a fact; semantic evaluation and review remain needed.

The versioned machine-readable contract is
`packages/contracts/json_schemas/grounded_extraction.v1.schema.json`, generated
from `GroundedFacts.model_json_schema()` and checked against code by a test.

## Frozen synthetic fixtures

`cases.v1.json` is v0.1.0, a frozen **engineering** expectation set. Its 12 authored
cases cover rate changes/swaps/absence, renamed entities and reversed holdings,
year precision, in-kind transfers, reversed transfer direction, paragraph order,
planned versus completed events, and undisclosed amounts/accounts. They do not
contain the original ruling text or tax outcomes. This is a small regression
suite, not a representative performance estimate. Change version when changing
inputs or expectations; retain old run reports and suite hashes.

Validate without any model or database:

```sh
make extraction-check
```

With a configured existing model adapter, run the synthetic model evaluation:

```sh
make extraction-eval
```

Only labelled input paragraphs and the extraction schema enter the model prompt;
expected answers stay local. Results in ignored `reports/` contain model name,
prompt version, suite hash, denominator, per-case outputs, missing/unexpected
observations and exact-match counts. Unexpected observations are candidates for
review, not automatically counted as hallucinations. Schema/transport failures
count as failed cases and retain sanitized exception types. Evidence is validated
before scoring. Matching requires subject, object, value, event/asset, date
precision and modality to agree; quote wording may differ if it is an input span.
A nonzero exit means at least one case failed. There is no retry-until-pass.

No real model score is claimed by offline tests. Model evaluation does not write
to the database, change professional validation states, or emit tax conclusions.
