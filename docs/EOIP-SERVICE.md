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

Owned-remove sanitizer CI 38753499644 passed at `ed6ac50`.

## Runtime recovery records increment

`tools/eoip/runtime-state.h` is an uninstalled lifecycle component. It uses a
private owned directory, one nonblocking exclusive lock and close-on-exec lock
descriptor. Per-slot records store a versioned expected interface index and
are replaced atomically. Reads are bounded, canonical, regular-file-only,
owner/permission checked, and reject symlinks. Unknown/corrupt records are not
overwritten; a different recorded index cannot be silently replaced or cleared.
An already absent record can be cleared idempotently. Callers initialize the
state descriptor to -1 and hold the lock through the whole lifecycle action.

Records belong under volatile `/var/run`, not flash. They are recovery identity
for the current boot, not saved user profiles, tunnel liveness or authorization
to delete without a fresh kernel observation. Persistent configuration remains
separate future work. The sanitizer fixture covers lock exclusion, descriptor
flags, record replacement/refusal, corrupt/symlink data and private-directory
checks. Its CI is pending; no firmware packaging or live action was added.

Runtime-record CI 38753942819 passed at `61823de`.

## Lifecycle orchestration increment

`tools/eoip/lifecycle.h` combines the configuration, observation and volatile
records behind adapter callbacks. One lock covers each complete start/stop.
Start refuses every existing interface, clears stale records only after
confirmed absence, creates exclusively, observes identity, saves the index,
configures and checks owned index/admin-up/MTU/master. Failure after a known
creation invokes owned cleanup and an absence postcheck. A failed/unconfirmed
cleanup keeps the recovery record. A missing creation acknowledgement or
unobservable identity is unconfirmed; no interface is adopted or blindly deleted.
Stop uses only slot/record/kernel observation, independent of endpoint fields.

The native fixture uses mock network adapters and real private record files;
it covers whole-action lock exclusion, existing/foreign refusal, index mismatch,
configuration failure/postcheck mismatch, successful rollback and failed cleanup.
CI is pending at introduction. The actual mutation adapters and firmware wiring
are still absent; this is not a working router service yet. Endpoint/ID/keepalive
post-observation and table-level conflicts remain necessary. A missing ACK with
no recorded index can leave an orphan requiring explicit recovery; no automatic
adoption is implemented. Physical identity races remain unverified.

Lifecycle sanitizer CI 38754523227 passed at `7c98c08`. The next observation
increment decodes EoIP local/remote addresses, tunnel ID and both private
keepalive attributes from IFLA_INFO_DATA, with presence bits and size/duplicate
checks. Data is interpreted only after the kind is known to be `eoip`, so
foreign bridge attributes are not misread as EoIP fields; DATA-before-KIND is
supported. Address/ID words preserve the pinned module/tool's raw netlink
representation; the one-byte retry field is widened explicitly. A fixture
asserts agreement with the pinned private attribute IDs 32/33.

Lifecycle postchecks now require all five fields and exact requested values,
in addition to index/admin-up/MTU/master. Missing/mismatched fields trigger
cleanup rather than profile success. Tests include nested parameter decoding,
foreign kinds and a tunnel-ID mismatch rollback. CI/full build of this change
are pending; no real configuration adapter or router activation was added.

## Owned configuration increment

`tools/eoip/configure.h` applies MTU, admin state and one explicit bridge master
to an interface that was already observed as owned. Every call re-observes the
interface by name and refuses unless the kernel still reports the requested
ownership alias, `kind=eoip` and the expected interface index, so a name reused
by another interface is never reconfigured. A bridge candidate must exist,
report `kind=bridge`, have a valid index and differ from the interface itself.
An empty bridge is the only way to request no master, and an interface that
already has a master is refused rather than detached. When the requested state
is already present the adapter sends nothing.

The change is one bounded RTM_NEWLINK that addresses the interface by index
only: admin-up flags plus IFLA_MTU and, when requested, IFLA_MASTER. A kernel
acknowledgement is accepted only for a zero-error echo of that exact sequence
from port 0; permission errors, timeouts, truncation and a different sequence
stay failures. A second observation must confirm index, ownership, MTU, admin
state and master before the call reports success, so an unacknowledged or
unverified change is never treated as configured.

