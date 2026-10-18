# WR1200JS KMS process status — local evidence

Date: 2026-10-18
Status: implemented; exact-image CI gate pending.

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
- `tools/verify-discovery-status-image.py` on a synthetic ROMFS fixture using
  the actual `Advanced_Services_Content.asp` fetched from pinned source
  revision `c25283e`: PASS. The upstream page's row is `div_vlmcsd`; the
  fixture substitutes a stub `httpd`, so this is not a firmware image check.
- Python AST compilation and `git diff --check` on selected changed paths: PASS.
- Build #466 (`39123770675`, commit `ccafa5e`) failed before compilation in
  `Apply WR1200JS board port`: the source page uses `id="div_vlmcsd"`, while
  the first implementation expected `id="row_vlmcsd"`. The original log and
  repository source page confirmed this mismatch. The generator and fixture
  now use the actual `div_vlmcsd` anchor. This fix awaits the next build.
- Build #465 (`39122905943`, commit `1ec907d`) completed successfully. Its
  exact-image report identified BusyBox 1.24.2, checked all 57 discovered shell
  scripts, 150 applets/links and ELF dependencies, and passed every emitted
  check. Its report correctly kept `whole_service_audit_complete` and
  `runtime_verified` false. The exact report revealed the Shadowsocks selector
  mismatch now being corrected in the service map.

## Limits / next step

The process indicator does not prove that KMS requests are served or that
client activation succeeds. Run the new verifier against the final assembled
`trunk/romfs` in CI and retain the result. Device runtime acceptance is not
performed; the device stays on its previously confirmed firmware #396.
