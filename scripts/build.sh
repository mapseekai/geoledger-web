#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/scripts/hugo.sh" --cleanDestinationDir --gc --minify --baseURL "${BASE_URL:-http://localhost:1313/}" "$@"
