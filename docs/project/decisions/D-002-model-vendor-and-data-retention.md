<a id="d-002-模型供应商与数据保留l0-阶段决策"></a>

# D-002 Model Provider and Data Retention (L0 Decision)

| Item | Details |
|---|---|
| Decision | Technical roadmap section 11, “Model provider and data retention terms” (original deadline 2026-08-31; completed after the deadline) |
| Decision date | 2026-09-03 |
| Status | L0 decisions partially resolved; written provider confirmation of retention terms pending |

<a id="决策内容"></a>

## Decision

1. **L0 integration**: use the provider-neutral OpenAI-compatible adapter (`packages/model_adapter`). Provider, model name, and key all come from environment variables (`.env`, ignored by Git); business code is not tied to any provider.
2. **Mandatory data boundary**: at L0, models may receive **fictional/synthetic data only** (fictional case descriptions and fact dictionary field names), matching the roadmap's interim default. No real client or pilot data may enter the model. Code enforces this through intake processing of synthetic fixtures and case descriptions explicitly labeled fictional. A separate decision is required before L1.
3. **Key management**: store keys only in `.env`, never in code, logs, commits, or reports. A key appeared in plaintext in a collaboration conversation on 2026-09-03; it was stored according to these rules, with a recommendation to rotate it promptly.
4. **Provider identity**: established by the project-supplied key (the endpoint is `FSIE_MODEL_BASE_URL` in `.env`). L1 data workflows remain frozen until the formal provider name and retention terms are recorded here.
5. **Output limits**: the model may produce only candidate facts (`ai_candidate`) and text drafts. Determinations remain with the deterministic rule engine and human review (PRD sections 3 and 5).

<a id="未决事项"></a>

## Open items

- Written confirmation of provider retention and training-use terms, required before L1.
- Model version pinning and change regression strategy, to be decided alongside prompt versioning.
