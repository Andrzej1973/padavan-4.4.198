# WR1200JS Privoxy Apply persistence feedback — 2026-10-21

## Source finding

`overlay/padavan-4.4/ports/privoxy/register-file-routing.py` writes Privoxy
editor files to `/etc/storage/privoxy` and runs `mtd_storage.sh save` after a
file changes. Before this correction, a failed save only produced a log entry.
The native Apply handler could still send `done_committing()`, so the browser
could imply durable success even though the storage save failed. This was
found by reading source; no failed save was observed on the physical router.

## Local correction

- The generated handler records a failed save and intercepts the Apply response
  before `done_committing()`.
- It clears both pending restart-event banks, returns without a success
  callback, and calls the Privoxy page's failure handler. The page retains the
  editor contents for retry and offers EN/UK/RU messages.
- The message explicitly says files may already have changed in RAM. No
  transaction rollback is claimed.
- The Privoxy final-image verifier checks the page callback, translation keys,
  HTTPD callback string and generated source branch ordering.

## Checks performed

1. Ran the production-order source transformations in memory against the local
   Padavan `web_ex.c`/`common.h` fixture: extended event bank, Privoxy editor
   routing, then incomplete-POST protection. Each transform completed and the
   failure marker preceded the success callback.
2. Parsed the modified Python scripts as Python source; passed.
3. `git diff --check` for the Privoxy files passed.

These original checks covered source transformation and static ordering only.
Target compilation, an injected storage-save failure in an authenticated
browser, actual restart behavior and reboot persistence remain open. The
router was not changed.

## Build #512 follow-up — 2026-10-21

Firmware run [#512](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39624109819)
completed compilation and passed the corrected Stubby/dnsmasq QEMU test, then
failed the Privoxy `save_failure_apply_order` image assertion. The uploaded
`privoxy-image-checks` JSON reports that single Privoxy check false; the other
reported Privoxy image checks passed. The incomplete build set prevented a
verified download artifact.

The checker now records individual Apply/save-order predicates in the report
(`apply_call_found`, branch order, failure marker, page callback, both pending
restart clears, and abort return) so the next image run identifies which exact
predicate disagrees with the prepared source. A local production-order
transformation reproduction against the available HTTPD source fixture passed
all eight predicates. This does not reproduce the exact CI prepared tree and
does not explain the CI failure. Preserve the strict gate; inspect its
component diagnostics from the next run before changing expected behavior.

No router state changed. Authenticated browser fault injection and persistence
remain unverified.
