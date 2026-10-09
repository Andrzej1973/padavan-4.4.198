# Enhanced Connected Devices — implementation contract

User request accepted 2026-10-09. WR1200JS homepage after login: readable, automatically refreshed device classification without excessive router work. Planned, not implemented or runtime verified.

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
