# Verification record — 2026-10-29

Baseline: GeoLedger `5bf353c88cb017c8c00035fb86667dd2d7497b43`, OINK `v1.4.0`, Hugo Extended `0.168.0`.

## Executed

- Production static build passed; 50 generated HTML documents.
- Root deployment and `/geoledger/` subpath each passed 3,336 internal reference and anchor checks.
- All 10 integration contract tests passed.
- Ego browser matrix passed: 320, 390, 768 and 1440 CSS-pixel widths × Home, Docs index, quick start, SDK reference and Blog = 20 page scenarios. No observed horizontal overflow, recorded runtime error or HTTP resource error in these scenarios.
- All four Mermaid architecture diagrams rendered as actual SVGs.
- Chinese full-text search, light/dark switching, mobile navigation opening, console image loading and architecture SVG loading were checked interactively.
- The original GeoLedger checkout remained unchanged at the pinned SHA.

Machine-readable logs and captured previews are in the gitignored `artifacts/` directory. Re-run `./scripts/check.sh` and `./scripts/browser-check.sh` after changes. This is browser smoke coverage, not a claim of comprehensive accessibility, load, security or cross-browser certification.

## Asset boundaries

Four real pre-existing browser-test captures are used, unmodified: map alpha.6 (2026-10-22), workspace/history alpha.3 (2026-10-15), schema publication alpha.7 (2026-10-26). Captions and `data/screenshots.json` expose these versions. They are not described as newly captured screenshots of the current main branch.

A separately built latest-source demonstration console reached its initial-password screen. The required password-change operation was blocked by the tool safety check; it was not bypassed. Its temporary services and build caches were removed after validation; existing user services were left untouched.

## Remaining deployment work

Set an actual public `BASE_URL`, create/push the repository when authorized, and choose a static hosting destination. No remote repository, commit, push or public deployment was performed. The local preview binds only to `127.0.0.1:1313` on the development Mac.

OINK's upstream LibSass deprecation warning remains visible during a successful build. The website's own deprecated Hugo configuration and template calls were updated.

## Documentation revision verification, 2026-10-29

This entry records the documentation revision separately from the earlier site checks above.

- Reorganized 25 technical pages and 6 section indexes. All pre-existing content paths remain present; five new technical pages and one site-level content hook were added.
- `./scripts/check.sh` passed with 12 contract checks, 55 generated HTML documents and 4,528 resource/anchor references, with zero errors. The checks also parse JSON, compile Python examples and run `bash -n` on documented shell snippets without executing product commands.
- The `/geoledger/` deployment-prefix build passed the same HTML reference validation.
- The HTTP catalog matches all 32 public business operations at the pinned source. Configuration tables cover all 31 server environment bindings. All 45 distinct pinned source paths referenced by the technical pages exist in the corresponding Git objects.
- Ego-browser space 30 covered 40 page/width scenarios at 320, 390, 768 and 1440 pixels, with no observed page overflow, recorded runtime error or HTTP resource error. Four Mermaid diagrams rendered as SVGs.
- A visual review found compressed mobile table columns despite the overflow checks passing. After the cell-width fix, 12 targeted table checks passed; phone cells have at least 128 CSS pixels and retain OINK's local table scrolling.
- Chinese search found and opened the new publication-recovery guide. Light/dark switching, keyboard focus with a 3px outline, navigation at 390px, content with JavaScript disabled, and visible content with reduced motion passed. The task browser space was closed after completion.
- Five documentation skills were installed at the user level from pinned public sources. They do not add site dependencies. Their source commits and local hashes are recorded in `artifacts/docs-review/installed-skills.json`.

Evidence and before/after screenshots are under the ignored `artifacts/docs-review/` directory. `compare.html` contains the visual comparison and remaining homepage recommendations; `REPORT.json` contains detailed findings, scope and verification. The original source files were copied there before editing because the initial repository files were untracked.

Hallmark's static audit was used diagnostically. Its Puppeteer renderer was excluded by the explicit ego-browser-only project policy; no clean Hallmark verdict is claimed for the unchanged homepage. Its uppercase decoration labels, simulated screenshot title bar, small auxiliary text and repeated decoration remain documented recommendations.

GeoLedger startup, SDK network writes and database recovery were not executed during this revision. Operational pages explicitly mark source-checked procedures as awaiting isolated-environment validation. No GeoLedger source checkout, existing service, commit, push or public deployment was changed. The task preview uses loopback port 1327.
