#!/usr/bin/env bash
set -euo pipefail
npm --prefix apps/web ci --include=dev
npm --prefix apps/web run build
python -m pip install .
# Server OCR needs no desktop/OpenGL libraries. Replace the GUI OpenCV
# dependency pulled in by RapidOCR with its headless equivalent on Linux.
if [[ "$(uname -s)" == "Linux" ]]; then
  python -m pip uninstall -y opencv-python
  python -m pip install --force-reinstall --no-deps opencv-python-headless==4.11.0.86
fi
python scripts/install_tax_engine_release.py
# Legacy Word (.doc) reader, installed without root. Modern Office files use Python.
if [[ "$(uname -s)" == "Linux" ]] && ! command -v antiword >/dev/null; then
  mkdir -p .tools
  attachment_build_dir=$(mktemp -d)
  (cd "$attachment_build_dir" && apt-get download antiword)
  for attachment_package in "$attachment_build_dir"/antiword*.deb; do
    dpkg-deb -x "$attachment_package" .tools
  done
  rm -rf "$attachment_build_dir"
fi
