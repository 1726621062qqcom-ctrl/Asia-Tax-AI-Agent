<a id="恢复知识库并连接引用"></a>

# Restore the Knowledge Database and Connect Citations

The user approved restoring the existing database/original texts, fixing ruling-date segmentation, connecting statutory and case retrieval, and regression testing existing cases. Retain PostgreSQL and the source manifest rather than rebuilding an unsourced knowledge collection.

1. Use Supabase-hosted PostgreSQL for knowledge and sessions. The user's explicit cloud requirement supersedes the earlier local database plan. Credentials remain only in the Git-ignored `.env`; running the application requires no local database installation.
2. Download the 10 currently in-scope sources again from approved official domains (1 of the 11 manifest entries is out of scope). Do not overwrite original snapshots. Retain hash drift status and do not change old manifest hashes merely because downloading succeeds.
3. Segment four rulings by numbered sections, preserving dates, applicable years, factual backgrounds, and ruling conclusion boundaries. They remain professionally unvalidated public rulings and are not sent to models or mixed into synthetic evaluation sets.
4. Retrieve provisions by rule locations; provide deterministic keyword search for cases/materials, including Chinese research keyword mappings and case identifiers. Do not claim completion of vector hybrid retrieval. Original records carry sources, locations, snapshot/text hashes, capture dates, and drift statuses.
5. Save the actual citations used by each analysis. The source sidebar supports original-text search, statutory/ruling passages, and official links. Show missing material and drift explicitly. Rebuilding indexes must not rewrite historical reports.
6. Validate preservation of dates/sections, identifier/keyword retrieval, actual database loading, regression of the existing 10 synthetic cases, and page citations. Backup recovery, production authentication, and expert validation require separate acceptance.

References: [official pgvector GitHub](https://github.com/pgvector/pgvector) (PostgreSQL License, PostgreSQL 13+ support; no code copied) and [official Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres). This round uses identifier/keyword retrieval; vector hybrid retrieval is separate work.
