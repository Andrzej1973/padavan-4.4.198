# Classic IoT real browser check

The host has no Playwright package/browser cache or Linux Chromium executable.
The existing Windows Edge installation supports the project's established CDP
test method. `python3 -B tools/iot/check-classic-browser.py` now exercises the
actual IoT form, configuration JS and navigation JS in a fresh headless Edge
profile. It reuses only the reviewed lifecycle/controller literal from the
existing browser checker; it does not execute or edit the paused Modern UI.

Result: PASS, Edge157. Actual DOM assertions cover initial disabled buttons,
explicit read, Main/Guest navigation preservation, safe SSID text, all three
save modes, KEEP/REPLACE, duplicate-click suppression, secret clearing,
unknown-result no replay and expired/regressed-clock refusal. CDP blocks all
page network requests. AJAX callbacks and the SDK frame are fixtures, so this
is not native HTTP/RC integration, native Classic frame/style acceptance or
device evidence. The separate C host fixture composes HTTP parsing with RC.

The owned Edge profile and temporary script were removed after successful
browser shutdown. No packages, persistent browser profile, router operation or
Codex application setting were changed. Failures retain their temporary profile
until process lifetime can be checked. Exact asset/tool hashes and result scope
are in WR1200JS-CLASSIC-EDGE-DOM-2026-11-18.json.

This optional Windows/WSL test is not added to Ubuntu CI. Its source and evidence
are included with the revision-bound runtime toggle package rather than
triggering a separate firmware cycle solely for a browser test. The companion
Edge report now includes both runtime buttons as well as the original modes.

CI observed meanwhile: standard1379 / 44231252043 and ABI932 / 44231255964
both succeeded for746ea2cc. Optional44233288115 was dispatched only after checking
standard's successful build/ZIP jobs and duplicate runs, with requested revision
746ea2cc05c9b73db8a0e51eb2441856500352e1 and dispatch revision05e77d61.
The newer Classic navigation package still requires its own target/image result;
independent optional1377 audit covers the earlier configuration-only page.
