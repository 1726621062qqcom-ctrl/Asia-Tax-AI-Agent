"""The test system (测试系统.md): automatic checks whose results the UI shows and that run before anything reaches an expert.

    python -m tax_graph.verify --tier fast|mid|full     runner (§5): every check of a tier, rows in the unified format
                                                        (results.py) to out/verify/<run_id>.jsonl, index in out/verify/index.json
    python -m tax_graph.verify --tier mid --baseline    accept the current results as the baseline later runs are attributed to

Modules: results (format, version fingerprint, run index), registry (the checks by layer and tier), fp (fingerprints
under controlled order / hash seed / cache; the baseline store), stability (instability check, layer C), attribution
(attribution, delta debugging over the files changed since the baseline, layer C), grounding + check_grounding (grounding
check), casecheck and sweep (comparison against real cases, 测试系统.md §8b)."""
