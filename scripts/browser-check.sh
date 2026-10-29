#!/usr/bin/env bash
# Pass only public test configuration into ego's isolated JavaScript runtime.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
command -v ego-browser >/dev/null || { echo 'Install and configure ego-browser first.' >&2; exit 1; }
{
  python3 - "$ROOT" "${GL_WEB_PREVIEW_URL:-http://localhost:1313}" "${GL_WEB_TASK_SPACE:-}" <<'PY'
import json,sys
root,base,space=sys.argv[1:]
config={"root":root,"base":base,"spaceId":int(space) if space else None}
print('globalThis.GEOLEDGER_WEB_TEST = '+json.dumps(config)+';')
PY
  cat "$ROOT/integration/browser-smoke.mjs"
} | ego-browser nodejs
