# Actual service and driver state in WebUI

## WR1200JS unsupported CPU timer watchdog — 2026-10-21

The `watchdog_cpu` switch targets the optional `rt_timer_wdg` module, which is
absent from the WR1200JS source/image path and live device sample. It is not the
built-in MT7621 watchdog. WR1200JS therefore hides the enable control, ignores
legacy saved values in the lifecycle, and defaults the setting off; other
boards retain their own supported behavior. A read-only diagnostic row remains
separate from any enable control. The exact source and device evidence plus
implementation/check status are recorded in
`evidence/WR1200JS-CPU-WATCHDOG-CAPABILITY-2026-10-21.md`.

## Remaining administration-service coverage — 2026-10-18

LLTD and ASUS Info Discovery now show their configured setting separately from
the observed `lld2d` and `infosvr` processes. The process names and executable
paths are verified against the build's pinned Padavan source revision
`c25283e915a2a00a763774dd255b14aff997285e`, where `start_lltd()` launches
`/bin/lld2d` and `start_infosvr()` launches `/usr/sbin/infosvr`. HTTP observers
return disabled/inactive, enabled/present, enabled/absent, disabled/still
present, or unknown if `/proc`, the provider binary or process observation is
unavailable. The UI is localized, manually refreshable, avoids polling hidden
tabs and expires observations after 45 seconds. This does not verify LLTD
exchanges, ASUS discovery replies, or client visibility. Local emitted-handler
and UI fixtures pass. The final-image verifier passed in WR1200JS build #448
(`5dd2c80`), checking the shipped page, httpd handlers, observation logic and
EN/UK/RU labels. Physical-page behavior and protocol exchanges remain pending.

Hardware watchdog now has a bounded observer for the saved `watchdog_cpu`
setting and `/sys/module/rt_timer_wdg` presence. Pinned `services.c` requests
`module_smart_load("rt_timer_wdg", NULL)` when enabled, but
`trunk/configs/boards/WR1200JS/kernel-4.4.x.config` separately sets
`CONFIG_MT7621_WDT=y` while leaving `CONFIG_RALINK_WDT` unset. The built-in
MT7621 watchdog driver and optional `rt_timer_wdg` module are distinct paths.
The live WR1200JS read-only sample later found `watchdog_cpu=1`, no optional
module file under `/lib/modules`, and no `/sys/module/rt_timer_wdg`, while
`/dev/watchdog` and `/sys/class/watchdog/watchdog0` existed. No readable
watchdog0 timer-state attribute or driver link was available in that sample.
The UI help now explicitly says the optional module and built-in driver are
separate, and that device-node presence does not prove timer activity. The
status observer only reports the optional module and does not claim hardware
timer servicing. Local handler/UI fixtures pass. The final-image verifier
passed in build #448 (`5dd2c80`), checking the shipped status row, handler,
refresh behavior and the earlier EN/UK/RU labels. The newer help wording that
distinguishes the built-in driver from the optional module is a local source
change and has not yet been checked in a final image. Physical-page behavior
and a reliable signal for timer registration/servicing remain unverified. Service run
#221 for commit `3976cf1` failed only in the Linux C fixture because strict C99
did not expose `S_IFREG`; the original job log confirmed this exact cause. The
fixture now defines the portable file-type constant and passes locally. The
final-image check in #448 is separate evidence. Service CI `39115923393`
for `469d0de` passed; its original log confirms execution of
`tools/check-discovery-status.py` and PASS for LLTD/ASUS process and watchdog
module states, including unknown conditions. This supersedes the earlier
pending host-fixture status; hardware timer operation remains unverified.

Cron implementation follow-up: an observed-process row is now prepared next to
the existing Cron control, using `crond_enable` and the `crond` process launched
by pinned services.c. Target #426 applet inventory includes crond/crontab.
The adapter distinguishes requested/observed combinations, unavailable proc or
provider and negative process observations. EN/UK/RU labels explicitly leave
job execution unverified. Manual/visible-page refresh and 45-second expiry use
the existing observer UI template. Emitted backend/UI fixtures passed locally;
firmware CI and final-image checks passed in build #441; physical acceptance is
pending. The image includes the Cron page and HTTP handler. LLTD and ASUS
discovery have process observations that do not establish protocol exchanges.
The watchdog module observer does not establish timer operation. This supersedes
Cron's missing-implementation status in the older paragraph below, not its
runtime gap.

