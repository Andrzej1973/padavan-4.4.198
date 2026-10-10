# Wi-Fi Roaming Monitor

User-approved WR1200JS feature, 2026-10-09. Partially implemented; target runtime is not verified. Integrate with Enhanced Connected Devices on the homepage and provide a detailed monitor page.

## What to display

Per client: observed AP/BSSID, radio/band, SSID/network role, RSSI with timestamp and validity, previous attachment and bounded recent timeline. Distinguish Connected, Disconnected and Unknown. Show association changes separately from steering attempts and RSSI Kick actions. Include source and observation quality.

A completed band change means the same observed client identity moved from an authoritative association on one radio to an authoritative association on the other. Simultaneous/ambiguous or missed observations remain ambiguous. Disassociation alone is not a roam; removal from a driver steering candidate table is not proof of link loss. The existing clients.c explicitly treats deleted legacy steering entries as insufficient disconnection evidence. Probe frames/seen RSSI are not association proof.

Correlate actual action records with later authoritative client attachment. Label outcomes Observed after action, No destination observed, or Observation incomplete. Do not claim that timing proves causation. Client-initiated moves must be labeled as such only when evidence supports it; otherwise Cause unknown. RSSI Kick can disconnect without producing a successful move. Kernel/radio counters and build flags alone do not prove either feature works.

## Scope and collection

On a single WR1200JS observe its own 2.4/5 GHz associations and actions. Seeing a client leave does not reveal its new external AP. Multiple-AP history requires participating APs supplying authenticated, bounded association events or snapshots with AP identity, boot/session identifier, sequence and timestamp. Add this optional integration later; do not invent external AP locations from ARP/DHCP. Account for clock skew, missed events, reboot and out-of-order delivery.

Use a read-only collector independent of whether Band Steering/RSSI Kick is enabled. Reuse actual association tables/events and instrument real steering/kick command results. Classify attempted, accepted by driver, failed and later observed outcomes distinctly. Reading the monitor must never steer, kick, force scans or change settings.

Prefer event collection where drivers provide authoritative events; bounded association snapshots reconcile missed events. Browser refresh cannot capture all short transitions, so history must be collected on the router while the UI is closed. RSSI sampling may use a slower interval than attachment events. Measure collection overhead before selecting the final cadence.

Keep a fixed-size RAM ring buffer (initial design: up to 256 events, at most 128 observed clients), deduplicate unchanged association snapshots, rate-limit noisy clients and expose overflow/drop counts. No continual flash writes, full packet capture or continuous probing. Clear history on reboot unless a user explicitly requests an export; show the recording start time. Unobserved intervals are gaps, not successful transitions.

Use authenticated bounded JSON, shared homepage refresh/retry/hidden-tab handling, DOM text insertion for names, filters and stable row identities. Show current state and history age separately. MAC randomization may create new identities; do not silently merge different MACs by hostname. Provide manual device labels without implying automatic identity proof.

## Implementation sequence

1. Define event schema and driver association evidence for both WR1200JS radios; verify existing steering/RSSI Kick command paths and their actual result semantics.
2. Implement bounded passive recorder, association reconciliation and action correlation with explicit gaps/unknown outcomes.
3. Add homepage summary plus per-device timeline and detailed monitor, automatic refresh and export on demand.
4. Verify reordered/missed/duplicate events, reboot, timeout, randomized MAC, ring overflow, disabled steering, failed kick, driver candidate deletion, simultaneous observations and UI reconnection.
5. On real hardware, record an actual successful band transition and an actual RSSI Kick outcome using a client that is not the remote management tunnel. Verify resulting association and measure CPU/RAM/load; multiple-AP claims require evidence from both APs. No remote disruptive tests or router writes are authorized by this planning request.

## Acceptance

The UI must show an observed result rather than merely the presence of configuration. If destination, action outcome or cause cannot be established, say so. Preserve the current default settings and prioritize completion of WR1200JS before secondary router work.

## Mandatory automatic refresh and schedule — clarified 2026-10-09

Implement these device/roaming UI deliverables immediately after the current DNS/DHCP recovery integration and its verification, within the WR1200JS stage and before secondary-router expansion. Both components share a refresh lifecycle. Manual page reload is not an acceptable normal update mechanism: refresh visible data automatically, approximately every 5 seconds, retry after failures, show freshness/error state, preserve filters/expanded groups/scroll, and refresh immediately when a hidden tab becomes visible. One request in flight and a shared bounded cache prevent overlapping or per-browser repeated collection. History recording continues independently of hidden tabs.

Low load is a design goal, not measured evidence. Reuse existing data; do not trigger full scans or networkmap restarts per refresh. Keep classification/rendering in the browser, bounded passive recording/cache on the router and no continual flash writes. Before acceptance compare baseline and enabled CPU, process RSS, request latency and network traffic with identical client counts in idle and loaded conditions and with multiple browser sessions; include collector cost while no UI is open. Check that forwarding/Wi-Fi throughput and latency do not regress. Report actual measurements and tune collection intervals/limits if necessary; do not claim a percentage CPU cost or fixed RAM footprint before measuring.

