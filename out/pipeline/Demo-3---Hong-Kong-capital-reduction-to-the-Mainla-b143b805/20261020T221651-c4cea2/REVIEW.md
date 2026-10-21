# To-do: Demo 3 - Hong Kong capital reduction to the Mainland (run 20261020T221651-c4cea2)

Extraction done; the items below are for a person to settle. Write the answers into `review.json` in this directory: `{"data": {"<path>": {"value": ..., "source": "...", "quote": "..."} | "unknown"}, "notes": [...]}`, then rerun `python -m tax_graph.pipeline C:/Coding/Projects/TUM/project_study_self/cases/private/Demo-3---Hong-Kong-capital-reduction-to-the-Mainla-b143b805.json --run-id 20261020T221651-c4cea2 --from review`. Unanswered items are computed as missing, never filled in.

## from a register / an official document (1)

- `flows.payment_1.assessment_notice_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书

## free text (2)

- `roles.JINHAI_INDUSTRIAL_CO_LTD.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.JINHAI_ASIA_LIMITED.attrs.ucmt_location`: free text the program cannot check; a person fills it in

## register unmatched (2)

- `roles.JINHAI_INDUSTRIAL_CO_LTD`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
- `roles.JINHAI_ASIA_LIMITED`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
