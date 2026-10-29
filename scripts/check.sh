#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
./scripts/build.sh
python3 -m unittest discover -s integration -p 'test_*.py'
python3 scripts/check_site.py public --base-url "${BASE_URL:-http://localhost:1313/}"
