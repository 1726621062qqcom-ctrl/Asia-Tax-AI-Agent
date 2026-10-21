# Business catalogue data contract

Schema version: `1`. This is a derived catalogue over the existing `official/official.sqlite`; no SQL migration is performed by this package.

## Axes

```text
Jurisdiction ─┬─ Country/topic entry ── Topic / tax family
              ├─ Treaty pair ───────── Related jurisdictions
              └─ Taxing rule scope

Document ── Document/topic links ── Classification basis
    └─ Clause / cite_id ─┬─ Parameter ── Compiled rule
                        └─ Direct rule reference
```

A document has a source jurisdiction and separately related jurisdictions. A treaty pair, tax subject, income type, tax topic and document type are independent concepts. A document tag is a discovery facet; it does not classify every clause of a whole Act as the same tax topic.

Document `subject_focus=COMPANY` describes the current project's catalogue focus. `source_subject_ids` records only explicit title indications or recognised mixed-scope statutes, with `source_subject_status` reporting that limited basis; an empty list means not reviewed. These fields do not restrict the legal scope of the source. Topic entries identify their target subject separately.

## Files and keys

| File | Key | Content |
|---|---|---|
| `taxonomy.json` | topic / jurisdiction / subject `id` | Controlled vocabulary, topic families and status definitions |
| `profiles.json` | jurisdiction + topic | Editorial summaries, boundaries and selected existing parameter/rule IDs |
| `data/documents.csv` | `id` | Original document metadata, related countries, topic tags, classification state, version/work and source links |
| `data/document_topics.csv` | document + topic + basis + reference | Auditable multi-label classification; no move or rename of originals |
| `data/parameters.csv` | `param_id` | Original source scope, value, unit, income, quote, citation, dates and consuming rule/country IDs |
| `data/rules.json` | `rule_id` | Taxing jurisdiction, transaction scope, effect, grade, reads, discretion keys and source/parameter links |
| `data/citations.json` | `cite_id` | Clause label, source document, official URL, local original and original clause-time metadata |
| `data/dictionary.json` | `entry_id = country_id:topic_id` | 69 country/topic cards, five coverage states, text, caveats, source IDs and sample parameters |
| `data/coverage.csv` | country + topic | Coverage matrix with independent source / structured / model / judgement / completeness states and counts |
| `data/treaties.json` | `pair_id` | Three indexed pairs, instrument scope, documents, works, parameters and limitations |
| `data/inventory.json` | snapshot | Source counts, source retrieval date, build-input fingerprints, quotation and classification statistics |

CSV list fields are semicolon-delimited; JSON preserves arrays. These exports are not replacement source-of-truth tables. Future SQL tables can normalise lists into junction tables while retaining the same identifiers.

## Jurisdiction semantics

- `source_jurisdiction`: where the source was registered in the original manifest; `INTL` and `TREATY` remain valid source buckets.
- Document `country_ids`: jurisdictions explicitly related by source metadata or a recognised bilateral instrument identifier. This is not a finding of extraterritorial tax applicability.
- Parameter `scope`: the original single jurisdiction or pair, unchanged.
- Parameter `used_by_country_ids`: taxing jurisdictions of the compiled rules that consume the parameter. A shared parameter's legislative origin must not be silently relabelled.
- Rule `country_ids`: the jurisdiction whose tax the rule acts on, derived from its compiled taxing scope.
- Entry `document_ids`: documents tagged with that topic and related jurisdiction. Clause / parameter links remain the more precise evidence.

## Evidence and dates

`quote_verified=true` requires a non-empty quotation to occur verbatim in its cited archived clause after whitespace normalisation. A citation alone is not a verified quote. Missing quotation records are retained and flagged.

`source_linked` on a rule means it has a direct clause, parameter-clause or explicitly labelled practice-context link. `no_direct_clause_link` is reported as a review item. Grade `B_PRACTICE` remains separate from `A_TEXT`; its observation is not relabelled as legislation. `D_DISCRETION` does not mean the current taxpayer has obtained a ruling.

Original effective dates are preserved. A blank start date becomes `start_date_not_recorded`; a recorded interval does not prove worldwide legal currency. Download hash rechecks indicate byte consistency, not a substantive legal review.

The original corpus prunes superseded or repealed content. Removed-document metadata and supersession counts describe that limitation; this catalogue does not reconstruct missing historical law.

## Classification state

- `reference_linked`: at least one existing parameter, compiled rule or precedent issue links the document to a topic.
- `metadata_inferred`: document type, identifier, title keyword or parent context supplies the assignment.
- `needs_review`: no topic assignment was made. The document stays visible in the source catalogue and review queue.

None of these states means human approval of the entire document or legal completeness. Compound and mixed-scope sources can have several labels; topic and country counts must not be summed to count independent documents.

## Coverage and extension

Subject coverage currently distinguishes `COMPANY`, `INDIVIDUAL`, `PARTNERSHIP` and `TRUST`. Only company scenarios have a model scope; incidental collection of personal provisions is labelled separately.

No entry is labelled globally complete. `not_indexed` / `not_modelled` must not be rendered as `0%`, `exempt`, `abolished`, or `no treaty`. Such legal findings require their own sourced records.

Adding a jurisdiction requires its metadata, source selection, profile content, identifier/subject mappings and, separately, calculation rules. Adding a topic requires a stable taxonomy ID and auditable classification bases. Rebuild, check referential integrity and review classifications before exposing new cards to a frontend.
