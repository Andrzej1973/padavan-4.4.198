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