The sanitizer fixture drives the adapter through mock observation and transport
callbacks: already-configured no-op, MTU change, bridge attach, foreign
interface and index mismatch refusal, absent or non-bridge bridge candidates,
implicit detach refusal, transport failure, unconfirmed post-state and
malformed requests. It also exercises the real socket transport against an
unknown interface index, which cannot mutate an interface. The test creates,
modifies and removes no interface. This is still not a service controller:
firmware wiring, table persistence, boot policy and the WebUI remain absent.

Configuration CI 38772832369 passed at `2211bf0`; the first run of the fixture
(38772632919) failed because the mock transport applied the change while
reporting failure, which hid the unconfirmed-post-state path. The adapter
itself refused correctly; only the fixture changed.

## Managed controller increment

`tools/eoip/controller.h` maps one slot to its fixed interface name
`wr-eoip<slot>` and ownership alias `wr-eoip:<slot>:v1`, and implements the four
lifecycle operations against the kernel. The netlink transport is injected, so
the same controller code runs behind a test transport and, in firmware, behind
the daemon's socket; nothing in the controller opens a socket of its own except
the optional generic transport it also provides.

Creation sends one exclusive RTM_NEWLINK in which the name, the ownership
alias, `IFLA_INFO_KIND=eoip` and every tunnel parameter travel together, so no
window exists in which an unowned interface carries a managed name. Deletion
addresses only an index that a fresh observation confirmed as owned and equal
to the expected index; an already absent interface is an idempotent success and
an unknown or foreign one is refused. Acknowledged requests are accepted only
for a zero-error echo of the echoed message type and the same sequence, and the
generic transport reads that type back from the request it sends.

The fixture drives the controller through the real lifecycle orchestration with
only the kernel transport mocked: slot mapping for all eight slots and the
out-of-range refusal, the full attribute layout of the create request (name,
alias, kind, tunnel id, both addresses, keepalive interval and retries), the
delete request, the complete create-observe-record-configure-verify path, a
foreign interface holding the managed name, an index that no longer matches the
record, an absent interface, and missing transport or output arguments. It also
sends a real delete for an unknown index over a real socket, which cannot
mutate an interface.

Controller CI 38775647354 passed at `22b83b3`.

## Service worker increment

`tools/eoip/worker.c` is the service entry point: one command performs one
complete action for one slot.

- `start SLOT ENABLED AUTOSTART LOCAL REMOTE ID MTU KEEPALIVE RETRIES BRIDGE`
  validates the profile with the configuration validator and then drives the
  lifecycle. A profile whose ENABLED field is not 1 is not "started off": the
  slot is stopped through the same verified cleanup path, so a half created
  interface is never left behind.
- `stop SLOT` performs cleanup only. It needs no endpoint, MTU or keepalive
  field, so it still works after a stored profile became invalid.
- `status SLOT` reports the observed state: absent, owned with index, MTU,
  master and admin state, a name held by a foreign interface, or unknown.

Result codes stay separated (usage 64, invalid profile 65, refused 66,
unconfirmed 67, rolled back 68) so a caller can tell "did nothing" from "did
something and could not confirm it". Messages carry no credentials.

The transport is injected: the fixture drives every path with a mock transport
while `main` supplies the socket transport and takes the state directory from
`WR_EOIP_STATE_DIR`, defaulting to `/var/run/wr-eoip`. The integrated package now
also builds the worker: `integrate-eoip.py` copies the validator, controller,
lifecycle, runtime-record and observer headers, adds `eoip-service` to the
package Makefile and installs it to `/usr/bin/eoip-service`.

Service CI 38776427458 compiled and ran the fixture
(`PASS EoIP worker: usage, profile validation, start, status, disable cleanup,
foreign and unknown refusal`) and also built the standalone binary, whose real
read-only query answered `slot absent 0`. A local fixture run of
`integrate-eoip.py` produced the package with the worker, the Makefile targets
and a complete quoted-include closure.

