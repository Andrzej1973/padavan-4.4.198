# EoIP managed-service port

The active WR1200JS profile already selects EoIP. The existing integration
packages the IPv4 `eoip.ko` module and `eoip-ctl`; build 283 predates the new
configuration validator below. Packaging is not tunnel operation.

The accepted service scope remains a tunnel table, endpoint/ID/MTU settings,
optional bridge assignment, enable/autostart, lifecycle and actual status.
Existing tunnels/interfaces must be preserved. No tunnel or bridge assignment
is created by this work on the live router.

## Configuration validation increment

`tools/eoip/config.h` validates requested profiles without side effects:

- Eight managed slots, decimal booleans and tunnel IDs 0..65535.
- IPv4 endpoints: local `0.0.0.0` allows automatic source selection; remote
  must be unicast. Unspecified, loopback, multicast/reserved remote ranges,
  IPv6 and equal explicit local/remote endpoints are rejected.
- MTU 68..65486 follows the current IPv4 module's change-MTU ceiling:
  `0xFFF8 - hard_header_len - tunnel->hlen`, with Ethernet 14 and IPv4/EoIP
  headers 20+8. This upper bound does not establish usable path MTU or jumbo
  frame performance; that requires route/path checks and physical validation.
- Keepalive 0..3600 and retries 0..255 match `eoip_proto.h`. Disabled
  keepalive normalizes retries to zero.
- Empty optional bridge or a bounded interface-name syntax. Bridge existence,
  ownership, topology and loop safety are not inferred from a valid name.

The validator is not yet installed in firmware or connected to HTTP/RC.
`tools/eoip/check-config.c` exercises boundaries and malformed inputs under
native ASan/UBSan in service CI; execution is pending at introduction.
On validation failure the output is cleared, never a partially trusted config.

The configuration sanitizer CI, run 38751553924 at `7d5140b`, passed.

## Interface observation increment

`tools/eoip/observation.h` decodes one bounded RTM_NEWLINK record. It checks
lengths, request sequence, expected interface name, attribute alignment and
duplicate known attributes without dereferencing unaligned structures. It
observes the interface index, flags, MTU, bridge master, kind and alias.
Only matching `kind=eoip` and the requested ownership alias mark a record as
owned; a same-named bridge or foreign alias remains foreign. Malformed input
clears the observation. Flags are not a claim of peer reachability or traffic.

The native sanitizer fixture covers owned/foreign records, unaligned input,
sequence/name mismatch, truncation, duplicate attributes and invalid lengths.
Its CI is pending. This decoder is not installed or connected to a netlink
socket yet. The transport must separately verify kernel sender identity,
receive truncation/errors and request/reply handling. Lifecycle must also
recheck identity before a mutation; this observation alone is not an atomic
ownership lock or authorization to delete an interface.

## Required next work

Implement owned-interface start/stop and cleanup, safe disabled defaults,
persistent table/backup behavior, conflict checks across the table and actual
interface-kind/parameter observations. Stop must remain possible even when
stored endpoint fields are invalid; do not gate cleanup on full-profile
validation. Optional bridge assignment must be explicit and preserve unrelated
LAN/VPN/WAN interfaces. No default-route or firewall changes should be inferred
from a tunnel profile. Translate the service UI and expand the model guide.

Physical acceptance needs a compatible remote endpoint and supervised tests:
creation/deletion, real frame transfer, MTU, optional keepalive behavior,
isolation, settings persistence and recovery. No physical acceptance is claimed.
