# Actual service and driver state in WebUI

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
and UI fixtures pass; final-image CI and physical-page behavior are pending.

Hardware watchdog remains open. Pinned `services.c` requests
`module_smart_load("rt_timer_wdg", NULL)` when `watchdog_cpu` is enabled, but
this source observation alone does not establish that the module exists in the
WR1200JS image, is registered, or is successfully serviced. Before adding a
status label, verify the actual driver/image evidence and choose an observation
that does not imply hardware timer operation from configuration or module
presence alone.

Cron implementation follow-up: an observed-process row is now prepared next to
the existing Cron control, using `crond_enable` and the `crond` process launched
by pinned services.c. Target #426 applet inventory includes crond/crontab.
The adapter distinguishes requested/observed combinations, unavailable proc or
provider and negative process observations. EN/UK/RU labels explicitly leave
job execution unverified. Manual/visible-page refresh and 45-second expiry use
the existing observer UI template. Emitted backend/UI fixtures passed locally;
firmware CI and final-image checks passed in build #441; physical acceptance is
pending. The image includes the Cron page and HTTP handler. LLTD, ASUS discovery
and hardware watchdog remain open. This supersedes Cron's missing-implementation
status in the older paragraph below, not its runtime gap.

At build #433 the Administration/Services page exposed Cron (`crond_enable`),
LLTD (`lltd_enable`), ASUS discovery (`adsc_enable`) and hardware watchdog
(`watchdog_cpu`) without observed-state adapters. Cron has an adapter and its
shipped page/handler markers are verified in build #441. LLTD and ASUS
discovery now have bounded process observations; those do not establish protocol
exchanges or client visibility. Hardware watchdog remains without a status
adapter. A switch value alone must not be reported as actual operation.

Next implementation work: verify the watchdog's actual driver/image capability
and determine a truthful observable state for it before adding a status UI. A
Cron process still does not establish scheduled-job success. A watchdog module
registration, if observable, would not by itself establish hardware timer
registration or petting. Retain the user's enable settings and do not activate
services during this audit.

Current image evidence remains distinct: #433 proves VPN editor packaging;
#426/#428 establish the documented target BusyBox/storage component checks.
Build #441 adds successful final-image checks for the observed service pages,
handlers and target BusyBox audit; see [build evidence](evidence/WR1200JS-BUILD441.md).
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
