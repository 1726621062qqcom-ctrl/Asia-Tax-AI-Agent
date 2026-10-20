# Applications

This directory contains application entry points that can run independently.

`api/main.py` provides the FastAPI application, health checks, and the built frontend. `api/chat.py` provides APIs for cases, messages, fact confirmation, and analysis. Orchestration and persistence live in `packages/chat/`, reusing the existing rule engine and model adapter.

The old web demo and its case analysis API remain on the `demo/hk-web` branch and have not been merged.

On the current `main` branch, [`web/`](web/README.md) is a bilingual Chinese and English tax chat workspace built with React, TypeScript, and Vite, connected to the APIs above. Incomplete model configuration produces an explicit error rather than a fixed substitute answer. See the [integrated setup and run guide](../docs/setup/README.md) and [acceptance testing entry point](../docs/verification/README.md) for complete operation and validation boundaries.
