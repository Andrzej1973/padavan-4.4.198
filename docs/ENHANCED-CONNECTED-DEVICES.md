# Enhanced Connected Devices Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В Р В Р’В Р вЂ™Р’В Р В Р вЂ Р В РІР‚С™Р РЋРІвЂћСћР В Р’В Р В РІР‚В Р В Р’В Р Р†Р вЂљРЎв„ўР В Р Р‹Р РЋРЎв„ў implementation contract

User request accepted 2026-10-09. WR1200JS homepage after login: readable, automatically refreshed device classification without excessive router work. The conservative browser classification core is implemented; collection, homepage integration, refresh and target runtime remain unverified.

## Presentation

A compact homepage section with collapsible network groups: Primary, Guest, IoT (only once that network exists), and Unknown network when attribution is unavailable. Show name, IP, connection/band, RSSI where available, category, confidence and last observation. Network role and physical connection are separate fields. Keep category filters for Android, Windows, Apple, Smart TV and Unknown. Preserve existing network map and settings.

Use text and icons together, not color alone. Apple means manufacturer identified, not an inferred operating system. Distinguish Android TV (TV form factor with possible Android OS) from an Android phone. Provide an explanation on demand and a manual user correction labeled User specified. Never invent exact probability percentages from heuristic scores.

## Evidence and classification

Pinned upstream c25283e915a2a00a763774dd255b14aff997285e already has networkmap/static_ip.inf, device name/type/stale flag, wireless MAC/RSSI and client JavaScript. Existing clients.asp reads lan_clients.asp; its error callback does not schedule recovery. The new component must not depend on that one-shot behavior.

Merge bounded snapshots of current radio associations, neighbor information, DHCP leases and existing networkmap data. DHCP lease existence alone is not current connectivity. Preserve unknown status where evidence cannot establish presence. Separate observation timestamps from HTTP refresh timestamps; fetching cached data must not make old evidence appear current.

Classify using available DHCP hostname, vendor/user class and parameter-request-list evidence, plus locally stored OUI vendor information when the MAC is globally assigned. Collect additional DHCP metadata through a bounded event path only if dnsmasq integration proves it available; it is not supplied by the current client endpoint. Do not use OUI on locally administered/random MACs. Hostnames, vendor classes and fingerprints are spoofable; vendor evidence alone cannot establish OS. Require corroborating evidence for High confidence; single weak hostname clues give Possible or Unknown. Conflicting evidence lowers confidence. Keep vendor, OS, form factor, category and explanatory evidence separate internally.

No continuous port scans, traffic capture daemon, cloud classification or internet OUI lookups. Optional service-discovery enrichment requires separate bounded collection design and must not bypass guest/IoT isolation.

## Refresh and router load

Authenticated bounded JSON endpoint with escaped untrusted names, no script eval and no dynamic HTML insertion of device-provided strings. Cache the router snapshot for approximately 5 seconds across browser sessions. Start with at most 128 records and bounded name/evidence sizes; disclose truncation rather than silently hiding devices.

Browser polls after the prior request completes, approximately every 5 seconds while visible, with a request timeout and retry backoff up to 30 seconds. Pause while hidden; immediately request on return. At most one request in flight. Show Updating, Last observation, Data unavailable/stale and Retry states. Preserve last known rows on errors with a visible stale marker. Restore normal cadence automatically after success. Use no-cache HTTP policy where appropriate and a sequence/timestamp check so old responses cannot replace newer observations. No repeated networkmap restart or full scan on each poll.

Compute lightweight classification and grouping in the browser using a small local ruleset. Router work is bounded snapshot collection/cache and optional DHCP event metadata. Update changed rows using stable identities; do not reset expanded groups, filters or scroll position on refresh. MAC randomization can create a new identity; do not merge devices by name alone.

## Delivery and verification

1. Document source fields and limits; design authenticated JSON schema and conservative rules.
2. Implement bounded snapshot/cache and available DHCP metadata integration without disrupting DNS/DHCP or other networks.
3. Add homepage component, automatic refresh/recovery and local vendor/rules assets.
4. Verify ambiguous/conflicting/random-MAC evidence, missing DHCP names, static-IP clients, duplicate IPs, stale devices, error recovery, hidden tab, multiple browsers, XSS-safe names and bounded response sizes.
5. Verify compiled ROMFS assets/default homepage and device runtime: connect/disconnect transitions, wired/both Wi-Fi bands, guest/IoT attribution, browser reconnection, CPU/RAM/network overhead with representative clients. Record measured load before claiming low overhead.