The first full firmware build with the packaged worker (288, at the previous
commit) failed on the target toolchain: the uClibc sysroot's
`linux/if_tunnel.h` expects `IFNAMSIZ` and `struct iphdr` to have been included
by the translation unit. `net/if.h` and `linux/ip.h` now precede that header in
`observation.h`, and `configure.h` takes `IFF_UP` from `net/if.h`. Full build 289
(commit `cc140d3`) completed successfully, so `eoip-service` compiles for
MIPS/uClibc and is packaged into the firmware. This is compilation evidence
only: no EoIP interface has been created on any router.

## Required next work

Apply notification preparation: the selected-profile generator now declares
`RCN_APPLY_EOIP` as `apply_eoip` and adds its own guarded rc notification branch
calling the EoIP policy's `apply` action. It uses no General Apply bit and does
not reuse restart_vpn, restart_netfilter or another service's notification.
This is the receiver only: no HTTP settings writer/sender is exposed yet.
Changes are prepared together before generator writes, including rc.c and the
notification header. Target compilation of this increment remains pending.

Local verification on 2026-10-15 used exact pinned-source files from
`c25283e915a2a00a763774dd255b14aff997285e`: default schema and independent rc
handler preparation succeeded. Separately, EoIP page preparation succeeded on
the pinned services page/dictionaries, all page WREOIP keys were present in
EN/UK/RU, and Node accepted the extracted inline JavaScript syntax. Fixtures
are local under guide-stage and are not delivery files. This does not execute
the real HTTP session or validate rendered browser layout.

Read-only page integration: selected builds install
`Advanced_Services_EoIP.asp`, linked from Administration/Services, and the
status view asset with EN/UK/RU labels. Initial loading and manual refresh use
the authenticated EJ source. Initial unavailable/pending collection is retried
with a bounded 25-second request deadline (one in-flight AJAX timeout may add
up to five seconds); hidden-page requests stop. No recurring polling timer is
installed. Explanations explicitly distinguish IFF_UP from peer/frame health
and state that editing is not connected. This delivers the observation page,
not the required full EoIP configuration interface.

Image checks now require the installed page, navigation link, matching JS and
UK/RU labels. These page/image changes have not yet completed a full build or
browser/device validation. Background status CI 38785515921 passed at
`be3ae98`, including the native read-only worker collection/cancellation test.

HTTP status integration increment: selected WR1200JS EoIP builds now run
`prepare-status.py` after the VPN status generator. It registers authenticated
EJ output `wr_eoip_status` through existing update.cgi and hooks background tick
and shutdown. The request starts at most one read-only child; only that child
performs eight bounded netlink queries. HTTP uses a nonblocking pipe and
WNOHANG for its own PID. Inherited HTTP descriptors are closed in the child,
stdio is redirected to /dev/null, and timeout cancels after 20 seconds on ticks.
There are no shell commands, interface mutations, NVRAM writes or disk cache.

Observations are sampled on demand, reused for 10 seconds, and rejected after
60 seconds or monotonic-clock rollback. First request may return
source_unavailable with pending=true; consumers must retry manually or with a
bounded completion mechanism, not display success. A valid response includes
sample_age and pending; UI parsing now rejects out-of-range sample ages.
Rows marked up still mean IFF_UP only. Failed collection invalidates the cache.
No persistent background polling is scheduled. Shutdown does not block waiting
for a child; init inherits a killed child not yet reapable at process exit.

CI now compiles/runs `check-status-runtime.c` for real read-only netlink sampling,
single-child refusal and cancellation. These new runtime and HTTP integrations
have not yet completed CI or target compilation. The actual page and its
authenticated settings writer remain unfinished.

