#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-1313}"
exec "$ROOT/scripts/hugo.sh" server --bind 127.0.0.1 --port "$PORT" --baseURL "http://localhost:$PORT/" --renderToMemory --disableFastRender "$@"
