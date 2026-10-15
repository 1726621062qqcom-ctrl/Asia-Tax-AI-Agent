<a id="中国内地跨境股息官方来源目录设计"></a>

# Mainland China Cross-Border Dividend Official Source Catalog Design

The user confirmed mainland China as the next expansion. Following the PRD's `source-catalog baseline`, the initial focus is dividends paid by mainland companies to Hong Kong companies. Declare five research topics, each with at least one State Taxation Administration official source; record jurisdiction, language, publication/applicability dates, version notes, coverage gaps, and unverified status. Register the original arrangement and Fifth Protocol separately and explicitly list missing protocols as gaps.

Retain the `sources` table and SQLAlchemy. Add topic tags, dates, and notes through an incremental migration. Version the manifest in Git. The importer validates fields and official domains and writes idempotently to Supabase by `source_id`. Mainland records retain `l0_in_scope=false` and `parse_status=registered`. Hong Kong FSIE retrieval uses only its own manifest and does not read these unsegmented mainland catalog records. The CLI can search the catalog by declared topic.

Acceptance: official entry points exist for all declared topics; required metadata is complete; repeated imports add no rows; Hong Kong records remain unchanged and retrieval does not mix catalogs; cloud queries by `CN` work after migration. When the State Taxation Administration rejects local automated capture, retain null `http_status` and check links manually in the browser rather than pretending capture succeeded. Tax expert review, full-text segmentation, freshness monitoring, and formal mainland case answers belong to the next phase.