Web status view candidate: `tools/eoip/status-view.js` validates schema 1 and
exactly eight unique slots, bounds numeric observations and rejects unknown
state labels. It renders with DOM textContent and provides a single-flight
manual refresh helper; failed/invalid refresh clears previous observations.
There is no periodic timer or automatic action. Local Node model checks passed
on 2026-10-15 for schema, uniqueness, numeric fields, parallel refusal and error
clearing; full browser rendering is not verified. The asset is not yet installed
or attached to an HTTP status source/page, so no finished WebUI is claimed.
The same check is now wired into service CI. Shell-policy CI 38784871587 passed
on `2c1f7fb`, including the isolated mocked boot/apply/stop scenarios.

Offline shell-policy coverage is now wired into service CI through
`tools/eoip/check-policy.py`: default-off no-op, profile-independent full stop,
disabled Apply, invalid master, NVRAM failures before mutation, full eight-slot
quoted argv, literal shell metacharacters and module-loading failure. It runs
an isolated copy under `/bin/sh` with mocked nvram, modprobe and worker; it does
not operate on real interfaces or validate target BusyBox behavior. Execution
of this new check is pending CI. Apply still needs an authenticated integration
that coordinates NVRAM writes; no spare event bit should be assumed and no VPN
service should be restarted as a side effect merely to reuse its event.

Table application increment: `apply-table` validates every enabled profile and
duplicate tuple before touching interfaces, then cleans all managed slots and
starts enabled profiles regardless of autostart. Boot still starts only enabled
autostart profiles. Any cleanup failure prevents all new starts and is reported
as incomplete (earlier cleanup is not rolled back). Starts can also partially
succeed; this is not an atomic network transaction. `stop-table` takes no
profile arguments and holds the operation lock across all eight cleanup calls.

The installed policy now supports `apply`; master=0/empty uses stop-table,
master=1 reads the complete table then invokes apply-table, invalid master
flags refuse. Stop never reads NVRAM. No HTTP action or NVRAM writer is exposed
by this increment; authenticated WebUI and coordination of writes/snapshot
reads remain required. Fixture cases were extended for empty Apply, conflict
refusal before deletion and unknown-state stop-table; execution is pending CI.

The generated model guide now includes EoIP setup prerequisites, no-registration
clarification, slot fields/defaults, GRE protocol vs port distinction, bridge
and MTU checks, read-only status commands and explicit limits of runtime
evidence. The same catalog text is reflected in `docs/setup/WR1200JS.md` and
will enter the generated SETUP text when EoIP is selected. The official
MikroTik page was read on 2026-10-15; RouterOS-only features are explicitly not
claimed as implemented by this controller. CI 38784233558 succeeded for
`50dac14`; full build 38784233580 remained running at inspection. The older
full build 38783698201 was verified still in the firmware compilation step,
not presumed hung and not restarted. Guide changes do not prove device behavior.

Structured runtime observation: `eoip-service status-json` now returns schema 1
with eight slot observations. States are `absent`, `unknown`, `foreign`, `up`
or `down`; up/down are only the owned interface's IFF_UP flag. Owned observations
include ifindex, MTU and master. No endpoint, alias, credentials or arbitrary
kernel strings are emitted. A valid JSON response can contain unknown slots;
successful serialization does not establish tunnel health, keepalive success,
peer reachability or frame transfer. The read-only command bypasses operation
locking and has no NVRAM/flash writes. Individual netlink queries are sequential,
so this is not an atomic kernel snapshot. WebUI integration remains pending.
The fixture includes owned-up and unknown serialization paths; its new version
has not yet run. Service CI 38784060437 succeeded on `ca67932`; full build
38784060440 was in progress when inspected. No device acceptance is claimed.

Follow-up: disabled single-slot start now bypasses endpoint/MTU validation and
uses only a validated slot and disabled flag for cleanup, matching the stop
contract. Fixture coverage includes disabling a running slot with corrupt
endpoint/MTU values, an entirely disabled table with empty endpoints, and
enabled duplicate tuples refused before create. Updated tests await CI.

Full build push triggers now include all `tools/eoip/**` inputs, fixing the
missing rebuild on worker/controller-only changes. Image checks now require the
MIPS/uClibc worker, boot-table command, exact executable boot script, disabled
defaults and RC boot/stop calls. CI 38783883607 passed on `f47e10c`; those earlier
checks do not establish the new coverage or physical behavior.

