#!/usr/bin/env bash
set -euo pipefail
npm --prefix apps/web ci --include=dev
npm --prefix apps/web run build
python -m pip install .
python scripts/install_tax_engine_release.py