## Implementation evidence — 2026-10-10

Commit `8c67e1554dc41c6b33eae379ba0d1d7cd3ab7a0e` connects the WR-only HTTP event-loop callback to a shared five-second association cache and bounded RAM history. The callback runs without browser requests; HTTP reads reuse the cache. Connection expiration remains unchanged. Blocking handlers can delay observations; missed intervals are recorded as gaps. No continual flash writes are introduced.

[ABI run 241](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38011112083) passed. Its source-parser gate covers native sanitizer fixtures, MIPS compilation, actual driver-layout extraction, radio query/merge validation and HTTP fixtures. The background fixture calls the callback before any HTTP request and checks a failed-source gap followed by a successful observed association. This is source and fixture evidence, not a real-router measurement.

The recorder bounds history to 256 events and 128 remembered client identities, reports overwrite/drop counts, requires two distinct successful samples before recording a band change, and treats simultaneous associations and collection gaps explicitly. It does not identify a steering cause or an external destination AP.

Still required: authenticated history JSON, homepage summary and detailed timeline with automatic refresh, actual steering/kick action instrumentation and outcome correlation, on-demand export, and target association/load measurements. Full build 124 failed the station-table ABI assertion: the userspace shared header defaulted to 32 clients while the WR drivers use 64. The WR-only selector fix preserves the assertion. ABI 244 passed the new native/MIPS probe that includes the untouched shared header using the prepared source prefix. Full build 126 now verifies the corrected code; neither a passing fixture nor a compiled image proves successful roaming on hardware.

## Action instrumentation source audit — 2026-10-10

Pinned source: `c25283e915a2a00a763774dd255b14aff997285e`. The `KickStaRssiLow` setter in both `mt76x2/ap/ap_cfg.c` and `mt76x3/ap/ap_cfg.c` updates a per-BSS threshold. Its successful return confirms configuration acceptance, not a particular client removal. Actual threshold enforcement is in `mt76x2/ap/ap.c` (around line 1381) and `mt76x3/ap/ap.c` (around line 2288); inspect and instrument the actual removal outcome there. Do not substitute threshold configuration logs for kick events.

The local steering transport `tools/band-steering/transport.c:wr_band_send` returns the result of the private ioctl. Driver acknowledgement is handled separately in `coordinator.c:wr_band_coordinator_event` through `WR_EVENT_GRANT` and the grant state machine. Record request intent, ioctl result and matching acknowledgement separately. Legacy `WR_EVENT_DELETED` handling invalidates candidate grants; it is not authoritative client disassociation.

Next implementation must provide bounded authenticated local event delivery from the driver/steering process to the HTTP RAM recorder, with radio/BSS/client identity, session, sequence, timestamp and explicit loss accounting. Avoid parsing verbose debug logs or writing events continually to flash. Correlate later association evidence without claiming causation. These source findings are not yet action instrumentation or hardware verification.

## Daemon integration requirements — source inspection 2026-10-10

The production staging path is `tools/band-steering/prepare-source-integration.py` -> `prepare-package-integration.py`. The latter explicitly copies daemon C modules and only headers from `tools/band-steering/*.h` into `trunk/user/wr-band-steering`. The dependency gap was corrected by commit `9b6c034af4697c0f3287b0386125c21e05131329`: the four required action headers are now copied into the target package `observations/` directory, with the staged protocol include rewritten for that layout. Isolated builds use `package/Makefile` with the original tools directory and must support the same integration.

Before modifying `main.c:send_command`, stage the complete action header dependency set and rewrite the protocol include for the staged layout. Verify both the original tools-tree build and the generated package build; passing a standalone action fixture is insufficient. The production wrapper must call the original transport exactly once and preserve its return/errno, with passive reporting optional when no collector is available. Queries and candidate deletion are not client roaming.

A complete integration also requires an owned local collector socket, verified sender lifetime/session, bounded draining and drop accounting, reconnect behavior after HTTP-daemon restart, actual grant acknowledgements, driver-side RSSI reason/outcome events and JSON/UI presentation. The HTTP observer must not control Steering lifecycle or make its startup depend on having a browser open. No live daemon integration has yet been delivered.

### Staged package verification

[ABI 260](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38026209692) passed the complete source preparation and registered target package step. That step compiles a MIPS translation unit including both staged `observations/steering-action.h` and `observations/action-send.h`, then builds the actual generated daemon and control executable. The standalone command-wrapper tests passed in ABI 259, and the nonblocking send tests passed in ABI 258. This establishes dependency and compilation coverage, not live event recording.

Still missing: opening/owning the collector endpoint, verifying service process lifetime, connecting and reconnecting after collector restart, wiring `main.c:send_command` and actual driver acknowledgements, bounded HTTP draining/history/JSON action presentation, and driver-side RSSI removal outcomes. Do not mark action monitoring complete until the whole path is exercised.
