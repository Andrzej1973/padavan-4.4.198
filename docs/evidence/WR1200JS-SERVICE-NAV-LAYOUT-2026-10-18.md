# WR1200JS service navigation layout adjustment — 2026-10-18

The user's router screenshot showed the six service groups wrapping to three
rows. The shared navigation CSS used a two-column layout below a 900 px viewport
width, which produces three rows for six groups. The two-column breakpoint is
now 760 px, keeping three columns (and therefore two rows) on wider router
views while retaining two-column and single-column layouts on narrower screens.

This is a source-level responsive layout adjustment in
`tools/services-nav/prepare-unified-nav.py`. It has not yet been rendered in a
new firmware image or checked in the router browser.

The same screenshot review found that Cron, Watchdog and Network discovery
navigation links all returned to the top of the same services page. Their
targets now use the existing `crond_enable_on_of`, `watchdog_cpu_on_of` and
`lltd_enable_on_of` element IDs. The source verifier now requires these exact
destinations and checks that the referenced anchors exist. This is a source
change only; final ROMFS and browser behavior have not been checked yet.

The same issue affected Telnet in the Access group. It now targets the existing
`telnetd_on_of` control, and the source verifier requires that destination too.

Read-only SSH inspection on 2026-10-18 confirmed that the page currently served
by the router still has unanchored Telnet, Cron, Watchdog and Network discovery
links, while all four target control IDs exist. The exact installed build
number remains unknown: `firmver` is `4.4.198.9`, while `buildno` and `extendno`
were empty. This confirms the defect on-device and that the source correction
has not yet reached the installed page; it does not verify a new image. See the
[runtime navigation check](../runtime/WR1200JS-2026-10-18-SERVICE-NAV.md).

## Follow-up — final-image gate and latest CI evidence, 2026-10-18

GitHub Actions full build #478 (`39139346947`, source `d1dc0eb`) completed
successfully. Its job log confirms that unified navigation was prepared and
that `prepare-unified-nav.py --verify-image` passed against final `trunk/romfs`
with EN/UK/RU labels and route checks. This verifies the committed navigation
and grouped status-panel implementation in that image; it does not verify
rendering or click-through on the physical router, which remains on the earlier
user-confirmed build #396.

A local follow-up strengthens the image gate for pages containing
`role="status"`: it now requires the actual status-selector wrapping logic,
cell and standalone panel styles, and the panel insertion operation. The
Python syntax and required-marker check pass locally. This stricter gate is a
working-tree change and was not part of build #478; the next final ROMFS build
must run it before the claim can be extended to the stricter check.

The build #478 job log was re-read on 2026-10-18. At 15:22:11 UTC the final
ROMFS command `prepare-unified-nav.py trunk/romfs --config trunk/.config
--verify-image` completed with `PASS unified service navigation routes, pages,
and EN/UK/RU labels`. The source commit was `d1dc0eb`. This independently
confirms the earlier navigation gate in the published image; the later local
capability-parser and status-panel preflight changes are not in that commit.

## Pre-compilation regression fixture — 2026-10-18

The status-panel image gate now delegates to a pure marker-contract helper. The
new `tools/services-nav/check-verifier.py` exercises both acceptance and
rejection cases without creating temporary files: a complete grouping script
and both panel styles pass, while missing insertion or either style fails. The
fixture passed locally, and the WR1200JS workflow invokes it before firmware
compilation. CI has not run this new preflight yet; build #478 predates it.

The first fixture draft attempted a nested directory in Windows `%TEMP%` and
was denied by the environment. Python could not remove that exact temporary
folder afterward (`%TEMP%\wr-services-nav-hv23huzi`). The fixture was rewritten
to avoid filesystem writes. This note does not claim that external temporary
folder was removed. No router state or firmware was changed.

## WPAD / PAC deep-link correction — 2026-10-18

The unified `WPAD / PAC` route now targets
`Advanced_DHCP_Content.asp#row_wpad`, the actual PAC editor row, instead of
opening the DHCP page at its top. The final-image verifier now requires that
exact route in the DHCP page navigation and continues to validate that the
fragment exists in the final page. The saved build #410 ROMFS DHCP page contains
`id="row_wpad"` and the `scripts.wpad.dat` editor field.

Local evidence: `tools/services-nav/check-verifier.py` passes; the changed Python
source parses; a read-only check of the saved ROMFS page confirms both target
markers; and `git diff --check` passes for the relevant workflow and verifier
files. This exact route change and stricter panel gate have not yet run in GitHub
CI or a new firmware image. The installed router remains on the user-confirmed
build #396; this local change has not been deployed.

## Return-route verifier follow-up — 2026-10-18

The image verifier previously checked only that the return label existed on
each standalone service page. It now requires the exact same-tab target
`/Advanced_Services_Content.asp` together with the localized return label.
Build #478 predates this stricter destination check; its image result proves the
older navigation implementation only. The current verifier change still needs
the next full-ROMFS build and router-browser click-through. No test or device
action was run for this follow-up.

## Capability filter correction — 2026-10-18

Review found that navigation config parsing retained commented lines and the
capability check searched for `CONFIG_OPTION=y` as a substring. A commented
optional selector such as `# CONFIG_FIRMWARE_INCLUDE_EOIP=y` could therefore
be treated as enabled and produce a misleading service shortcut.

The parser now ignores comments and accepts only active assignments. The final
image verifier reconstructs the expected navigation from active build
selectors and requires each page's navigation block to match exactly. The
pre-compilation fixture now covers a commented `=y`, an active `=n`, an active
`=y`, and the return link. The fixture and Python syntax checks passed locally;
the existing workflow runs this fixture before firmware compilation. A new
full-ROMFS check and router-browser review are still pending. No service
selector or router state was changed.

## Final-ROMFS result — build #488 — 2026-10-19

GitHub Actions run [#488](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39275709312)
completed successfully for PR #2. The PR head was `b99d9cd19ec5aa96d550ddf547bc32d92d505d03`;
the reusable WR1200JS workflow used merge revision
`a600659e21b63bd8153d51833d2278e203bd4811`.

The firmware job built `WR1200JS_4.4.198.9-488.trx` (12,616,562 bytes;
SHA256 `9a0b641b4b7c308eda7f25321f41321ce161eb4b8db4cb0e6373dac28287515f`).
Its final-ROMFS log reports `PASS unified service navigation routes, pages, and
EN/UK/RU labels`; the firmware ZIP and downloads jobs also completed
successfully. The overall run displayed a duration of 55m59s, while image
creation and the final-ROMFS navigation gate completed at 15:25:01 UTC. The
long wall time therefore did not indicate a stalled firmware compile. No
cancellation or redundant rerun was needed.

This is CI/image evidence only. It does not show the image installed on the
router or verify clicking the shortcuts in its physical browser. The previously
recorded router state and runtime acceptance boundary remain unchanged.
