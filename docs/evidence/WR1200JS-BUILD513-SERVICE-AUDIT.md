# WR1200JS firmware build #513 — service audit — 2026-10-21

## Workflow result

GitHub Actions run [#513](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39632923432)
used branch `codex/wr1200js-service-webui` at source commit
`8ff6016947bcb19363a7f0ddbc502a217432868b`. The `Build WR1200JS firmware`
step completed successfully. The job then failed at
`Verify Privoxy image packaging and ELF dependencies`; the selected-image
download job failed, so this run did not produce a verified downloadable
firmware image. This is compile success, not final-image acceptance or
physical-router acceptance.

The DNS listener-conflict and Stubby combined-config checks under QEMU passed
before the Privoxy gate. The remaining Privoxy checks in the uploaded
`privoxy-image-checks` artifact passed except `save_failure_apply_order`.
Artifact ID `12360573046`, SHA-256
`9e912f1165534dc204db31acd258450f671a15200be04402a392d22489ef08e9`.
Its component report was:

| Predicate | Result |
|---|---|
| `apply_call_found` | false |
| `failure_branch_after_apply` | false |
| `success_response_after_failure` | true |
| `failure_flag_set` | true |
| `failure_callback_in_branch` | true |
| `legacy_restart_cleared` | true |
| `extended_restart_cleared` | true |
| `apply_aborted` | true |

## Diagnosis and local correction

The gate searched for the pre-shared-Wi-Fi spelling
`result = validate_asp_apply(wp, sid);`. The production source pipeline later
runs `tools/prepare-shared-wifi.py`, which adds the shared adapter argument to
that call (`&shared`). The failure handler and abort remained present; the
gate did not recognize the transformed Apply call and reported a false
failure.

`overlay/padavan-4.4/ports/privoxy/verify-image.py` now recognizes both the
two-argument and shared-adapter call forms, extracts the Save/Apply response
block including its nested failure branch, and still requires the failure
handler to follow the apply call and precede `done_committing()`. The failure
branch must continue to set the page error callback, clear both pending restart
banks, and abort the response. The check has not been loosened to accept a
missing handler.

An in-memory fixture using the transformed `&shared` spelling passed all
seven current order/abort predicates, and the verifier parsed as Python. This
is a checker fixture only; the updated checker has not yet run against a new
compiled ROMFS. Build #513 predates the correction and the CPU-watchdog board
change. No firmware was flashed and no router setting or process was changed.

## Exact pinned-source parser check — 2026-10-21 16:59 UTC

Fetched the pinned base [`web_ex.c`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/httpd/web_ex.c)
at `c25283e915a2a00a763774dd255b14aff997285e` and confirmed the exact
Save/Apply source template matched the Privoxy response transform. In memory,
applied that response replacement and the shared-Wi-Fi `&shared` Apply-call
rewrite to the pinned source. The current image verifier then found the outer
response block and call and passed checks for failure ordering, callback,
both restart-bank clears, abort, and success ordering. No checkout files were
created for this fixture. This supports the verifier correction against the
pinned handler shape; it still does not substitute for a fresh full prepared
source/ROMFS workflow.

## Remaining work

The isolated verifier correction was committed as `a6edff8` and pushed to
`codex/wr1200js-service-webui` on 2026-10-21. The remote branch was checked
at `8ff6016` before the push and advanced to `a6edff8`. Python AST parsing
and staged whitespace checks passed. A new Actions image result is still
required; the successful push alone does not prove that the Privoxy gate or
the complete firmware build passes.

- Run the corrected verifier in a later WR1200JS image workflow and inspect
  its uploaded diagnostics.
- Complete remaining enabled-service image and exact BusyBox checks for item 4.
- Keep physical-router service behavior and restart/persistence checks open;
  the latest successful device snapshot remains the read-only check at
  2026-10-21 16:18 UTC.
