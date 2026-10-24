# WR1200JS USB/IP settings durability uncertainty — 2026-10-19

`tools/usbip/export-store.h` now routes the directory synchronization call
through `WR_USBIP_FSYNC(fd)`, which defaults to the ordinary POSIX `fsync(fd)`
in production. The C fixture overrides that call for directory descriptors to
return `EIO` after the temp file has been written, synced, and atomically
renamed. It expects `WR_USBIP_STORE_UNCONFIRMED`, then reads the replacement
table back to prove the error means durability is uncertain rather than the
rename being rolled back. The existing UI maps `synchronized:false` to its
localized warning and directs the operator to reload.

The generated actual HTTP-handler fixture now injects the same directory
`fsync` failure through the real settings/store implementation. It changes
the table contents, requires `saved:true`, `synchronized:false`, `applied:false`
and `flash_committed:false`, then reads back the changed table. The VM UI
fixture exercises that response and verifies the localized unsynchronized
warning survives request completion. This links store, endpoint and UI
expectations without treating an uncertain directory sync as an unchanged file.

The C fixtures are intended to exercise the Linux host filesystem error path;
their updated failure cases have not yet executed here. They do not prove target
flash durability, service behavior on WR1200JS, client transfer, or reboot
recovery. The fixture is included in the existing `zram-lifecycle.yml` USB/IP
runtime test step. Linux CI has not run since this change. The Windows MinGW
toolchain here lacks the POSIX `openat`, `O_DIRECTORY`, and `O_NOFOLLOW`
interfaces used by this target-storage fixture, so it cannot provide a valid
local build result. No router data was changed.

Local checks on 2026-10-19: `node tools/usbip/check-settings-view.js` passed;
the HTTP C-fixture generator ran to the Windows null device, Python AST parsing
and `git diff --check` passed. Generating C source is not a C compile or runtime
result. The existing service workflow already compiles and runs both C fixtures
with ASan/UBSan on Linux after this batch is pushed.

## Subsequent Linux CI evidence

[Service checks #245](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39294618711)
subsequently passed on head `9a6449e5da8b00b0c76b3af19c9c69cff25b8007`.
Job `118203806715` completed the existing ASan/UBSan compile-and-run commands.
Its original downloaded log confirms all three success markers at
2026-10-19 17:30:48 UTC:

- `PASS USBIP export store: ... directory-fsync uncertainty ...`
- `PASS USBIP HTTP settings: ... directory-fsync uncertainty ...`
- `PASS USBIP settings view: ... fsync uncertainty ...`

The sanitized excerpts are retained locally in `.codex/pr2-usbip-ci245.log`.
This supersedes the pending-Linux-execution statements above. The evidence is
Linux-host failure injection and JS behavior, not physical flash durability,
target MIPS execution of this failure branch or on-router recovery acceptance.