Schedule in WR1200JS WebUI work, preserving firmware-port and current service-recovery priorities. No live router writes or flashing authorized by this feature request.

## Mandatory automatic refresh and schedule Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В Р В Р’В Р вЂ™Р’В Р В Р вЂ Р В РІР‚С™Р РЋРІвЂћСћР В Р’В Р В РІР‚В Р В Р’В Р Р†Р вЂљРЎв„ўР В Р Р‹Р РЋРЎв„ў clarified 2026-10-09

Implement these device/roaming UI deliverables immediately after the current DNS/DHCP recovery integration and its verification, within the WR1200JS stage and before secondary-router expansion. Both components share a refresh lifecycle. Manual page reload is not an acceptable normal update mechanism: refresh visible data automatically, approximately every 5 seconds, retry after failures, show freshness/error state, preserve filters/expanded groups/scroll, and refresh immediately when a hidden tab becomes visible. One request in flight and a shared bounded cache prevent overlapping or per-browser repeated collection. History recording continues independently of hidden tabs.

Low load is a design goal, not measured evidence. Reuse existing data; do not trigger full scans or networkmap restarts per refresh. Keep classification/rendering in the browser, bounded passive recording/cache on the router and no continual flash writes. Before acceptance compare baseline and enabled CPU, process RSS, request latency and network traffic with identical client counts in idle and loaded conditions and with multiple browser sessions; include collector cost while no UI is open. Check that forwarding/Wi-Fi throughput and latency do not regress. Report actual measurements and tune collection intervals/limits if necessary; do not claim a percentage CPU cost or fixed RAM footprint before measuring.

## Classification core checkpoint

`tools/connected-devices/classify.js` separates category, confidence, manufacturer, OS, form factor and evidence. Hostname or DHCP vendor class alone is only a Possible OS clue; corroborating hostname and vendor-class clues allow High confidence, which is still heuristic and spoofable. Conflicting Android/Windows clues retain Unknown classification. Apple OUI indicates manufacturer only; locally administered or multicast MACs never establish a manufacturer. Manual category overrides are explicitly labeled User specified. Input text is bounded to 128 characters and explanatory evidence to six entries.

The pinned networkmap writer emits six CSV fields: IPv4 address, MAC, device name, legacy type, HTTP flag and stale flag. The existing `lan_clients.asp` returns JavaScript rather than bounded JSON. It does not supply DHCP vendor class or current observation timestamps. Those facts must remain unavailable until the new collector provides evidence; the classification module does not invent them.

Local Node tests pass for ambiguous/conflicting clues, Apple manufacturer/OS separation, random MACs, Android TV form factor, bounded strings and manual correction. This module is not yet included in ROMFS or the homepage. Rendering must use text nodes, and safe JSON, authentication, shared cache, automatic refresh, DHCP metadata, local OUI assets and runtime load measurements still require implementation.

## Refresh lifecycle checkpoint

`tools/connected-devices/refresh.js` implements an abortable single-request lifecycle shared by device and roaming views. It polls after completion at five-second cadence, times out after five seconds, retries failures at 5/10/20/30 seconds, pauses and aborts on hidden-tab notification, and immediately refreshes on return. The caller must connect page visibility events and supply an abortable authenticated transport. Stop invalidates callbacks and removes timers.

Snapshots require a bounded collector epoch, integer sequence and at most 128 device records. Same-epoch older responses are rejected; unchanged cached sequences do not redraw rows or renew source observation timestamps. Collector epoch changes permit a sequence reset. Errors retain the last displayed dataset with a stale state. Rendering callback failure schedules recovery instead of permanently stopping the loop.

Local deterministic Node tests cover overlapping requests, retries/backoff/recovery, hidden pause/resume, delayed callbacks, timeout abort, stale data, collector epoch reset and rendering errors. This is lifecycle code, not homepage integration: the JSON endpoint, collector cache, observation timestamps, DOM rendering and actual browser/router checks remain required.

## Passive networkmap source checkpoint

