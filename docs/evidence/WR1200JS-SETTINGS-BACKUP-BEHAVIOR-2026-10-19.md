# WR1200JS flash-save feedback and backup page fixture — 2026-10-19

The inherited settings page's flash-save error callback interpolates a jQuery
button object into a string timer; it cannot call `reset_btn_commit` with a
valid button ID. The shared header's error callback passes `#commit_btn` to a
helper that adds its own `#`, producing an invalid selector. The expanded VM
fixture reproduces the timer failure on the unmodified build #410 ROMFS page.

`tools/prepare-flash-save-feedback.py` replaces the two page and two header
string timers with function callbacks carrying the correct IDs. It checks all
source anchors before writing either file, is idempotent and rejects changed
upstream snippets. CGI URLs/actions, form behavior and session gates are not
altered. The source-preparation step and final-ROMFS Node test are wired into
the existing WR1200JS workflow.

Both feedback handlers now accept success only for numeric `sys_result: 0`.
The pinned `trunk/user/httpd/web_ex.c` CommitFlash handler emits that property
with `%d`; boolean `false`, an empty string or string `"0"` must not be shown
as success via JavaScript's loose equality. These malformed-result cases are
covered by the VM fixture.

`tools/check-settings-backup-behavior.js` executes the supplied page and sibling
`state.js` in Node VM, or accepts their texts as JSON on stdin for in-memory
source checks. It exercises the actual `initial`, form setters, backup/restore
handlers and flash-save handlers with inert Ajax/browser/timer substitutes:

- All eight privileged rows start hidden and are revealed only by a safe
  session's initial function, with exact row IDs checked.
- Cancelled resets and header flash-save confirmation send no request.
- Reset/upload forms use the expected action names, URLs and encodings;
  backup downloads use the expected names without a settings form submit.
- Page NVRAM/storage and header flash-save buttons handle server success,
  server failure, null/malformed responses and Ajax errors. The timer invokes
  the real reset helper, removes feedback from the correct button, and uses
  no string evaluation.

The expanded fixture intentionally rejects the unmodified #410 page at the
known timer defect and passes after the production transform is applied in
memory. Idempotence and changed-anchor refusal also pass. Earlier, the smaller
fixture passed on #410 because it did not exercise flash-save feedback.
The corrected fixture also passed on the real page/state.js from the verified
exact Git archive at pinned revision `c25283e915a2a00a763774dd255b14aff997285e`,
transformed in memory without temporary directories.

These checks establish client JavaScript behavior only. New final-ROMFS/CI and
browser checks, server authentication/CGI acceptance, actual flash writes and
restore/reboot recovery remain unverified. No HTTP request, flash write,
router setting change or reboot was performed.
