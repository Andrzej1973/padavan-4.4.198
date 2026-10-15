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

Observation CI 38752028099 passed at `1916f15`.

## Read-only netlink transport increment

`tools/eoip/netlink-query.h` sends only RTM_GETLINK on a fresh NETLINK_ROUTE
socket, without multicast subscriptions, and sets one-second send/receive
timeouts. It validates kernel sender port 0, sender address size/family,
datagram truncation, response sequence and length. Only matching kernel
ENODEV/ENOENT replies establish absence; permission failures, timeouts and
other errors remain unknown. A present foreign interface remains distinct
from an owned EoIP interface. Socket descriptors are closed on all paths.

The native sanitizer test includes real read-only queries for loopback and a
nonexistent interface in the Linux CI runner, plus synthetic origin/error/
truncation cases. This performs no interface creation, modification or removal.
Execution is pending at introduction. These native observations do not prove
MIPS/uClibc operation or a physical router's EoIP support. The transport is not
installed in firmware yet and must run in a supervised service worker, not
synchronously in the HTTP request loop. Start/stop and persistence remain open.

Netlink query CI 38752406828 passed at `ff38cd6`, including the real read-only
Linux runner queries.

## Owned creation increment

The existing `eoip-ctl` now accepts optional `owner wr-eoip:<slot>:v1` only for
exclusive IPv4 `add name wr-eoip<slot>` (slots 0..7). It places IFLA_IFALIAS
in the same RTM_NEWLINK request as the name, tunnel parameters and `eoip` kind.
The tool no longer needs a second command to attach this ownership marker.
`set` cannot use this option to claim an existing interface. Foreign names,
mismatched slots, malformed/duplicate owners and IPv6 owned creation are
rejected before netlink. Legacy commands without the owner option remain.
Name and kind attributes now include their terminating NUL.

A sanitizer fixture wraps netlink open/talk/close, inspects the actual CLI's
request and tests rejection/send failure. It creates no real interface.
CI and full firmware compilation are pending at introduction. This is the
creation primitive, not a completed manager: owned cleanup, parameter/status
comparison, table persistence, boot policy and WebUI remain open. Atomic
request construction does not prove kernel rollback or runtime ownership races.

Owned-create sanitizer CI 38752941074 passed at `e297cf3`; its full firmware
build was still active when the next increment began.

## Owned removal increment

`eoip-ctl owned-remove SLOT EXPECTED_IFINDEX` queries the fixed managed name
and alias, refuses unknown/foreign/index-mismatched observations, and sends
RTM_DELLINK by the verified index. Confirmed absence is an idempotent success.
After a successful delete acknowledgement it queries again; only confirmed
absence is success, while present/unknown becomes unconfirmed. Cleanup does
not depend on valid saved endpoint or MTU fields. The legacy `remove name`
command remains unchanged and is not the manager's cleanup primitive.

The tool package now copies the query/observation headers and tracks their
object dependencies. The optional MIPS candidate compile uses the same headers.
A wrapped-transport sanitizer fixture exercises owned removal, refusal,
send failure and the postcheck without deleting a real interface. CI/full
compilation are pending. This is not an atomic compare-and-delete operation:
kernel identity changes between query and deletion remain a runtime race.
The higher-level manager must serialize its own actions and preserve its
recorded identity; table lifecycle/persistence/WebUI are not implemented yet.

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