`tools/connected-devices/networkmap.h` reads the pinned six-field source format without invoking networkmap or initiating a scan. It validates IPv4 and MAC syntax, canonicalizes MAC letter case and reads the final three numeric fields from the right so commas in device names remain part of the name. Limits are 128 retained records, 128 name bytes, 511-byte input chunks and 64 KiB total input. Invalid/oversized/partial records are counted; capacity/input truncation is explicit.

The caller must hold the existing networkmap source lock or supply a consistent snapshot. A source read error invalidates the output. The record exposes the networkmap stale flag without asserting current connection state. No DHCP vendor class, network role or radio observation is invented. Tests cover valid/stale data, comma-containing names, malformed IP/MAC, oversized lines, incomplete tail and record truncation; native sanitizer execution and MIPS compilation run in CI.

This parser is not yet integrated with HTTP. Authenticated bounded JSON emission, source freshness, merging radio/neighbor/DHCP observations, a shared cache and the homepage remain incomplete.

## Bounded JSON checkpoint

`snapshot-json.h` serializes the bounded passive records into caller-owned memory. It exposes the collector epoch and sequence, invalid-record count, truncation and record evidence. It does not invent radio, network role or observation timestamps. JSON strings escape controls, quotes, backslashes and HTML delimiters; valid UTF-8 round-trips through Unicode escapes, invalid/truncated sequences use U+FFFD. Browser sequence values are limited to the exact JavaScript integer range. Insufficient output capacity fails; callers must discard failed output and send only successful results.

The fixtures exercise a 128-record maximum, small output buffers, hostile names, Unicode, emoji and invalid UTF-8, including a Python JSON round-trip. Native sanitizer execution and MIPS compilation are CI gates; the serializer is not an HTTP endpoint or a safe DOM renderer.

The original parser CI directory-order error in ABI 213 was corrected; ABI 214 completed successfully. HTTP authentication, consistent locked input, cache generation and source freshness, radio/neighbor/DHCP merging, automatic homepage integration and runtime measurements remain incomplete.

## Shared RAM cache checkpoint

The pinned `httpd.c` uses a shared select/accept request loop; source inspection found no per-request fork or worker thread. `snapshot-cache.h` is designed for one cache in that process, shared across browser sessions. It invokes the supplied passive collector no more than once per five seconds, including after failures. Read failure preserves the last successful snapshot with Stale status; before any success it reports Unavailable. Recovery restores Current status.

Content equality uses explicit record fields instead of structure padding. Unchanged content keeps its sequence; changed evidence increments it. Collection time is separate from source observation time and is not represented as proof that clients were just seen. The caller must supply a distinct collector/httpd-instance epoch after restart, rather than reusing only a boot ID with reset sequences. Clock rollback expires the cache deadline.

Deterministic C fixtures cover repeated callers, unchanged sequences, failures/stale retention, recovery and instance reset. Native sanitizer execution and MIPS compilation are CI gates. The cache is not yet called by httpd; source locking/authentication, source-age evidence, HTTP status/JSON delivery, radio/neighbor/DHCP merging and homepage integration remain pending.

ABI 215 completed successfully for the preceding JSON serializer and Unicode round-trip tests. Target behavior remains unverified.

## Consistent source collection checkpoint

Pinned `shared/bin_sem_asus.c` implements `file_lock("networkmap")` with an exclusive POSIX `fcntl` lock on `/var/lock/networkmap.lock`; `flock` would not coordinate with it. `source-collector.h` uses the same whole-file POSIX lock with nonblocking `F_SETLK`. Busy acquisition fails promptly so the shared cache can retain its last successful dataset. It does not rewrite/truncate the upstream lock's PID metadata.

The collector opens the source without following symlinks, accepts regular files only, uses the bounded reader and checks source/lock identities before accepting the result. Symlinks and FIFOs fail. Results are copied to the caller only on complete success. Production callers must use fixed internal paths; there is no request-supplied file path.

A forked-process fixture holds the actual POSIX lock while the collector attempts a read, checks unchanged output and stale cache retention, then verifies recovery after release. It also covers lock metadata preservation and source symlink/FIFO rejection. Native sanitizer execution and MIPS compilation are CI gates. ABI 216 succeeded for the preceding shared cache checks. HTTP registration, source-age metadata, radio/neighbor/DHCP merging and homepage wiring still remain to be implemented.
