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
