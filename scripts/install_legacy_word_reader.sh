#!/usr/bin/env bash
# Render has no usable apt package index. Fetch a pinned Debian package directly,
# verify it, and unpack locally without root or modifying the system packages.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -s)" != "Linux" ]]; then
  exit 0
fi
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo 'The bundled legacy Word reader requires Linux x86_64.' >&2
  exit 1
fi
attachment_build_dir=$(mktemp -d)
trap 'rm -rf "$attachment_build_dir"' EXIT
curl --fail --location --retry 3 --connect-timeout 15 --max-time 120 \
  https://deb.debian.org/debian/pool/main/a/antiword/antiword_0.37-16_amd64.deb \
  --output "$attachment_build_dir/antiword.deb"
printf '%s  %s\n' \
  f26b6a843c0d42aa760f45e74e5abd5f9b7cb431803d19c51b6351777c95d12b \
  "$attachment_build_dir/antiword.deb" | sha256sum --check -
mkdir -p .tools
dpkg-deb -x "$attachment_build_dir/antiword.deb" .tools
# Check the actual binary and UTF-8 mapping before declaring the build ready.
ANTIWORDHOME="$PWD/.tools/usr/share/antiword" \
  .tools/usr/bin/antiword -m UTF-8.txt tests/chat/fixtures/attachment.doc \
  > "$attachment_build_dir/word.txt"
grep -q 'CNY 2000000' "$attachment_build_dir/word.txt"
echo 'Legacy Word reader installed and verified.'
