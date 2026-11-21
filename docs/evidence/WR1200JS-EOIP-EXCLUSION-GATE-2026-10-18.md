# WR1200JS EoIP selected/excluded image gate — 2026-10-18

The WR1200JS profile keeps EoIP optional and currently disabled. The build
workflow now runs a fixture before compilation for both selected and excluded
cases. After assembly, an enabled profile uses the positive ROMFS verifier; a
disabled profile checks both requested and effective selectors and rejects
leftover EoIP page assets, the Administration / Services shortcut, worker files
or EoIP HTTP handler markers. Both paths produce the required
`eoip-image-checks.json` artifact.

Local validation passed:

- `python tools/eoip/check-image.py` — positive ROMFS fixture passes; missing
  HTTP markers, duplicate labels, enabled selector in an excluded image and a
  leaked optional page are rejected.
- `python -m py_compile tools/eoip/verify-excluded.py tools/eoip/check-image.py`
- `git diff --cached --check` — no whitespace errors in the staged patch.

These are host fixtures and workflow-source checks. Build #478 did not preserve
an EoIP report, so it does not establish EoIP image inclusion or exclusion. The
new workflow gate needs a later firmware CI run. EoIP Apply, autostart, tunnel
transfer and device behavior remain unverified; no router state was changed.
