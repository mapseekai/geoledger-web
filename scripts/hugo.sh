#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/.tools/hugo" ]]; then HUGO="$ROOT/.tools/hugo"; else HUGO="$(command -v hugo || true)"; fi
if [[ -z "$HUGO" ]]; then echo 'Install Hugo Extended 0.168.0; see README.md.' >&2; exit 1; fi
VERSION="$($HUGO version)"
if [[ "$VERSION" != *"v0.168.0"* || "$VERSION" != *"+extended"* ]]; then
  printf 'Expected Hugo Extended 0.168.0; found: %s\n' "$VERSION" >&2; exit 1
fi
exec "$HUGO" "$@"