At build #433 the Administration/Services page exposed Cron (`crond_enable`),
LLTD (`lltd_enable`), ASUS discovery (`adsc_enable`) and hardware watchdog
(`watchdog_cpu`) without observed-state adapters. Cron has an adapter and its
shipped page/handler markers are verified in build #441. LLTD and ASUS
discovery now have bounded process observations; those do not establish protocol
exchanges or client visibility. Hardware watchdog now has a bounded module
presence observation; neither its setting nor module presence establishes
hardware timer operation. A switch value alone must not be reported as actual
operation.

Watchdog signal assessment — source checked at pinned Padavan revision
`c25283e915a2a00a763774dd255b14aff997285e`: the MT7621 driver registers a
watchdog device in `probe()` but enables the timer only in its `start()` callback
by setting `TMR1CTL_ENABLE`. The 4.4 watchdog core creates the class device but
does not publish an active-state sysfs attribute. Opening `/dev/watchdog` invokes
`watchdog_start()`, so an HTTP observer must not open it as a status probe: that
would change device state. The optional Padavan `rt_timer_wdg` module is a
separate path from built-in `CONFIG_MT7621_WDT`. No safe read-only operation
signal has been established; keep the UI label limited to the requested setting
and optional module presence, with timer activity explicitly unverified.
Sources: [MT7621 watchdog driver](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/watchdog/mt7621_wdt.c#L69-L78), [watchdog core registration](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/watchdog/watchdog_core.c#L195-L203), [watchdog character-device open](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/watchdog/watchdog_dev.c#L414-L440).

A Cron process still does not establish scheduled-job success. Retain the user's
enable settings and do not activate services during this audit.

Current image evidence remains distinct: #448 passed the WR1200JS firmware
build and final SSH/Cron/LLTD/ASUS/watchdog observer image gate; this proves
packaging and UI markers only, not device runtime. #426/#428 establish the
documented target BusyBox/storage component checks; #441 added earlier
final-image checks for service pages and handlers; see [build evidence](evidence/WR1200JS-BUILD441.md)
and [build #448 evidence](evidence/WR1200JS-BUILD448.md).
Host CI for synchronized VPN mutations and DNS/ZRAM freshness passed, but
physical browser, service interactions and reboot persistence remain open.

## Process observation expiry — 2026-10-18

SSH, iPerf3 and Privoxy process indicators now expire to unknown 45 seconds
after receipt without a new observation. A visibility-change check invalidates
old observations immediately when returning to a hidden tab. Generation guards
prevent old timers from replacing newer results; noninteger states are rejected.
The timestamp remains the historical last observation, not a claim of current
health. Local emitted-JavaScript tests passed for all three observers. Full CI,
final-image inclusion and physical browser behavior for this change remain open.
No service lifecycle or saved enable setting is changed.

ZRAM now uses the same 45-second observation lifetime, including its initial
page sample, integer-state validation and visibility-return age check. The
emitted-page Node fixture passed locally (a fixed local fixture directory was
used because Windows sandbox temporary-directory creation failed). The ROMFS
gate requires the expiry controls. CI and physical browser acceptance remain
pending; this does not activate swap or change its configuration. DNS/DoH
observation expiry was a separate open item at that checkpoint.

Follow-up: Stubby/DoH initial and AJAX observations now share the same
45-second lifetime and visibility-return check. Expiry clears both the DoH
process label and all slot descriptions to unknown. A generation guard keeps
old timers from replacing newer data. The emitted DoT/DoH Node fixture passed
locally; both ROMFS verifiers now require these controls. CI/image/physical
acceptance remains pending for this change. These remain process observations,
not functional DNS/TLS checks; the live router's intentionally disabled DNS
services were not changed.

## Independent VPN profile link freshness

The independent profile table has an explicit authenticated, bounded
read-only observation using the fixed manager's `observe` command. It shows
interface absent, UP, DOWN or unknown, and does not assert handshake,
ownership or routed connectivity. A local follow-up displays browser receipt
time for successful observations and expires the text to unknown after 30
seconds without further network requests. A per-profile generation guards
against an old expiry invalidating a newer observation. Local actual-JS tests
cover expiry, refresh generations and no network calls on expiry; Linux CI
and image/browser acceptance for this follow-up remain pending.

## DoH instance ownership follow-up

The observer introduced in `670c12b` passed native ASan/UBSan CI [38505941650](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38505941650). The subsequent read-only HTTP handler passed emitted-handler tests in [38506100513](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38506100513). It reports four-bit masks for configured slots, PID-file/executable ownership, unknown observations and duplicate PIDs without exporting resolver URLs or PID values.

The DoH page now consumes that handler on entry, manual refresh and its existing 30-second visible-page interval. EN/UK/RU descriptions distinguish configured slots without confirmed processes, unknown slots, duplicate PIDs and owned processes in unconfigured slots. A malformed/failed response clears the displayed observation to unknown. Existing Stubby numeric process state remains unchanged. Local emitted-page tests cover these cases and request single-flight/hidden behavior; shipped-image checks require the new handler, renderer and locale keys. Full image and physical page verification remain pending for this change. PID ownership alone does not verify a listener, the process's resolver profile, DNS responses or TLS validation. The live router's DoH remains intentionally disabled.

Subsequent image evidence: [full build 258](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38506299524), commit `f93f467d2b2752c1eec25958c8426531a7e54376`, completed successfully. The downloaded original [DoH image report](evidence/build258-doh-image-checks.json) confirms `observed_process_ui`, `observed_instance_backend`, all three shipped status locales and dependency/loader checks. It contains no missing libraries or invalid ELF files. This supersedes the pending image status above, but physical page behavior, actual DoH DNS/TLS and start/stop/reboot behavior remain unverified. The expanded per-slot instructions added after this commit are not proven included by build 258.

User requirement, 2026-10-12: every exposed service, feature and driver must show its actual operational state. An enabled configuration switch must never be presented as proof that the service is working.

Keep the saved enable switch as the requested setting. Place an actual-state badge beside it, with a short reason and the time of the last successful observation. Do not silently change the saved setting after a start failure.

Required states, localized in Ukrainian, Russian and English:

- Disabled: configured off and observed inactive.
- Working: observed active using evidence appropriate to the feature.
- Starting/stopping: a real operation is in progress; bounded timeout leads to failure or unknown.
- Error / not running: configured on but observed inactive or failed.
- Still running: configured off but observed active; stopping has not been confirmed.
- Unknown / stale: observation failed or expired. Never show green working status based on saved settings or old data.
- Unsupported: capability absent on this model/image; hide its enable control or explain the unavailable capability.

Refresh on page entry and after Apply; provide manual refresh. Periodic refresh should be modest, suspend on hidden pages and use a shared bounded cache. Observation must not restart services, change NVRAM or probe the network aggressively.

## Evidence required by feature

ZRAM: active `/dev/zram0` entry in `/proc/swaps`; a module, initialized device or nonzero disksize alone is insufficient. DNS forwarders: process/listener state is distinct from successful resolution, upstream reachability and TLS validation. VPN: daemon/interface state is distinct from a peer handshake or working route. Wi-Fi: distinguish interface/radio enabled state, actual associations and driver features. NAT acceleration: requested mode is distinct from actual hardware registration. Band Steering: use driver observations and controller health rather than only BandSteering=1. ZeroTier: distinguish daemon, network membership, authorization and online status. Other services require their own runtime adapter and failure reasons.

Controls for Enable/Disable continue to use the existing service lifecycle. A failure must remain visible, preserve access to the router and offer a retry or corrective guidance where implemented. Avoid success messages before observing the result.

## Initial implementation order and acceptance

Start with ZRAM, where live evidence shows enabled setting with zero active swap. Then cover Stubby/DoH, VPN services and radio/acceleration controls, followed by the remaining selected services. Preserve every applicable existing control and model-specific capability gate.

Verify enabled-but-dead, disabled-but-live, unavailable observation, normal operation, start/stop failure, stale cache and reboot states. UI must match the runtime adapter and retain the requested setting. Full coverage remains pending; this document does not claim implementation.

## Privoxy status implementation progress — 2026-10-17

The Privoxy page now has a separate observed-process indicator driven by a
read-only HTTP observation. It distinguishes disabled/no process, enabled/process
present, enabled/no process, unknown observation, and process present while the
saved setting is off. A present process is explicitly not presented as proof of
a listening socket, working client configuration, or proxy traffic. The normal
Privoxy enable control and Apply lifecycle remain unchanged. EN/UK/RU labels,
manual refresh, visible-page refresh, and ROMFS image checks are wired into the
WR1200JS build. This change is pending its CI image/build result and physical
browser/device acceptance; do not mark Privoxy runtime verified yet.

## iPerf3 status implementation progress — 2026-10-17

The iPerf3 settings page now has a separate observed-process indicator beside
the unchanged enable switch. It distinguishes disabled/no process,
enabled/process present, enabled/no process, unknown observation, and a process
still present while disabled. The UI states clearly that process presence does
not establish a client connection or successful throughput test. It offers
manual refresh and a 30-second interval while the page is visible; EN/UK/RU
labels and a selected-image gate are wired into the WR1200JS build. This change
has not yet been validated by CI or on the router. Do not claim iPerf3 runtime
or client-test verification from this observer.

Build #405, containing iPerf3 status, was blocked before its dedicated
per-service gate by the shared navigation gate. That gate incorrectly looked
for source fragment `EN.footer` inside ROMFS; the build combines it into
`EN.dict`. Build #406, containing SSH status, failed at the same shared
navigation ROMFS gate: it searched for `WRServicesNav` in `EN.footer`, while
the image merges translations into `EN.dict`. Commit `45ef6e1` corrects the
shared verifier. Manual WR1200JS build #407 (`39057712642`) is running against
`45ef6e1`; full-image verification remains pending.
Build #405 did compile and install the
iPerf3 daemon, but failed final ROMFS verification and did not produce a
qualified image. iPerf3 and SSH image verification remain unconfirmed.

### Superseding image evidence — 2026-10-18

Build #478 (`d1dc0eb`) subsequently passed the conditional iPerf3 final-ROMFS
verifier. Its job log states that the status UI, HTTP handler and EN/UK/RU
labels were found; artifact `iperf3-image-checks` was uploaded. See
[build-specific evidence](evidence/WR1200JS-BUILD478-IPERF3-IMAGE.md). This
supersedes the pending image status above only. The read-only router sample
reported `iperf3_enable=0` and no process; neither client connectivity nor a
throughput measurement has been tested.

## USB/IP status and guarded device controls — 2026-10-18

The selected WR1200JS source exposes separate module/process observations, a
bounded USB device inventory, and authenticated, confirmation-gated bind/unbind
operations serialized by the USB/IP lifecycle lock. The export-selection UI
stores a stable VID/PID/serial identity; optional restore defaults off and
checks identity and safety policy before binding. These observations do not
establish an available listener, remote attachment, or data transfer.

Build #478 passed the exact-image BusyBox restore orchestration fixture and
USB/IP settings ROMFS verifier; details and artifact digest are in
[USB/IP build evidence](evidence/WR1200JS-BUILD478-USBIP.md). Saved selection
is written under `/etc/storage/usbip`, while the HTTP response explicitly says
`flash_committed:false`. Physical module/daemon state, real USB operations,
client transfer and storage-save/reboot persistence remain unverified. A
read-only SSH probe could not run here because the `ssh` command resolves to an
explicit sandbox-denial wrapper; no router command was executed.

USB/IP storage follow-up, 2026-10-19: the storage fixture now injects a
directory-`fsync` failure after successful file write and atomic rename. It
requires the backend to return `WR_USBIP_STORE_UNCONFIRMED` while confirming
the replacement file is readable in the current runtime. This covers the
uncertain-durability branch consumed by the UI warning; it does not establish
flash commit or reboot persistence. The fixture has not yet run in Linux CI;
the Windows MinGW compiler cannot build this POSIX `openat`/`O_NOFOLLOW` test.
No router settings were changed.

Inherited settings backup/restore follow-up, 2026-10-19: the ROMFS verifier
still checks packaging, while `tools/check-settings-backup-behavior.js` now
executes the shipped page handlers under inert Node browser stubs. It passed
locally on the available #410 ROMFS page for the `login_safe()` row gate,
restore cancellation/confirmation, CFG/TBZ backup downloads, upload extension
validation and CGI form destinations. The test is wired into the next firmware
build. It does not call CGI, test a browser session, or verify flash/recovery
behavior; device acceptance remains pending. See
[backup/restore behavior evidence](evidence/WR1200JS-SETTINGS-BACKUP-BEHAVIOR-2026-10-19.md).

## SSH daemon status implementation progress — 2026-10-17

The Administration / Services page now reports the selected Dropbear or
OpenSSH process separately from the saved SSH mode. It distinguishes disabled,
enabled with process present, enabled without a process, unknown observation,
and a process still present while disabled. Process presence does not verify a
listening socket, firewall reachability or authentication. Manual refresh,
visible-page 30-second refresh, EN/UK/RU labels and a ROMFS image gate are wired
into the WR1200JS build. CI and physical browser/device acceptance are pending.

## ZRAM implementation progress

Commits `b952b16` and `793241e` add a page-load observation of `/proc/swaps`, a separate actual-state label beside the unchanged requested setting, EN/UK/RU labels, and linked-handler/page image gates. The inherited Apply completion calls `refreshpage()`, so the server observation is obtained again after Apply. This is a page-load snapshot, not continuous monitoring; manual browser refresh obtains another observation.

[CI run 38271573998](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38271573998) passed ASan/UBSan execution of the emitted HTTP handler for all five operational states, missing/empty/malformed input and unrelated swap devices. The same run passed lifecycle failure-path checks. Full images 224/225 and physical-router/browser checks are pending. Other service and driver adapters remain unimplemented under this contract.

Subsequent verification: [full build 224](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38271382261) completed successfully, including the shipped ZRAM page/linked-handler gate. It precedes the additional malformed-input header validation; build 225 contains that refinement and remains pending at this observation.

## Stubby and DoH process observation

ZRAM follow-up, 2026-10-13: commit `4ff8fee` adds manual refresh and a 30-second visible-page interval, with no overlapping requests and no requests on unsupported models. Request failure renders unknown. The image gate now checks refresh controls and shipped EN/UK/RU button labels. [Native CI 38430285721](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38430285721) passed observer/lifecycle checks. [CI 38431626049](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38431626049) executes the emitted browser function with capability, hidden-page, duplicate-click, error and invalid-response fixtures.

[Full build 238](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38430285996) completed successfully. Its log `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build238-log.txt` records the ZRAM image gate passing at 16:33:09 UTC and the handshake image gate at 16:32:51 UTC. The workflow manifest reports `WR1200JS_4.4.198.9-238_4ff8feee.trx`, 13,139,623 bytes, SHA256 `3e1151285ebc4a68bdde9816383089b4aa211f2d48e5b75fff5d1d76cd03d76f`; this is a manifest value, not a locally recomputed image hash. ZRAM activation after flashing/reboot and physical browser execution remain unverified.

Commit `64fa50b` adds separate EN/UK/RU labels for process presence beside requested settings on both DNS pages. A present process is explicitly labelled DNS-unverified. This does not implement functional resolver checks, TLS health, complete DoH child-process coverage or continuous polling. [CI 38272444310](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38272444310) passed native ASan/UBSan execution of the emitted handler for enabled/disabled, present/absent, inaccessible proc and invalid-selector cases. Full build 226 and physical-router/browser verification remain pending.

## VPN source findings and implementation requirements

DNS follow-up: commit `981bed4` adds manual process-state refresh and a 30-second visible-page interval for Stubby and DoH. Requests use the existing authenticated update route, do not overlap and do not modify services. Request failure renders unknown. Commit `385d57d` adds shipped-page, linked-handler and shipped EN/UK/RU status-label checks to both service image verifiers. [CI 38428683542](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38428683542) passed the native process observer checks. Commit `f24166a` executes the emitted refresh function under controlled AJAX/browser state; [CI 38429109908](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38429109908) passed concurrent-click, hidden-page, request failure, invalid response and disabled-state cases. Physical browser behavior, complete DoH child coverage and functional DNS/TLS health are still pending.

The imported `vpncli.asp` currently hides WireGuard state when the reported state is zero or the requested enable switch is off; state 1 renders a green Connected label. This prevents users seeing disabled-but-still-present or inactive states. Keep the actual-state indicator visible for the selected supported VPN type, with requested configuration shown separately.

The imported `wgc.sh` initializes `wg_latest_handshakes_t` to the current time during startup, before a successful handshake. Its later successful connection check updates that value, but the variable alone cannot establish a real peer handshake. Do not repurpose it as runtime peer evidence or alter its watchdog behavior merely to add UI status.

Client interface is `wg0`. Observe real interface presence separately from actual WireGuard/AmneziaWG peer handshake data. Missing handshake or an idle/old handshake must be described accurately; a recent handshake does not prove all routes or Internet traffic work. An observer must use bounded read-only operations, disclose sampling age, and avoid exposing peer/private keys. Interface and handshake observations remain unimplemented at this stage.

The subsequent interface observer reads fixed sysfs flags for client `wg0` and server `wg1`. It reports absent/UP/DOWN/unknown states separately from requested configuration, labels peer connectivity unverified and changes the client controller badge to an explicitly historical label. EN/UK/RU labels, source preparation and native observer tests are wired into CI; build and test results are pending. Actual peer-handshake observation, continuous refresh and router/browser execution remain unimplemented or unverified.

## Handshake observation progress — 2026-10-13

Commits through `7fa96c1` add a bounded parser of actual `wg show wg0/wg1 latest-handshakes`, a monotonic freshness cache, supervised background workers and page refresh. HTTP requests read cached observations; they never execute the utility. Sampling runs every 30 seconds independently of the page. A worker is cancelled at the first event-loop tick at or after its three-second deadline (the existing idle-loop wakeup is five seconds, so this is not a hard three-second wall-clock guarantee). Shutdown cancels workers without a blocking wait; remaining killed children are inherited by init when HTTP exits.

EN/UK/RU page labels distinguish unavailable and stale data, show peer counts by timestamp category, sampling age and youngest handshake age. The manual button reads the latest cached observation; it does not force a new utility run. Page refresh occurs every 30 seconds while visible. Recent counts describe the sampling instant. Observations do not establish routing or Internet health, and no peer keys are returned.

[Native CI 38425199952](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38425199952) passed parser/cache, subprocess failure/malformed-output, timeout, HTTP role/freshness and UI formatting checks. Source preparation also passed on a local fixture built from the pinned HTTP source and imported VPN pages. [Full build 229](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38425200060) is in progress at this observation. Image contents, MIPS runtime, physical router behavior and browser behavior remain unverified; this is not a claim of a completed device port.

Subsequent evidence: full build 229 succeeded; downloaded artifact sizes and hashes are recorded in `docs/evidence/WR1200JS-BUILD229.md`. It predates the dedicated handshake image gate and subsequent runtime fixes. Commit `e1a0a26` accepts already completed workers before enforcing the deadline and measures sample age from query start. Commit `1c96a5a` closes inherited descriptors in the worker itself. Commit `c661102` adds one authenticated update response containing a fresh sysfs interface observation and cached handshake statistics, so both indicators refresh together. Native CI [38427208810](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427208810), [38427427949](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427427949) and [38427759179](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427759179) passed the respective checks. Full images containing these refinements and physical execution remain pending at this observation.

Full-build follow-up: [build 232](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427428174), commit `1c96a5abc3e2a06832579ecb44340cd337b83d37`, completed successfully. The downloaded run log `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build232-log.txt` records the shipped handshake image gate passing at 16:19:03 UTC and guide checks passing at 16:19:06 UTC. Its manifest reports `WR1200JS_4.4.198.9-232_1c96a5ab.trx`, 13,139,487 bytes, SHA256 `33eda3bd1bd9d3bb5ceb1d1c151bf7316298b7193dd2b611a86edd460a7524c1`; this hash is from the workflow manifest and has not been independently recomputed locally. This proves compilation and selected image contents through worker descriptor isolation. Joint interface/handshake refresh, DNS refresh image gates and physical execution are not established by this build.

## Build #504 service/runtime evidence follow-up — 2026-10-20

Build #504 (run `39461735957`, PR source head `9c1e9b1`) passed its image
checks for the iPerf3 and SSH status pages/handlers, ZRAM dependencies and
BusyBox help, Stubby packaging/ELF dependencies and an authenticated DoT
lookup through the image under QEMU, and DoH packaging/ELF dependencies. The
same run passed the target BusyBox audit. See the [build #504 service
checkpoint](evidence/WR1200JS-BUILD504-SERVICE-AUDIT.md). These checks are
image/CI evidence, not device execution.

The downloaded `target-busybox-audit.json` identifies the scope precisely:
`selected_service_entrypoint_map_complete` is true, there are no entrypoint
gaps or unmapped active selector groups, and the image's selected service
entrypoints are present with shell syntax accepted where applicable. However,
`runtime_verified` and `whole_service_audit_complete` are both false. Its
Stubby, DoH, Privoxy and vlmcsd dispatch probes exercise only refusal of an
unknown action; they explicitly do not enter configuration, locking or daemon
lifecycle paths. The audit labels all service interactions unverified.

Separately, the read-only WR1200JS sample from 2026-10-18 observed 30,912 KiB
of active `/dev/zram0` swap. No service was toggled for the #504 image check;
enable/disable behavior and reboot persistence remain open. The unsupported
PPTP/L2TP VPN UI correction is now pushed as commit `35d70be`; build #505 is
queued to verify its final-ROMFS result. No firmware was installed and no
router state was changed for this follow-up.
