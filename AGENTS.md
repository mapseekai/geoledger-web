# GeoLedger Web

- Independent Hugo documentation site for GeoLedger; OINK v1.4.0, Hugo Extended 0.168.0, Go 1.27.3. Use `./scripts/hugo.sh`; do not replace the theme with a React app.
- Home explains the product; Docs separates tutorials, how-to guides, references and architecture; Blog distinguishes published releases from main-branch notes.
- Product claims and examples must match `data/project.json` and the pinned GeoLedger source. Cite source paths in technical pages; no invented APIs, performance figures or integrations.
- Reuse GeoLedger branding: #fa520f marks, #cc3a05 accessible text/buttons, #0b1220 navigation, neutral slate surfaces. Keep keyboard focus, responsive layouts and reduced-motion behavior.
- Screenshots must come from a real isolated console with synthetic data. Keep credentials, databases, logs, binaries and caches out of Git. Record asset provenance in `data/screenshots.json`.
- Theme customizations live in site-level layouts/assets; never edit the downloaded theme. Do not enable panic-on-warning; review warnings, including the accepted upstream LibSass warning.
- Run `./scripts/check.sh`; integration tests belong in `integration/`. Never invoke a local coding agent. Do not modify the GeoLedger source checkout or its running services.
- AGENTS.md is the sole instruction file; CLAUDE.md is a relative symbolic link to it. Do not inject GitNexus rules. Commit/push only when explicitly requested.
