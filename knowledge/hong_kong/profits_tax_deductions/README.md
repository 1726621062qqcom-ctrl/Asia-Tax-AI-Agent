# Hong Kong profits tax: ordinary business expense deductions

This package indexes official material for an initial expense-deductibility research flow. It covers the general section 16 production-of-profits test, the section 17 exclusions, and IRD guidance on common accounting adjustments. It does not make a final determination for an individual expense. Interest, capital allowances, research and development concessions, and special deductions require separate treatment.

The cloud database currently holds three sources and 392 legal units: 43 statutory units, 125 profits-tax guidance blocks, and 224 BIR51 instruction blocks. The statutory XML snapshot is the 22 May 2026 version; the IRD web pages were captured on 13 October 2026. The package therefore uses **22 May 2026 as its conservative legal coverage cutoff**. A later tax year or rule change needs a new verified statutory snapshot.

Build into the configured cloud PostgreSQL database with:

```sh
python -m packages.knowledge_pipeline.cli --manifest knowledge/hong_kong/profits_tax_deductions/source_manifest.json
```

Source snapshots are kept locally under `raw/` and are ignored by Git. The database stores source URLs, snapshot hashes, and citable legal units. Re-running the build reuses a local snapshot; upstream changes must be captured as a new snapshot and reviewed before updating the pinned hashes.

The chat and source search use an isolated expense route with source and quote validation. This first slice does **not** include a deterministic deductibility rule engine or the FSIE case-confirmation/report workflow. It is unverified pending professional review. Do not treat a user's expense label as proof of deductibility; ask for business purpose, assessment year, private use, capital nature, and records.
