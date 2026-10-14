# Hong Kong FSIE Candidate Knowledge Package

Public ruling Cases 68, 72, 74, and 75 were added on 2026-09-15, bringing the source catalog to 11 entries.
See [ruling_research_cards.json](ruling_research_cards.json) for research cards.
The [download and parsing validation record](../../../docs/project/2026-09-15-ruling-source-validation.md) documents
50 parsed output blocks and the issue where the old segmenter filtered out all four ruling dates. Public cases are not synthetic evaluation cases and were not sent to the model.
The seven-source record below describes the original historical baseline.

This is the first verifiable research package skeleton. It is not tax advice or a validated rule library.

Current status:

- Seven sources were validated through controlled capture on 2026-09-01 (HTTP 200). Metadata including `content_sha256` and byte counts has been populated, and `parse_status=captured`. Originals have not yet been segmented into legal units.
- The professional validation status of all sources and rule nodes remains `unverified`. They must be reviewed by Hong Kong tax experts before activation.
- All test cases are fictional and must not be replaced with client data.
- Rule nodes define only inputs, evidence, and stopping states; they do not produce exempt/taxable conclusions.
- Field names, evidence types, node keys, and status values must comply with the [`packages/contracts`](../../../packages/contracts/README.md) data contract.

Validation command:

```bash
python3 scripts/validate_fsie_package.py
```

Next steps: implement a controlled source pipeline, parse and segment originals into legal units, populate each rule's `source_unit_id`, complete the four missing nodes in the decision chain, and have experts confirm each rule and its evidence requirements.
