# Wi-Fi Roaming Monitor

User-approved WR1200JS feature, 2026-10-09. Planned, not implemented or runtime verified. Integrate with Enhanced Connected Devices on the homepage and provide a detailed monitor page.

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