Managed worker mutations now hold a private `operation-lock` across an entire
start, stop or boot-table command. This is separate from the lifecycle registry
lock, avoiding recursive flock acquisition while preventing two managed worker
commands from interleaving slots of a table. Busy commands refuse without
mutation; read-only status does not acquire this lock. Lock files use the same
owner, permissions, no-symlink and close-on-exec checks as registry locks.
The worker fixture now includes contention refusal and cleans up both files;
execution of the updated fixture is pending CI. Legacy eoip-ctl and external
netlink writers do not participate in this lock. NVRAM snapshots still need
coordination with future WebUI Apply writes.

CI 38783698084 passed for `f2f2719`; full build 38783698201 was still running
when inspected. These results do not cover the new operation-lock increment.

Boot/shutdown integration increment: `prepare-defaults.py` now also adds
APP_EOIP-guarded RC calls after the existing iPerf3 startup/shutdown anchors.
The package installs executable `/usr/bin/wr-eoip-boot`. Disabled master at boot
returns without kernel operations or runtime files; enabled boot loads `eoip`
and submits the full snapshot to the worker. Stop visits all managed slots
without reading NVRAM, does not unload the shared module, and reports incomplete
cleanup. RC logs failures but does not restart or reconfigure other services.
Generator anchor checks are completed before writing its files.

Service CI 38783437373 passed at `fd3b029`; full build 38783437472 was still
in progress when inspected. Those results predate these new RC/package hooks.
Target compilation, boot order on the device, persistence across reboot,
snapshot serialization against future Apply, and WebUI remain unverified or
unfinished. No router changes were performed.

The worker now accepts `boot-table` with exactly eight ten-field profiles.
It validates all enabled profiles and tuple uniqueness before any start; empty
endpoints of disabled slots are allowed. Only enabled autostart slots are then
started, using the existing ownership lifecycle. Per-slot failures are reported
as an incomplete boot table; successful earlier starts are not rolled back.
The candidate boot script collects all fields into quoted argv before calling
this command, rather than starting while reading NVRAM. These reads are not an
atomic NVRAM transaction; integration must serialize against Apply. Whole-table
runtime locking, module loading and RC hooks remain unfinished. This code has
not yet been compiled or exercised on the target.

`tools/eoip/table.h` now defines requested-table uniqueness: slots must be
distinct and enabled profiles must not share local/remote/tunnel-id tuples.
The identity follows `eoip_tunnel_find` in the pinned module: managed tunnels
use the same link=0 and Ethernet type. MTU or bridge differences therefore do
not make duplicate tuples valid. The helper expects individually validated
profiles and is not yet wired into boot or Apply. No execution test is claimed.

The build now invokes `tools/eoip/prepare-defaults.py` for selected EoIP
profiles. It adds the compile selector APP_EOIP, a disabled master switch and
eight disabled slot profiles to the firmware defaults table. Remote addresses
and bridge assignments start empty; MTU defaults to 1458 (not a measurement of
the actual path). No boot hook or WebUI apply event is enabled by this step.
Existing stored values are not migrated or overwritten by this generator;
physical backup/restore and persistence still require acceptance testing.
Compilation of this increment has not yet been confirmed.

Execution resumed by Sol on 2026-10-15 after the user's explicit role transfer.
`tools/eoip/boot.sh` is an **uninstalled candidate** for the NVRAM boot policy.
It starts only slots with master, slot enable and autostart exactly `1`, passes
fields as separate arguments to the validating worker, and aggregates failures.
Explicit stop does not read NVRAM and needs no valid endpoint. No NVRAM writes,
flash saves, firewall or route changes are performed by the policy. Existing
interfaces are subject to the worker's refusal rules; this is not an Apply or
restart implementation. Defaults generation, module loading, cross-slot
conflict checks, boot/RC integration and target-shell verification remain open.
This candidate has not been executed on a router or packaged into an image.

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
