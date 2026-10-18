# WR1200JS KMS process status — local evidence

Date: 2026-10-18
Status: implemented locally; exact-image CI gate pending.

## Change

Administration → Services now appends a status row to the existing `vlmcsd`
enable setting. The observer compares `vlmcsd_enable` with the presence of the
`vlmcsd` process and `/usr/bin/vlmcsd`. It reports disabled, running, enabled
but missing, unknown, or disabled but still running. EN/UK/RU labels state
explicitly that KMS client requests and activation results are not tested.

The page includes manual refresh and 30-second visible-page polling, an AJAX
timeout, and expiry of observations after 45 seconds. When the state becomes
unknown or expires, the displayed observation time is cleared.

## Local checks

- `tools/check-discovery-status.py`: PASS; emitted page, Node refresh/expiry
  fixture, and host C handler fixture for LLTD, ASUS Info Discovery, KMS and
  watchdog states.
- `tools/verify-discovery-status-image.py` on a synthetic ROMFS fixture: PASS.
  This checks marker wiring only; the fixture is not a firmware image.
- Python AST compilation and `git diff --check` on selected changed paths: PASS.
- WR1200JS build #463 (`39121882639`) remains the latest confirmed full build.
  Builds #464 (`39122749780`) and #465 (`39122905943`) were in progress when
  this local check was recorded. Neither includes this change.

## Limits / next step

The process indicator does not prove that KMS requests are served or that
client activation succeeds. Run the new verifier against the final assembled
`trunk/romfs` in CI and retain the result. Device runtime acceptance is not
performed; the device stays on its previously confirmed firmware #396.
