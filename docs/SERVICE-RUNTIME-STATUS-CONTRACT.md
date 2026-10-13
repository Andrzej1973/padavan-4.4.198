# Actual service and driver state in WebUI

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

## ZRAM implementation progress

Commits `b952b16` and `793241e` add a page-load observation of `/proc/swaps`, a separate actual-state label beside the unchanged requested setting, EN/UK/RU labels, and linked-handler/page image gates. The inherited Apply completion calls `refreshpage()`, so the server observation is obtained again after Apply. This is a page-load snapshot, not continuous monitoring; manual browser refresh obtains another observation.

[CI run 38271573998](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38271573998) passed ASan/UBSan execution of the emitted HTTP handler for all five operational states, missing/empty/malformed input and unrelated swap devices. The same run passed lifecycle failure-path checks. Full images 224/225 and physical-router/browser checks are pending. Other service and driver adapters remain unimplemented under this contract.

Subsequent verification: [full build 224](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38271382261) completed successfully, including the shipped ZRAM page/linked-handler gate. It precedes the additional malformed-input header validation; build 225 contains that refinement and remains pending at this observation.

## Stubby and DoH process observation

Commit `64fa50b` adds separate EN/UK/RU labels for process presence beside requested settings on both DNS pages. A present process is explicitly labelled DNS-unverified. This does not implement functional resolver checks, TLS health, complete DoH child-process coverage or continuous polling. [CI 38272444310](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38272444310) passed native ASan/UBSan execution of the emitted handler for enabled/disabled, present/absent, inaccessible proc and invalid-selector cases. Full build 226 and physical-router/browser verification remain pending.

## VPN source findings and implementation requirements

The imported `vpncli.asp` currently hides WireGuard state when the reported state is zero or the requested enable switch is off; state 1 renders a green Connected label. This prevents users seeing disabled-but-still-present or inactive states. Keep the actual-state indicator visible for the selected supported VPN type, with requested configuration shown separately.

The imported `wgc.sh` initializes `wg_latest_handshakes_t` to the current time during startup, before a successful handshake. Its later successful connection check updates that value, but the variable alone cannot establish a real peer handshake. Do not repurpose it as runtime peer evidence or alter its watchdog behavior merely to add UI status.

Client interface is `wg0`. Observe real interface presence separately from actual WireGuard/AmneziaWG peer handshake data. Missing handshake or an idle/old handshake must be described accurately; a recent handshake does not prove all routes or Internet traffic work. An observer must use bounded read-only operations, disclose sampling age, and avoid exposing peer/private keys. Interface and handshake observations remain unimplemented at this stage.

The subsequent interface observer reads fixed sysfs flags for client `wg0` and server `wg1`. It reports absent/UP/DOWN/unknown states separately from requested configuration, labels peer connectivity unverified and changes the client controller badge to an explicitly historical label. EN/UK/RU labels, source preparation and native observer tests are wired into CI; build and test results are pending. Actual peer-handshake observation, continuous refresh and router/browser execution remain unimplemented or unverified.

## Handshake observation progress — 2026-10-13

Commits through `7fa96c1` add a bounded parser of actual `wg show wg0/wg1 latest-handshakes`, a monotonic freshness cache, supervised background workers and page refresh. HTTP requests read cached observations; they never execute the utility. Sampling runs every 30 seconds independently of the page. A worker is cancelled at the first event-loop tick at or after its three-second deadline (the existing idle-loop wakeup is five seconds, so this is not a hard three-second wall-clock guarantee). Shutdown cancels workers without a blocking wait; remaining killed children are inherited by init when HTTP exits.

EN/UK/RU page labels distinguish unavailable and stale data, show peer counts by timestamp category, sampling age and youngest handshake age. The manual button reads the latest cached observation; it does not force a new utility run. Page refresh occurs every 30 seconds while visible. Recent counts describe the sampling instant. Observations do not establish routing or Internet health, and no peer keys are returned.

[Native CI 38425199952](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38425199952) passed parser/cache, subprocess failure/malformed-output, timeout, HTTP role/freshness and UI formatting checks. Source preparation also passed on a local fixture built from the pinned HTTP source and imported VPN pages. [Full build 229](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38425200060) is in progress at this observation. Image contents, MIPS runtime, physical router behavior and browser behavior remain unverified; this is not a claim of a completed device port.

Subsequent evidence: full build 229 succeeded; downloaded artifact sizes and hashes are recorded in `docs/evidence/WR1200JS-BUILD229.md`. It predates the dedicated handshake image gate and subsequent runtime fixes. Commit `e1a0a26` accepts already completed workers before enforcing the deadline and measures sample age from query start. Commit `1c96a5a` closes inherited descriptors in the worker itself. Commit `c661102` adds one authenticated update response containing a fresh sysfs interface observation and cached handshake statistics, so both indicators refresh together. Native CI [38427208810](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427208810), [38427427949](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427427949) and [38427759179](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427759179) passed the respective checks. Full images containing these refinements and physical execution remain pending at this observation.
