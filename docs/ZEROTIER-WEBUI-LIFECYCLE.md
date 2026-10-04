# ZeroTier WebUI and service integration

This integration targets WR1200JS on the pinned Linux 4.4.198 base. ZeroTier 1.16.2 source-built image inclusion was verified in run 37173482651. The expanded lifecycle, WebUI and firewall integration requires a new build and device validation.

## Controls and defaults

ZeroTier, router access and routed LAN access are disabled by factory default. The page provides a validated 16-hex Network ID, explicit Leave network, independent router/LAN permissions, and cached node/network status. Authorize the node in the network controller. A controller route to the LAN is required for routed LAN access. The existing NAT setting is retained; masquerading applies only from overlay IPv4 source prefixes toward LAN when LAN access and NAT are both enabled. This policy does not grant overlay transit to WAN or other VPNs.

The status cache is read from a fixed path with bounded input and HTML escaping. HTTP does not execute CLI or read identity secrets. Reload the page to update its displayed cache; the timestamp identifies the sample time.

## Lifecycle and persistence

Start, stop, refresh and explicit membership synchronization share a bounded action lock. The daemon and monitor close inherited lock descriptors. Stop preserves identity, membership, Moon and custom planet files. Only changing or clearing the WebUI-managed Network ID removes the previous marker-managed membership; manually joined network files are preserved. Explicit Leave also applies while the service is disabled. Persistent identity takes precedence over the legacy NVRAM secret; its file mode is restricted.

The background monitor has bounded startup and CLI waits, bounded Moon orbit retries, and PID/start-time ownership checks. It stops polling after a stuck or unidentified CLI worker. Static routes are refreshed when a reachable ZeroTier gateway/interface exists, without waiting for controller authorization. Failed stop or membership synchronization prevents an automatic restart.

Dedicated ZTWR chains are installed before the daemon starts. The four IPv4/IPv6 full/default base filter generators include the same overlay guards inside their own restore transactions. Periodic refresh updates IPv4 NAT prefixes and configured routes. IPv4 and IPv6 transactions remain separate.

## Evidence and remaining work

Local preparation against clean pinned files, Python parsing, shell syntax and page JavaScript syntax passed. Earlier isolated fixtures tested membership changes, scoped rule generation and bounded mock CLI completion. These are not target runtime tests. New CI must compile HTTP/rc changes and verify exact helper assets, controls, compiled guards and defaults in ROMFS.

Device acceptance still requires enable/disable/restart, controller authorization, two-node connectivity, router/LAN permission combinations, firewall restart, address changes, Moon/custom-planet/static routes, and identity/membership restoration after a controlled reboot or upgrade. Storage archive persistence and flash-write behavior still need explicit verification. No remote flashing or reboot is authorized by this integration. Existing upgraded devices must explicitly choose the new router/LAN permission controls; absent new settings do not enable access.
