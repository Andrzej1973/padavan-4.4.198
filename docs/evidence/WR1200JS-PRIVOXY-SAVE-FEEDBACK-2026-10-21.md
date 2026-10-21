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

These checks cover source transformation and static ordering only. The new
final-image gate has not run in CI. Target compilation, an injected storage-save
failure in an authenticated browser, actual restart behavior and reboot
persistence remain open. The router was not changed and no firmware build ran.
