# WR1200JS ZeroTier persistent-state hash guard — 2026-10-21

## Source finding

The ZeroTier lifecycle preparation computed per-file MD5 values in a shell
pipeline ending with `awk`. Without pipefail, a failed read or hash of a
durable file could be hidden by the successful last command. Startup or
membership synchronization could then compare incomplete hashes and proceed
without reliable evidence that a changed identity/network file was saved.
This is a source-level failure mode; it was not observed on the router.

## Change

`prepare-persistence-events.py` now captures per-file hashes before sorting
and returns failure if any file cannot be hashed. It checks the sort and
aggregate hash results too. The before-state hash must succeed before startup
or explicit membership synchronization. If the after-state hash fails, the
helper leaves a pending-save marker and blocks startup so a later attempt
retries persistence. The image verifier requires these guards in the shipped
ZeroTier lifecycle helper.

## Evidence and limits

- Python syntax parsing of the preparation script and image verifier passed.
- Git Bash `sh -n` accepted the extracted generated shell helper. Host-only
  probes using an existing local file passed for successful hashing, an
  injected per-file MD5 failure, and an injected aggregate MD5 failure. The
  probes replaced only the file list in memory and wrote no fixture files.
- Added `tools/check-zerotier-persistence-target.py` and wired it into the
  WR1200JS image workflow. It uses the shipped helper and exact ROMFS BusyBox
  under QEMU, with only explicit image applet providers. Synthetic cases cover
  unchanged and changed files, per-file/aggregate MD5 and sort failures,
  storage-save failure, and recovery using the pending marker. The report
  records hashes of the image BusyBox and lifecycle helper.
- Python parsing and host `sh -n` of the assembled QEMU fixture passed. Its
  expected source anchors were checked: one file list and one save call, four
  pending-marker references. These are preparation checks; the QEMU scenarios
  have **not** run locally.
- `git diff --check` for the ZeroTier files passed.
- The new QEMU/image gate has not run in CI. No generated lifecycle helper or
  target BusyBox was available in this checkout for local target execution;
  Git Bash host behavior does not prove target BusyBox behavior.
- Actual storage faults, daemon lifecycle, membership persistence and router
  reboot behavior remain unverified. No router state was changed.
