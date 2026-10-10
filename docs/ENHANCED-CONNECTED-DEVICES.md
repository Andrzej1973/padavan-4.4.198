# Enhanced Connected Devices Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В Р В Р’В Р вЂ™Р’В Р В Р вЂ Р В РІР‚С™Р вЂ™Р’В Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В Р В Р’В Р В РІР‚В Р В Р’В Р Р†Р вЂљРЎв„ўР В Р Р‹Р Р†РІР‚С›РЎС›Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В Р В Р’В Р вЂ™Р’В Р В Р вЂ Р В РІР‚С™Р РЋРІвЂћСћР В Р’В Р В Р вЂ№Р В Р Р‹Р РЋРІвЂћСћ implementation contract

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

## Mandatory automatic refresh and schedule Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В Р В Р’В Р вЂ™Р’В Р В Р вЂ Р В РІР‚С™Р вЂ™Р’В Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В Р В Р’В Р В РІР‚В Р В Р’В Р Р†Р вЂљРЎв„ўР В Р Р‹Р Р†РІР‚С›РЎС›Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В Р В Р’В Р вЂ™Р’В Р В Р вЂ Р В РІР‚С™Р РЋРІвЂћСћР В Р’В Р В Р вЂ№Р В Р Р‹Р РЋРІвЂћСћ clarified 2026-10-09

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

## HTTP integration checkpoint

`prepare-http.py` installs a WR1200JS-only `wr_devices.json` MIME route with `application/json`, the existing no-cache headers and `need_auth=1`. The pinned httpd checks external requests through `auth_check` before invoking such handlers; its existing localhost exception is unchanged. The handler does not read user-supplied paths or invoke scanning, NVRAM mutation or service commands.

A single process RAM cache is shared by requests. Its instance epoch uses PID and initialization time so an httpd restart can reset sequence independently of the router boot. Responses include cache state, collection age and the source file's update time. Source update is not a per-client last-seen timestamp or proof of current connectivity. Source-age changes are evidence changes for the snapshot sequence. Initial collection failure returns an error object; later failures return the last snapshot marked stale. Browser refresh now respects the server stale state.

Standalone HTTP fixtures check valid JSON, escaped names, cache reuse, source-failure retention and source update metadata. Preparation was applied to the actual pinned `web_ex.c` locally; the generated route has `need_auth=1`. CI compiles native/MIPS fixtures and checks generated route registration. The full firmware workflow now prepares this hook after shared-Wi-Fi integration. Full httpd linking and live HTTP authentication remain unverified until the new full build/device checks complete.

ABI 217 succeeded for the preceding nonblocking source collector and cache-composition checks. No homepage assets are installed yet, and the new endpoint still only contains networkmap evidence. Radio/neighbor/DHCP merging, vendor-class/OUI evidence, connect/disconnect behavior, homepage rendering and roaming history remain required.


## Homepage integration checkpoint

ABI 218 and full firmware build 121 succeeded at commit `e92f83ceff9e33dbef3d2d7590a1ef2a96d798e3`, confirming the HTTP integration compiles. Live authentication and target behavior remain unverified.

The WR1200JS preparation now installs a connected-device section above the existing homepage network map, together with classification, polling and presentation assets. The existing homepage content is preserved. Rows show address, category, confidence and evidence; unknown network roles remain explicitly unidentified. This source currently only supplies networkmap observations, so it cannot prove current association or primary/guest/IoT membership. Classification remains a heuristic, not a reliable operating-system identification.

Polling uses authenticated same-origin JSON requests, one active request, five-second cadence, bounded response size, retry backoff and a stale-data indication. Hidden pages pause polling. Rendering uses text nodes for device names and preserves row identity, filters, expanded groups and scroll position. It does not scan clients or write flash.

Node fixtures cover these DOM/transport contracts with a simulated DOM. A separate preparation fixture uses the actual pinned `index.asp`, verifies the original content is preserved, checks installed asset bytes/order and rejects repeated preparation. These checks do not prove real browser rendering, ROMFS installation or router runtime. The next full build must verify the new homepage assets. Localization, manual category editing, radio/neighbor/DHCP merging, OUI metadata, roaming history and measured target load remain unfinished.

The source preparation gate also verifies the pinned UTF-8 homepage and authenticated JavaScript/static CSS MIME routes. Scripts contain no EJ template markers. The five installed assets total 14,165 raw bytes; this is not a measured compressed TRX increase. Browser compatibility and router CPU/RAM measurements remain pending.


## Browser verification checkpoint

A local browser fixture using the actual presentation/classification/refresh scripts and synthetic networkmap observations exposed corrupted literal icon/separator encoding. Commit `9e8f49b2cc14a946b3d27f0c32f463e3833c0f92` replaces these literals with ASCII Unicode escapes and adds an ASCII-source regression check. Reloading the fixture displayed the Android/unknown icons and separators correctly.

The browser displayed hostile HTML-like names as literal text. Selecting Android filtered the unknown row; automatic source-time updates continued while the selected category remained Android. This fixture uses simplified CSS and a local mock endpoint, so it does not establish integration with the full Padavan page, real authentication, wireless association or target CPU/RAM use. The corrected assets now total 14,274 raw bytes; the earlier 14,165-byte measurement precedes the encoding fix.

ABI 221 succeeded for the preceding source/ROMFS-gate commit. Full build 123 is still compiling; its staged ROMFS verification and final image are not yet confirmed. Device validation remains required.


## Wireless evidence source checkpoint

Inspection of pinned source `c25283e915a2a00a763774dd255b14aff997285e` found the existing `ej_wl_auth_list` in `trunk/user/httpd/ralink.c`. For the normal dual-radio path it queries each main radio with `RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT`; this is a station-table query, not the separate active scan routine. `shared/include/ralink_priv.h` defines each entry's MAC, `ApIdx`, three RSSI values and connected time. The existing helper chooses the strongest nonzero RSSI among the configured receive streams.

The current JavaScript-oriented authentication list loses band and BSS identity. It must not be parsed or evaluated as the new JSON source. A bounded collector should retain band and `ApIdx`, reject impossible counts/lengths, distinguish failed radio queries from a successful empty table, and merge by MAC with networkmap records. The original reader uses a 4096-byte buffer and loops to the returned count; copying that loop without independent bounds validation would be inappropriate. Driver-side structure/word-size agreement and WR-specific BSS mapping must be verified before treating entries as current association or network-role evidence. The IoT BSS remains unactivated, so an assumed third BSS is not proof of a working IoT network.

This establishes a source integration direction only. The radio collector, JSON fields, merge tests and target verification are not implemented yet.
