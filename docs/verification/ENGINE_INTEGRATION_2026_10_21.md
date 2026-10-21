# Engine integration candidate — 2026-10-21

This is an integration candidate, not a production acceptance record.

## Inputs

- Source: `c5d6a1d4fb23c2ee57dbc0afee108e834569ecc5`.
- Official data: `9720c08d55f7b7a3a8f35688e21f342e6ddf7f59`. The latest source snapshot omits this directory. This older data combination passes upstream compilation/self-checks, but is not claimed to be the author's intended release pair.
- SQLite SHA-256: `e9f2ccee521a330b8f9dcb1fe2138d559a71b45ae4824324504422efb518e798` (matches historical LFS pointer).
- Selected source/data SHA-256: `3c80dd92b0da3155653ee59bbe8ba569fc14ddd1c330f08fc14550784f70efcc`.
- Downloads are independently pinned; secrets, private cases, generated outputs and upstream UI are excluded.

## Integration

Existing React UI, authentication and deployment layout are retained. Worker understands English and Chinese answer-type descriptions. Reviewed field labels are kept in separate languages. Test fixtures are now owned by this repository, not dependent on upstream examples remaining present.

Planner explicitly uses `scope='all'` to preserve the existing product's modelled transaction coverage. Upstream's new income-only product policy is not silently adopted. This is an integration policy choice, not an assertion of legal completeness.

The prerequisite audit preceding this integration is preserved in a separate checkpoint commit. Unknown new fields fail closed as `needs_policy_review`; they cannot be selected as automatic questions. Conditional strategy trees are preserved in blocked results rather than flattened into a single definite conclusion.

## Validation

- Python suite: 611 passed, 11 live-database tests skipped.
- New adapter tests: 9 passed.
- TypeScript and Vite production builds: passed.
- Browser suite: 40 passed initially; remaining test asserted the old release hash. Updated the expected release and reran the structure suite.
- Upstream `tax_graph.check_engine`: exit 0.
- Local installer copies, verifies and atomically installs this release successfully.

No production credentials were used by these tests. They do not establish live model or production database acceptance.

## Remaining production gates

- 59 upstream glossary fields are absent from the reviewed interview catalogue. Review their prerequisites, translations and cross-flow isolation before enabling them. Existing rules may request these fields; cases can therefore require manual review instead of continuing automatically.
- The current UI does not yet render upstream conditional strategy trees/workpacks; such results are explicitly blocked.
- Verify the intended official data version with the upstream owner; do not assume historical data is fully current merely because compilation succeeds.
- Complete end-to-end synthetic acceptance across supported scenarios before promoting this candidate to main/Render.
