# WR1200JS separate IoT Wi-Fi implementation contract

## Auxiliary retry scheduler — 2026-10-31

The isolated APCLI/Monitor close path now has a host-tested scheduler binding:
only a proven-unmutated `WR_FAMILY_DOWN_RETRY` is queued, `dev_hold` precedes
submission, the original ndo_open module pin is retained, the exact ticket is
completed under the adapter transition lock before reuse/release, and the
worker invokes only the family-specific retry under RTNL. Adapter release
requires an empty deferred count and a non-busy auxiliary work item. PCI probe
and remove paths join or flush the work.

Candidate82 passed86 extracted host variants; a fresh whole-chain reproduction
is byte-identical and passed6 focused replay variants. Failed/canceled work is
retained and blocks release; there is no reaper. MIPS compilation, callback/
timer/DMA quiescence, final child/root/PCI release and device runtime remain
open. Evidence:
`evidence/WR1200JS-IOT-AUX-RETRY82-2026-10-31.md`.

## RC shutdown admission gate — 2026-10-29

The isolated `activation.h` backend now requires `cancel_requested` and polls
it immediately after LOCK, before each START operation, and after final
observation. A request aborts
START through the existing recovery sequence; failure to prove recovery keeps
the owner lock, snapshot and isolation. The host fixture covers cancellation
after radio preparation and after BSS observation, plus a failed recovery.
The callback still needs a real RC/driver binding. Each backend operation,
including recovery, must be bounded or cooperatively cancellable; polling
between operations alone cannot guarantee a timely reboot. SIGPWR and process
faults retain the immediate stock path and require fail-closed boot recovery.
The host fixture additionally injects SIGTERM after RADIO_PREPARE through
the RC marker and verifies that a callback reading that marker prevents
`BSS_UP`; this remains a model, not a source or device integration.

The prepared RC's SIGUSR1 notification loop is sequential, but its fatal
signal handler directly invokes `shutdown_router()` and can interrupt an IoT
activation. Normal shutdown signals SIGTERM and SIGQUIT and the separate
SIGPWR path must be accounted for before binding the production backend.
The same signal list also includes process faults (for example SIGSEGV and
SIGBUS); do not mask those merely to make activation appear serialized.
Choose a bounded, fail-closed shutdown admission/cancellation protocol that
preserves a working reboot and retains quarantine on uncertain teardown.
Verify the exact generated RC path and the driver transition owner together.
One PID 1 control worker, a mailbox RUNNING record, or a short signal mask
alone is not this proof. Source detail:
`docs/evidence/WR1200JS-IOT-RC-SIGNAL-OWNERSHIP-2026-10-29.md`.

## Shared UP/DOWN ticket coverage — 2026-10-24

### Common ioctl identity gap (source check 2026-10-24)

In the staged MT76x3 source, `include/rt_os_net.h` constructs
`RT_CMD_INF_UP_DOWN` from only `rt28xx_open` and `rt28xx_close` and calls
`RTMP_COM_IoctlHandle` with adapter and that structure. The structure in
`include/rtmp_cmd.h` has only those two function pointers. The common cases
in `common/cmm_cfg.c` therefore receive no netdev, family or registration
generation; they can mutate `VirtualIfCnt` but cannot validate that the
caller still owns the particular interface after unlocked work. The DOWN
wrapper also returns `VOID`, hiding dispatcher failure from every stop hook.

Before binding the shared transition owner, extend the private UP/DOWN
request and all five call families together to carry a pinned interface
identity/generation and a checked result. Acquire the adapter owner before
the count/readiness decision, validate the same generation at the mutation
boundary, and retain the ticket through checked completion or rollback.
Do not infer identity from `pAd->net_dev`: that is the primary device even
when AP-client, WDS or MBSS invoked the ioctl. Do not change the two-field
structure alone while old callers remain, or treat converting `VOID` to
`INT` as proof of physical teardown: legacy `rt28xx_close` reports zero on
unverified paths. This is an ABI/source requirement for the isolated
candidate, not a production implementation or runtime result.

The repeatable caller gate is `tools/iot/check-virtual-if-call-coverage.py`.
Run it on each newly staged MT76x3 driver tree before changing the request
ABI; it fails when any of the five caller files or their UP/DOWN counts drift.
On the `reserved-removal-20261024/driver` stage it found exactly one UP and
one DOWN per family and printed the existing two-callback request fields.
This gate measures source coverage only; it does not certify the future
identity/ownership implementation.

The candidate registry now exposes `wr_iot_registry_find_openable` under the
existing adapter lock. It returns a published, non-removing, IDLE record with
a nonzero generation; MBSS admission uses it instead of its own lookup loop.
The generation can be captured from that record for the future common request
and checked again by `wr_iot_registry_find` at dispatch. This is a shared
registry primitive, not a second ownership ledger. Strict host registry and
composed MBSS admission fixtures passed on 2026-10-24. The common request and
other four caller families are still unchanged, so there is no all-family
ownership guarantee yet.

The isolated MBSS checked-close helper now requires the caller's pinned
registration generation and uses `wr_iot_registry_find` before any close
mutation. A zero or stale generation is rejected before CR disable, queue
stop, virtual-down or module-reference release. This prevents a retry for an
old registration from claiming a newly reused slot at entry. The caller that
begins CLOSE/BSS_CLOSE must still carry that generation through the whole
operation; the production netdev stop hook is not bound, and unlocked vendor
work still requires the shared owner/lifetime proof. Strict host checks of
the direct helper, combined open/close/down and last-close physical chain
passed after updating the extracted fixtures to the current source shape.

Follow-up: after each unlocked MBSS vendor/queue/virtual-down step, the
candidate now rechecks the same `(device, generation, close serial)` record
and active radio ticket under the adapter lock before writing the next close
stage or consuming the reference. The uncertainty path also refuses to mark a
newly reused record as failed. A host fixture injects generation reuse during
`MBSS_Close` and confirms the old operation stops without touching the new
record or decrementing its module reference; direct and both composed strict
C11 fixtures passed. This fail-closed check does not make slot reuse safe
while vendor work is in flight: actual unregister, callbacks and lifetimes
still require the shared owner and a proved quiescence barrier.

The isolated `wr_iot_mbss_begin_close` now captures the OWNED registry
generation and starts CLOSE/BSS_CLOSE from the same adapter-lock critical
section as the active-interface count read. It rejects unpublished records,
zero count and competing active tickets, returning no generation on failure.
Retries keep the original generation and ticket rather than starting another
close. Direct and composed host fixtures passed. This removes the candidate's
read-to-reserve gap for MBSS but remains unbound to `ndo_stop`; every other
family must join the same owner before the shared count is safe.

Pinned source and current isolated assembler show five families behind the
same virtual-interface count. Main open receives a candidate radio ticket in
`prepare-radio-adapter-candidate.py`; MBSS open receives BSS_OPEN through
`mbss-open-admission.inc`. AP-client and WDS candidates currently repair only
failed-open module-reference balance, and sniffer has lifetime staging; their
raw `VIRTUAL_IF_UP` still has no shared ticket. All five legacy DOWN callers
remain unconverted; checked MBSS close is staged but not the netdev stop hook.
Moreover, pinned `ApCli_VirtualIF_Open` ignores the return from `APC_OPEN`
after virtual UP, so a zero return is not proof that its own setup succeeded.
Pinned `ap/ap_apcli.c` returns FALSE from `ApCli_Open` if no
`ApCliTab[*].wdev.if_dev` matches the device. Before that verdict it may run
the packet-forward probe; on a match it starts the netdev queue and programs
hardware MAC and optional state. A bare error return after legacy virtual UP
would leak the incremented count/module ownership and could leave partial
vendor state. Validate the device/generation and reserve a ticket before UP;
any post-UP failure needs checked rollback or retained-resource recovery.
The next integration must acquire and retain shared ownership at every family
entry before its raw UP/DOWN, pass checked completion/failure through the
common dispatcher, and preserve vendor references for retry/rollback. A
MBSS-only dispatcher patch would leave competing count writers live. This is
source coverage evidence, not a production, target-build or device result.

## Registration removal versus reserved open — 2026-10-24

The isolated candidate's generic `wr_iot_registry_begin_remove` previously
marked a record removing even in `WR_REF_RESERVED`, while the MBSS open wrapper
could be between admission and raw UP. It now refuses removal in RESERVED;
the caller may retry after the open ticket retires. An owned or closing record
can still be marked for removal so normal stop/teardown can proceed. Host
`check-interface-registry.c` covers refusal during reservation and later
success after an unacquired open finishes; `check-netdev-registration.c` also
passes. Both compiled with MinGW GCC `-std=c11 -Wall -Wextra -Werror` and
ran with exit 0. This closes one isolated candidate race, not the shared
UP/DOWN dispatcher, lifetime or device acceptance gates.
The candidate assembler binds `wr_iot_mbss_begin_remove` before MBSS beacon
storage teardown and returns failure before that mutation when admission is
refused. The helper requires `WR_REF_IDLE`, so RESERVED fails at both the
generic mark and MBSS-specific boundary. The expanded netdev-registration
fixture asserts both refusals leave the record unmarked and BSS LIVE; strict
compile and run returned 0. Generic mark_removing remains unbound for other
families, so this proof is limited to staged MBSS removal.
Full exact-source candidate preparation also completed with exit 0 into
`.iot-local-check/reserved-removal-20261024`. The generated driver copy has
the RESERVED guard in `include/interface-registry.h` and the checked removal
call before beacon deinit in `ap/ap_mbss.c`. This confirms composition of the
isolated overlay, not compilation of the target module or runtime safety.

## MBSS stop ownership audit — 2026-10-24

Pinned MT76x3 source: `ap/ap_mbss_inf.c` installs `MBSS_VirtualIF_Close` as
the netdev stop hook. That hook calls `VIRTUAL_IF_DOWN` and returns success,
but `include/rt_os_net.h` defines `VIRTUAL_IF_DOWN` as `VOID` and discards the
ioctl result. `common/cmm_cfg.c` handles `CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN`
by decrementing `VirtualIfCnt` before calling `rt28xx_close` for the last
interface, and discards the close result. Its UP path increments the same
counter, including the secondary-interface branch. The source has no common
transition lock around this count and the radio open/close decision.

Consequently the isolated `wr_iot_mbss_close_checked` helper cannot simply
replace the stop hook: its CLOSE/BSS_CLOSE ticket needs an owner that
serializes all UP/DOWN writers, protects the count from underflow and
rolls back or retains ownership on failed close. The stop path must propagate
failure without reporting a completed kernel stop while BSS resources remain.
The isolated candidate already stages zero/overflow arithmetic guards in
`tools/iot/prepare-interface-count-guards.py`; those guards do not serialize
the count or preserve it after a failed last-interface close. A source-wide
call inventory finds five UP/DOWN families: main (`os/linux/rt_main_dev.c`),
MBSS (`ap/ap_mbss_inf.c`), AP-client (`ap/ap_apcli_inf.c`), WDS
(`ap/ap_wds_inf.c`) and optional sniffer (`os/linux/rt_profile.c`). Every
family reaches the same `CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP/DOWN` dispatcher.
The candidate also already contains `wr_iot_virtual_down_checked` in
`tools/iot/virtual-down-checked.inc`: with an owned CLOSE/BSS_CLOSE ticket it
checks the count under the transition lock; for the last interface, stage 1
retains the zero count and the same ticket while checked physical close is
retried. This is exercised by `tools/iot/check-virtual-down.c`. It is appended
to a staged `common/cmm_cfg.c` but the legacy ioctl cases and all five legacy
`VIRTUAL_IF_DOWN` callers still use the unchecked path. Do not introduce a
second reservation algorithm. Integrate this existing checked path only after
one owner covers all writers and stop failure/lifetime semantics are resolved.
The pinned `os/linux/rt_main_dev.c` legacy `rt28xx_close` itself returns 0
when `GET_PAD_FROM_NET_DEV` yields no adapter; otherwise it calls `RTMPDrvClose`
(declared `VOID`) and then also returns 0. Thus changing only the outer ioctl
to return `rt28xx_close` would still produce false success. The checked close
chain must report its own teardown milestones and retain the owner/resources
on failure. The staged `MBSS_VirtualIF_Open` admission wrapper takes a BSS_OPEN
ticket, but its raw `VIRTUAL_IF_UP` still reaches the unconverted shared
dispatcher. This makes the common UP/DOWN dispatch and all-family ownership
the actual integration boundary, not the already-implemented MBSS wrapper.
Next: bind all five virtual-interface families to a single checked transition
owner and dispatcher, then test interleaved
main/MBSS open, close and reset. This is a source audit, not a target build or
router-runtime result; the production driver and router remain unchanged.

## Rule for every project router

IoT is a required built-in network for every supported board, alongside the main and guest networks. No board configuration or build option may exclude its implementation from a release image. WR1200JS is the first implementation target; Mi Mini and each later board require their own capability, image and on-device acceptance evidence. Until those checks pass, that board is pending, not an exception that hides or simulates IoT. Keep the authenticated runtime on/off control separate from build inclusion. Factory activation must use distinct safe credentials and verified LAN/router isolation; do not broadcast an unsecured default network. The current WR1200JS image that excludes IoT is a development checkpoint, not release acceptance.

Current checkpoint, 2026-10-18: ABI run [#449](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39114663222)
passed for `b65acf6081ebe9e73e8fea7501af346f7473dcd9`. It compiled the
activation and snapshot components for MIPS and passed host fixtures, including
retained activation recovery and request-snapshot guard revalidation. The
source-integration diagnostic still reports activation pending: the tested
controller uses an injected backend, and production RC bindings, complete
writer/service rollback, firmware inclusion, and router runtime are not proven.
See [ABI checkpoint evidence](evidence/IOT-ABI-B65ACF6.md).

The main WR1200JS firmware workflow on `d1dc0eb` explicitly excludes
`wr-iot-profile.c` and `wr-iot/`; thus the passing full firmware build does not
contain an accepted IoT implementation. The 2026-10-18 read-only device sample
also found no live `ra2` interface. No router state was changed.

Approved 2026-10-08. Source inspected at vipshmily/padavan-4.4 commit `c25283e915a2a00a763774dd255b14aff997285e`. This is an implementation contract and partial source audit, not device support proof.

## Current constraints

`trunk/user/rc/ralink.c` declares `i_fphy[2]` and `i_val_mbss[2]` and sets `i_ssid_num = 2` (main plus guest). It emits two-entry NoForwarding, NoForwardingMBCast, HideSSID and HT_MCS lists, and individual guest SSID/password fields. Raising BssidNum alone leaves profile fields incomplete and may introduce out-of-bounds accesses if loops are generalized.

`trunk/user/rc/net_wifi.c` explicitly starts/stops main and guest interfaces and adds the guest interface to `IFNAME_BR`. A third IoT interface needs its own lifecycle and bridge attachment. Existing guest isolation is not evidence of a separate IoT subnet.

Both driver families expose MBSS profile parsing and virtual-AP initialization. Their headers select `MAX_MBSSID_NUM` from chip capability only under `MBSS_SUPPORT`; otherwise it is 1. Beacon array capacity is not proof of effective chip capacity. Trace MT7603E and MT7612E capability initialization and actual build definitions, including AP-client/repeater reservations, before selecting an interface index or advertising three simultaneous SSIDs.

## Required implementation

1. Preserve main and guest network settings. IoT uses a third BSS, initially 2.4 GHz; shares the physical radio channel and width constraints.
2. Extend every relevant profile field consistently: SSID, authentication, cipher, PSK, isolation, hidden status, rate policy and other per-BSS settings. Default OFF retains the existing two-BSS profile where possible.
3. Create an isolated IoT bridge, non-overlapping subnet and scoped DHCP/DNS configuration. Start/stop the third interface with radio and network lifecycle; never attach it to the primary LAN bridge as a convenience.
4. Integrate IPv4 and IPv6 firewall policy, blocking primary-LAN and router-administration access by default while explicitly permitting DHCP/DNS and requested internet traffic. Evaluate hardware offload paths so isolation cannot be bypassed.
5. Add authenticated WebUI enable, SSID/security/password, subnet/status, local QR and explicit controller exceptions. Default WPA2-Personal/AES. Provision IoT in every released board profile; factory activation requires verified distinct credentials and isolation. Keep it OFF during development until that gate passes. Discovery/mDNS and client isolation require deliberate policies compatible with the user's IoT devices.
6. Verify actual target compilation, image assets, lifecycle and persistence, followed by device tests with primary, guest and IoT simultaneous. Verify DHCP, DNS, inter-network isolation, allowed exceptions, restart behavior and AP-client/repeater compatibility separately.

## Evidence still missing

Effective per-chip third-BSS capacity, complete profile/lifecycle integration, isolated subnet/firewall, WebUI, target build and live-device behavior remain unverified. No router configuration changes are authorized by this audit.

## Authenticated Apply and RC integration audit — 2026-10-21

Follow-up 2026-10-21: the candidate request-stage reader now accepts only the
separate `wr_iot_request_*` NVRAM namespace. Host staging and snapshot
fixtures passed with Windows networking/test-path adapters. This closes the
specific risk of the stage reader consuming ordinary active-form names, but
does not bind an authenticated form, RC notification or production activation
controller. Evidence: `evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.

The pinned HTTPD source registers `apply.cgi*` as an authenticated handler.
Its Apply path writes registered form values through `nvram_set`, dispatches
`action_script` through `sys_script`, then redirects; RC notifications are
handled separately by `handle_notifications()`. Since `sys_script` has a
generic `/tmp/<name>` execution fallback, any IoT trigger must be an explicit
fixed-name branch, never user-controlled shell text. Candidate Wi-Fi values
must stay separate from active NVRAM until activation succeeds, with original
state retained for rollback. The generic Apply success callback cannot report
whether activation actually succeeded, so candidate-table registration alone
is insufficient. Use a dedicated authenticated submission/result path that
validates the whole request before writes and serializes it with the fixed RC
transaction. No production IoT notification consumer or
activation backend is installed yet. Detailed pinned-source evidence and the
required control flow are in
[`WR1200JS-IOT-APPLY-CONTROL-PLANE-2026-10-21.md`](evidence/WR1200JS-IOT-APPLY-CONTROL-PLANE-2026-10-21.md).

Update 2026-10-18: build #451 run `39114348390` passed the production
Kbuild capacity gate. Downloaded original reports are preserved as
`evidence/WR1200JS-BUILD451-IOT-MT7603.json` and
`evidence/WR1200JS-BUILD451-IOT-MT7612.json`. Both effective commands enable
MBSS. MT7603 has a source/configuration limit of 16; MT7612 has 8 (array
ceiling 16, chip limit 8). The required 2.4 GHz three-BSS source gate passed.
This supersedes the missing effective-source-capacity item above. Both reports
retain `runtime_verified: false`; production activation, live third BSS and
physical isolation/lifecycle acceptance are still missing. Full build #451
was still active when the gate and downloaded reports were inspected.


## Capability initialization traced — 2026-10-08

MT7603 `mt7603_chip_init` calls `mt_bcn_buf_init`; the latter assigns BcnMaxHwNum=16 and BcnMaxNum=16. The header may reduce the array ceiling to 8 under ECONET_ALPHA_RELEASE, which still exceeds three; confirm effective definitions in a target probe.

MT76x2 initialization calls `rlt_bcn_buf_init`. Its MT76x2 branch assigns hardware beacon count 8. With APCLI_SUPPORT it sets BcnMaxNum to 8 minus MAX_MESH_NUM; the inspected header defines MAX_MESH_NUM as 0. This gives a source-level candidate capacity of eight, not proof of eight working networks.

The effective kernel configuration downloaded from successful WR1200JS run 37823022372 enables CONFIG_MT7603E_MBSS_SUPPORT and CONFIG_MT76X2_AP_MBSS. Effective driver preprocessing, target capacity probes and a third-BSS device test remain required. No production profile has been changed by this audit.

## Lifecycle integration requirements — 2026-10-08

Pinned-source follow-up, 2026-10-18: MT7603
`os/linux/rt_main_dev.c` calls `rt28xx_init` and then `RT28xx_MBSS_Init` in
the main-interface open path. RC `restart_wifi_rt` stops the radio interfaces,
regenerates the 2.4 GHz profile when requested, and reopens main/guest through
`start_wifi_ap_rt`. Merely editing BssidNum or administratively opening an
already-existing ra2 is not evidence that the new virtual interface was created.
The production activation backend must integrate the profile/radio reopen and
observe ra2 identity afterward, retaining the original main/guest profile for
recovery. Existing IoT quiesce hooks clear temporary gates during ordinary
restart; calling that restart blindly inside activation would invalidate staged
state. This interaction still needs a dedicated coordinated activation path.
`594d98b` supplies only the owned-bridge administrative BSS-UP primitive and
host-kernel tests; it does not supply that radio reload/activation path.

The pinned `stop_wifi_all_rt` stops the AP-client, four WDS interfaces, guest and main BSS explicitly. It does not stop a third BSS. `start_wifi_ap_rt` attaches main and guest to `IFNAME_BR`; inserting IoT into this existing bridge loop would violate the isolated-subnet requirement. Radio scheduling, manual radio control, profile regeneration and full LAN restart must all quiesce IoT explicitly.

Activation order:

1. Serialize configuration/profile generation and validate effective router/radio mode, credentials, complete active-subnet inventory, interface identity and ownership. An existing unrelated `br-iot` must cause rejection.
2. Stop and detach the third BSS before changing its profile or network. Confirm it is down; abort on failure.
3. Prepare the complete profile, create/verify the owned IoT bridge with its address, and install IPv4/IPv6 isolation before the BSS can carry traffic.
4. Rebuild DHCP/DNS while retaining main-LAN settings. IoT DHCP must set the existing service's DHCP-used flag even when main-LAN DHCP is disabled. Check configuration and service startup.
5. Attach only the third BSS to the IoT bridge, then enable it. Report active only after interface/bridge/service/firewall observations succeed.

Failure and shutdown order:

- Disable the third BSS first, then detach it. If either fails, retain isolation rules and report failure; do not remove guards from a potentially live interface.
- Rebuild the shared DHCP configuration without IoT, preserving LAN DHCP/DNS. Remove only resources positively owned by IoT.
- Firewall reload, WAN changes and DHCP restart must regenerate the IoT policy before generic accept rules, including the default filter builders and the case where the main firewall is disabled.
- Do not enable IoT in AP-client-only, WDS-only or radio-off modes. Repeater/AP-mode support requires a separate decision and evidence; reject unsupported combinations clearly.

Host evidence so far: run 37832869879 verifies eight IPv4 TCP checks, including WAN replies, LAN/router isolation and blocking a preexisting LAN connection with generic ACCEPT policies. It does not prove production lifecycle, DHCP lease transactions, Wi-Fi driver behavior or target-device runtime. Extended UDP/IPv6 checks are pending.

## Expanded IPv6 isolation packet matrix — 2026-10-18

The disposable host-kernel packet fixture now creates separate IoT, LAN and WAN
IPv6 prefixes and first proves that its TCP/UDP baseline routes work. After
loading the generated IPv6 filter rules it checks router INPUT and forwarded
traffic over TCP and UDP, including IoT-to-LAN/WAN and unsolicited LAN/WAN-to-
IoT paths. The existing IPv4 TCP/UDP and DHCP source-port checks remain in the
same fixture. This is a stronger regression gate for the current policy, which
blocks all IoT IPv6 traffic, but does not implement IPv6 internet access or
prove target-kernel, production-lifecycle, Wi-Fi, or physical-router behavior.
Local Python syntax validation passed; the privileged namespace test requires
Linux CI. The first run, `39102134653`, failed before applying any firewall
rules because the fixture passed an unnecessary fourth argument to its TCP
server helper. The original job log and `build_log.nim` triage confirm this
test-harness error. After that call was fixed, rerun `39102351326` reached the
IPv6 topology baseline but failed connecting from IoT to the LAN TCP listener
(`fd51::2:8082`), still before firewall rules were loaded. The failure is in
test routing setup, so it proves neither a policy pass nor a policy defect.
The fixture now enables forwarding on each routed interface explicitly and
prints route/address/neighbour/sysctl diagnostics if a baseline path fails.
ABI run `39103063444` stopped before the packet test because `sysctl`
interpreted the dot in interface name `eth2.2` as a path separator. The fixture
now writes and reads the exact `/proc/sys/net/ipv6/conf/eth2.2/forwarding`
path. This correction was published as `770a7c5`. ABI rerun `39103236496`
passed setup and policy preparation but failed before firewall installation:
the IoT namespace could not reach the LAN IPv6 listener. The original job log
was reviewed with `build_log.nim`; this is a host-test baseline failure, not
evidence for or against the firewall policy. Routes and forwarding were present;
after the failed connect, diagnostics showed the LAN address/MAC in bridge FDB
and `fd51::2 REACHABLE`, so an absent NDP response alone does not explain the
missing TCP reply. Diagnostics now also capture the reverse route, LAN IPv6
listener via `ss`, and the pre-firewall FORWARD table. No IPv6 packet-policy
conclusion is established yet.

## Radio writer coordination requirement — 2026-10-21

Legacy module helper return values do not prove a fresh adapter: smart_unload
returns 1 even for a busy module without issuing removal, while smart_load
returns 0 for an already loaded module. Require strict absent/present/error
observations and interface generation/state before/after any selected reload;
verify 5 GHz is preserved. Legacy void stop/start wrappers do not establish
individual interface success or exact main/guest restoration.

Changing BssidNum is not address-neutral. Pinned MT7603 capability defaults to
HIF_MT/MBSSID_MODE4; its MT_MAC path changes the address mask at 2→3 BSSes.
Guest MAC can therefore change depending on factory address bits even while
main remains unchanged. Verify actual mode/addresses, main/guest/APCLI/WDS
mapping and hardware filter behavior before choosing a reserved-third-BSS or
fresh-adapter lifecycle. Do not silently promise MAC preservation or patch a
mask without target evidence. Record any required migration before acceptance.

Distinguish failed-startup rollback from normal disable after ACTIVE. DNS
activation commit releases its original service/file/lease snapshot; abort
cannot restore that snapshot afterward. Normal OFF requires a fresh guarded
transaction against the current main/guest/service configuration, removing
only owned IoT resources and preserving subsequent legitimate changes. Do not
keep the startup service guard indefinitely through ACTIVE or replay an old
global DNS configuration on normal OFF. The real backend must prove both
startup rollback and post-commit disable/recovery before acceptance.

Normal OFF must prepare and commit replacement DNS/DHCP before removing its
owned bridge: old service configuration can depend on that interface during
failure recovery. First quiesce IoT BSS and install full quarantine, close
internal gates, regenerate/verify services with no owned IoT fragment, then
bring down/detach/remove the bridge and remove the owned profile. A foreign
bridge or administratively UP BSS must refuse service-disable preparation.
Administrative DOWN alone is not vendor RF quiescence proof.

### Driver transition gate before IoT installation — 2026-10-22

The current isolated MT76x3 radio bundle is a candidate, not an installed
driver change. Before copying it into the build source, demonstrate one
per-adapter transition owner across MBSS_OPEN, VIRTUAL_INF_UP, CR_ENABLE,
queue publication, CR_DISABLE, MBSS_CLOSE, VIRTUAL_INF_DOWN and PDMA reset.
The design must state which steps can sleep, which run in interrupt/BH
context, and how reset waits for or invalidates an in-flight open without
holding BcnRingLock across polls, ring cleanup or physical startup. Do not
assume the generic DISABLE_DEQUEUEPACKET flag identifies reset: radio-off
and ATE also write it.

For every failed open, prove exactly one reference/count rollback and
selected-BSS intent cleanup, with separate cases for the first virtual
interface (`rt28xx_open` path) and an additional interface (all-BSS beacon
rebuild path). The rollback must not close a different active interface or
resume beacon submission after reset/administrative radio-off. A CR_ENABLE
error must be observed by the owner; a successful netdev open with failed
CR_ENABLE is not an acceptable state. Cover concurrent close and reset
entry/exit, including repeated retries, in fault-injection checks.

Only then stage the full modified MT76x3 source in the exact WR1200JS build
path, compile the actual selected MIPS driver object/module, and inspect the
final image and build log. The existing ABI job compiles host/MIPS fixtures
extracted from the candidate; those fixtures do not prove a real driver
object builds or is installed. Preserve `production_installed=false` and
`bss_close_exclusion_proven=false` until their respective evidence exists.
Device RF silence, main/guest preservation and recovery remain separate
runtime acceptance gates. Source basis: pinned commit
`c25283e915a2a00a763774dd255b14aff997285e`, with the detailed audit
in `evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

Reserved third-BSS startup is not approved merely because ra2 is DOWN. Prove
beacon intent and management/data dispatch across both initial and repeated
main-radio opens. Pinned mt76x3 `wdev_bcn_buf_init()` does not clear bBcnSntReq;
an existing adapter must not be treated like fresh zeroed memory. Require an
observed silent/down/unattached baseline and preserve main/guest state before
selecting a lifecycle implementation. See the activation-gap source evidence.

The activation controller must coordinate legacy manual/scheduled radio and
guest changes, not just serialize its own request queue. `reload_svc_rt` causes
watchdog to requeue schedule controls; it is not a module reload. Preserve
scheduled/user radio-off intent. A legacy stop/restart must transition or
invalidate the controller's ACTIVE result and retain required recovery state;
status must not continue reporting ACTIVE solely from an earlier terminal
mailbox record. Cover events queued during startup/recovery and post-activation
profile changes before production integration. The current quiescence hooks
alone do not satisfy this requirement. Source evidence and pending cases are
in `evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

## Source-level radio capacity diagnostic — 2026-10-18

The WR1200JS build workflow now has a diagnostic step after the production
build that records separate MT7612/MT76x2 and MT7603/MT76x3 evidence under the
`wr1200js-iot-radio-capacity` artifact. `tools/iot/check-capacity.py` uses each
radio's actual Kbuild `.cmd` and target compiler, checks the effective MBSS and
beacon-array macros, verifies that `MAX_MBSSID_NUM` consults the chip limit,
follows the pinned chip initializer, and records the nested source commit plus
SHA-256 hashes for the source files it inspected. It reports the
source/configuration BSS limit while keeping
`runtime_verified: false`; it does not enable IoT or prove three simultaneous
working SSIDs.

The initial IoT contract is 2.4 GHz only, so the firmware build workflow now
treats the MT7603/mt76x3 three-BSS source/config result as a required gate. An
absent, unavailable, or insufficient probe fails that post-build step. The
MT7612/mt76x2 5 GHz result remains diagnostic until 5 GHz IoT is in scope.
This gate establishes source/config capacity only; it does not activate the
third BSS or count as runtime/device acceptance.

Local synthetic Kbuild fixtures exercised the MT76x2 and MT7603 paths and
reported source/configuration limits of eight and sixteen BSS respectively.
These fixture results only validate the diagnostic's parsing and reporting.
The probe has not yet run against a real target build.

The ABI workflow now includes `tools/iot/check-capacity-selftest.py` to exercise
both radio parsers and the required-capacity failure case with host synthetic
Kbuild trees before downloading the large target toolchain. On 2026-10-18,
`py -3 tools/iot/check-capacity-selftest.py` passed twice with exit code 0
in an approved elevated execution context on Windows. It reported
`PASS IoT capacity probe MT76x2/MT7603 source checks and required-limit failure`.
The ordinary sandbox still denied nested temporary-directory creation; this
was an execution-permission issue, not a failed capacity assertion. These
successful host fixtures do not establish target radio capacity or runtime
acceptance; the updated workflow result remains pending.
The self-test also checks absent and ambiguous Kbuild command files and an
unavailable compiler in both diagnostic and required modes. All six negative
cases passed locally on 2026-10-18: unavailable evidence keeps capacity and
runtime verification false, emits a JSON reason, and fails the required gate.
The report now distinguishes `effective_source_config_bss_limit` (the minimum
of the array ceiling and chip source limit with MBSS enabled) from the raw
chip limit. A passing MT7603 fixture with a sixteen-entry chip limit and an
eight-entry array verifies that the effective value and console limit are eight.
This remains source/configuration evidence rather than working-SSID capacity.
The ABI workflow also compiles the prepared `services_ex.c` to
`iot-services-ex-mips.o` with the
WR1200JS MIPS compiler. Its include paths follow the pinned RC/shared Makefiles
and include the Linux kernel headers; the WR1200JS Ralink board header is staged
directly beside `rc.h` by the preparation step. In ABI run `39113907911`
for `52c802b`, the `Prepare pinned RC IoT bridge and owned radio-stop hook`
step completed successfully, including whole-object `services_ex.c` MIPS
compilation. Earlier run `39113649278` failed because kernel include paths
overrode the target sysroot's errno header; using `-idirafter` and staging
UAPI headers corrected that integration gate. The overall run passed and its
downloaded object/hash identity was independently verified; see
[ABI evidence](evidence/IOT-ABI-52C802B.md). Firmware linking of this IoT
candidate and physical runtime remain unconfirmed.

The separate ABI workflow [run `39104700313`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39104700313) completed successfully for `dd1e98c`. Its `band-steering-mips-abi` artifact contains compiled MIPS RC objects for the staged IoT bridge, profile, DHCP, network, request-stage, and request-snapshot code, as well as passing host DHCP/DNS and IPv4/IPv6 firewall fixtures. This is source-preparation/ABI evidence, not a production firmware image. The artifact's `iot-rc-source.json` says
`activation_integrated: false`, `writer_journal_lifecycle_bound: false`,
`dnsmasq_service_rollback_complete: false`, and that DHCP protocol readiness
is pending. The source does install a journal binding inside the conditional
DNS restart transaction; the report's false lifecycle value is conservative
because the production IoT activation path does not set that gate and not all
DNS-related writers are covered. Main firmware build
[#448](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39104625566)
(`5dd2c80`) explicitly excluded `wr-iot-profile.c` and the `wr-iot` RC
directory; its success applies only to that non-IoT scope. Production
integration, complete service rollback, Wi-Fi behavior, and physical-router
acceptance remain open.

## Owner clarification — Classic only, 2026-10-20

IoT must be fully usable in the original Classic theme even if no other theme
is installed. Add 2.4 GHz / 5 GHz / IoT navigation to the network-map panels,
all Wi-Fi section pairs and relevant shared Classic shortcuts. Preserve
Classic classes/design, Apply behavior and existing unsaved repository work.
No new theme or Modern dependency is authorized by this task. Retain the
existing shared-main-network mechanism and production IoT components; do not
introduce a second configuration writer. First stage is source/local checks,
without a full firmware compilation. Local navigation work and its explicit
production-backend gap are recorded in
`evidence/WR1200JS-IOT-CLASSIC-NAVIGATION-2026-10-20.md`.
This clarification does not turn partial activation fixtures into a working
IoT service; complete authenticated Apply, rollback, isolation and runtime
acceptance remain required.

## Command-worker shutdown requirements — 2026-10-22

The transition implementation must cover queued work as well as active calls.
Pinned MT7603 `RTPCICmdThread` checks STOPED before entering CMDHandler, but
CMDHandler drains commands without checking CmdQState between elements. Queue
insertion refusal after STOPED is therefore not cancellation of accepted work.
The exit path frees queued payloads/elements when PM_FlgSuspend is false and
skips that cleanup when suspended. Do not infer a terminal request result from
STOPED or an empty queue.

Before production activation, require all of the following:

- Publish a stopping/closing generation before resource teardown; revalidate
  admission immediately before any accepted operation reaches radio hardware.
  Queue locks may protect admission, never the whole hardware operation.
- Return an explicit canceled/failed terminal result to each accepted IoT
  request removed during teardown, preserving result lifetime and references.
  An operation that may already have changed hardware must retain recovery,
  not report clean cancellation or success.
- Prove the suspended-worker exit path retires its queued references or retains
  adapter lifetime until a specified recovery path does so. Do not unconditionally
  free buffers that another worker/callback may still own.
- Never wait for a transition lock from a command worker while the owner joins
  that worker. Reopen must use a new generation; stale queued requests may not
  execute against the new adapter/radio state.

These are required production gates, not claims that the current candidate
implements cancellation or driver-wide serialization. Exact source evidence:
`evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

## Sequential-agent integration audit — Sol, 2026-10-22

Current shared branch is codex/wr1200js-service-webui at 441138a. The existing
IoT work is preserved in this checkout and must be continued rather than
reimplemented. Git author names include Codex and Andrzej1973; these are not
reliable attribution to individual model/account sessions.

Verified composition already present:

- prepare-rc.py assembles bridge, profiles, DHCP/DNS, quarantine/readback and
  disable adapters in an isolated RC source tree; activation_integrated and
  complete DNS writer/rollback claims remain false.
- prepare-http.py and prepare-control.py compose authenticated CGI, private
  mailbox and RC notification. control-server.c calls wr_iot_activation_execute;
  only fixture definitions implement that symbol in tools/iot. No production
  activation backend is supplied by these preparers.
- prepare-radio-queue-candidate.py assembles checked enqueue, result cleanup and
  MCU ACK stages with pinned input hashes. prepare-radio-error-candidates.py
  separately assembles MBSS/beacon/reset error candidates. These are complementary
  partial bundles, not one installed driver. Neither proves lifecycle exclusion.
- band-steering-abi.yml invokes the preparers and composition fixtures. The main
  firmware workflow explicitly requires wr-iot-profile.c and wr-iot RC directory
  to be absent. A firmware success therefore cannot establish IoT inclusion.

Outstanding integration work, in dependency order:

1. Extend actual generated worker-exit fixture coverage to the new pending
   cancellation walk before the suspend branch. Current composition extractor
   tests the older inner free slice; the helper test does not cover this walk.
2. Establish adapter-wide admission/lifetime across first/additional open,
   close/reset and worker teardown; revalidate radio generation/readiness with
   the BSS opening mutation. Preserve no-wait-on-joined-worker ordering.
3. Compose the reviewed queue/MCU and MBSS/reset changes with overlap review,
   compile the actual target driver, then bind the RC activation callbacks.
4. Close DNS-writer/service rollback gaps, wire authenticated Classic Apply and
   observed status to that backend, and only then replace production exclusion
   with exact image and approved device acceptance gates.

PROJECT_STATUS.md, CODEX_HANDOFF.md and the detailed IoT activation-gap evidence
file exist locally but are untracked at this checkpoint. Agents using this same
folder can read them; GitHub checkouts do not receive them until explicitly
included in an authorized commit. This tracked contract records the shared
integration path without silently staging the untracked history. Current sole
writer remains Sol; preserve the existing Sol/DeepSeek handoff rules.

This audit inspected current source/workflow/Git state only. It did not rerun
ABI CI or establish on-device behavior. No duplicate backend or driver installer
was created.

Follow-up 2026-10-22: integration-audit item 1 now has strict host execution of
the actual generated pre-suspend cancellation walk (two IoT nodes, foreign tail,
repeat notification, reference preservation and later cleanup). Full worker
shutdown/concurrency and adapter lifetime remain pending; proceed with item 2.
Evidence is recorded in the existing IoT activation-gap report.

## Adapter transition admission candidate — Sol, 2026-10-22

radio-transition.h introduces a shared nonblocking admission state for START,
BSS_OPEN, RESET and CLOSE. All calls require the same external adapter-scoped
short lock; the exclusive ticket spans hardware work after releasing that lock.
A close request invalidates queued epochs, clears readiness and prevents new
open/reset admission; admitted work must retire before close can begin. Late
success cannot undo closing, stale completion cannot release a newer owner,
reset failure requires teardown, and epoch exhaustion fails closed.

Strict host GCC sequential transition fixture passed. ABI workflow now contains
host sanitizer execution and MIPS object checks for this header/fixture; those
CI checks have not run for this change. This is admission state only, not an
installed lock or proof of concurrency. Integration must put the state in the
actual adapter, prove initialization/destruction lifetime, use one short lock
at every entry and keep that lock out of firmware waits/task joins. Every
caller that fails admission needs a defined retry/abort path; ndo_stop and
mandatory reset cannot simply discard required teardown. Actual main readiness
must be observed under that admission protocol before BSS mutation, with no
unregistered writer able to invalidate it. Keep production exclusion until the
full driver bindings, target compile and hardware evidence satisfy the gates.

## Radio reconstruction invalidates queued generations — 2026-10-22

Pinned MT7603 common/cmm_cfg.c:1046-1049 increments VirtualIfCnt before
rt28xx_open and decrements on failure; :1063 increments on additional-interface
open before all-BSS beacon rebuild. include/rtmp.h:10055-10057 defines these as
plain count macros. A positive count is not readiness proof. Adapter lifetime
anchors found: common/rtmp_init.c RTMPAllocAdapterBlock initializes BcnRingLock
at line 136; os/linux/rt_profile.c RTMPFreeAdapter frees it at line 1742.
A new transition lock/state needs its own correct allocation/unwind/free path;
these anchors alone do not establish lifetime or justify reusing BcnRingLock.

Corrected radio-transition.h so admitted START and RESET advance the epoch,
not only CLOSE. Requests queued before reconstruction are now rejected even
after a successful reset with the same adapter/netdevice address. Epoch overflow
sets a fail-closed state rather than wrapping. Strict host fixture now verifies
successful reset restores readiness but cannot admit a pre-reset BSS request,
then exercises reset failure/teardown. GCC -std=c11 -Wall -Wextra -Werror -O2
and whitespace checks passed. Actual vendor binding and target execution remain
pending; no production or router changes.

## Partial adapter initialization boundary — 2026-10-22

Pinned RTMPAllocAdapterBlock (common/rtmp_init.c:74 onward) initializes resource
lists after AdapterBlockAllocateMemory, then allocates statistics BEFORE driver
spinlocks. A failed statistics allocation follows the local failure block and
RtmpOsVfree directly, not RTMPFreeAdapter. The normal RTMPFreeAdapter path
(os/linux/rt_profile.c:1697 onward) frees driver locks and resource lists before
RtmpOsVfree. New transition state/lock must be initialized only after its required
allocation prerequisites, and its failure unwind must match this local path.
Do not rely on the normal destructor for every partial-allocation failure.

radio-transition.h now refuses every begin/finish and ignores close requests
while epoch is zero (the zeroed, uninitialized adapter state). Only explicit
initialization admits transitions. The strict host fixture checks all four
operations on zero state, then the existing lifecycle/reset cases; it passed.
This is a state precondition, not permission to acquire an uninitialized lock:
the adapter publication/lifetime protocol must exclude callers before lock
initialization and after destruction. Actual vendor bindings remain pending.

## Adapter storage/init/free candidate — 2026-10-22

prepare-radio-adapter-candidate.py stages exact pinned rtmp.h, rtmp_init.c and
rt_profile.c in a separate output. It adds dedicated NDIS_SPIN_LOCK and transition
state fields, initializes them immediately before successful adapter publication
(after all existing allocation failure branches), and stages a matching free in
normal destruction. The stats/ring early-failure paths precede this initialization
and do not acquire the new lock. No production source is edited.

Verified generated source ordering, one allocation/free hook, extracted actual
init/free host compilation/execution with injected lock primitives, and refusal
of drifted source before output creation. Strict GCC passed. Evidence retained:
C:/Users/ANDRZEJ/AppData/Local/Temp/iot-adapter-candidate-jsmcqyas.
These are fragment/source checks, not whole-driver compilation or early-failure
runtime execution. Destructor retirement/publication safety is NOT proved;
entrypoints_bound and adapter_retirement_proven remain false in the manifest.
The free hook assumes all users have retired and must not be installed before
that precondition is enforced. Next bind lifetime/admission at actual entries
and teardown, with source-overlap review for existing rtmp_init.c/header bundles.

## Queue/MCU/adapter assembly merged — 2026-10-22

prepare-radio-queue-candidate.py now invokes the adapter preparer and carries
its storage/lock/header into the existing queue/MCU bundle. The sole permitted
source overlap is common/rtmp_init.c: the adapter delta must equal exactly its
init insertion before publication, then that insertion is applied to the queue
candidate without replacing the file. Other overlaps still fail. Manifest
records one final hash per path and queue+adapter attribution; all production,
retirement and lifecycle-exclusion claims remain false. Source blob checks are
unchanged; only overlap text comparison normalizes Windows CRLF/LF.

Final assembled output retained both queue dispatch/cleanup and adapter init,
with unique manifest paths and matching SHA256s. Its actual queue-composition
fixture compiled with strict host GCC and ran successfully. The initial CRLF/LF
comparison refusal was corrected and rerun into a new output. Evidence:
C:/Users/ANDRZEJ/AppData/Local/Temp/iot-merged-adapter-07uv56fd/bundle-fixed.
This supersedes the earlier unmerged adapter/queue status; it does not establish
whole-driver compilation, real entrypoint locking, adapter retirement or device
acceptance. The existing ABI bundle step will exercise this assembly on its
next authorized CI run; no workflow run was started for this local check.

## Selective BSS close versus adapter close — 2026-10-22

Pinned main-device wrappers (os/linux/rt_main_dev.c:111-137,157 onward) mutate
main interface state before VIRTUAL_IF_DOWN/UP. Main close performs carrier/
queue stop and RTMPInfClose before decrementing the virtual count. Therefore
main readiness must be invalidated at this wrapper boundary even when another
virtual interface keeps the physical adapter open. A count-only hook in
cmm_cfg.c would miss these prior mutations.

Added WR_RADIO_BSS_CLOSE to shared admission state for selective, non-last BSS
close. It excludes open/reset but does not latch adapter closing or invalidate
main readiness on observed success. Last-reference close must instead use the
adapter-wide CLOSE protocol; its count decision and mutation need the same
owner. Failed/uncertain selective close remains faulted and requires recovery.
Strict host fixture passed selective-close exclusion and preservation of main
readiness/epoch, alongside existing startup/reset/close cases. Real wrapper
binding, count decision and RF evidence remain unimplemented/unverified.

Next integration must cover wrapper-side state changes, not only virtual count
ioctls. Main-down with surviving secondary BSS needs an explicit inhibited-main
state distinct from physical DOWN; do not treat it as READY or blindly reopen
all BSS. This is a required source binding before installing the admission gate.

## Main-interface inhibition candidate — 2026-10-22

The shared admission state now has main_inhibited and a main-down invalidation
operation, separate from physical adapter CLOSE. Main-down advances epoch and
clears readiness while retaining physical phase. Late BSS/reset/main-open
completion cannot undo a newer main-down intent. Selective BSS_CLOSE remains
admissible with inhibited main so secondary interfaces can retire; new BSS_OPEN
and RESET are refused. Explicit MAIN_OPEN (or physical START) may clear inhibition
only on observed success for its still-current epoch. It does not authorize
silently reopening a manually/scheduled disabled main interface.

Strict host fixture passed main-down during admitted BSS work, selective close
with main inhibited, main-down racing explicit main-open and successful explicit
reopen. This is deterministic admission-state testing; driver wrapper hooks,
real main-readiness observation and concurrent lifetime proof remain pending.
When binding, record main-down before MainVirtualIF_close mutations and route
reopen only from an authorized existing main-open action. Physical READY here
means the candidate's adapter state; it is not a claim of RF/client operation.

## First real wrapper hook staged — 2026-10-22

Adapter preparer now pins rt_main_dev.c and inserts main-down invalidation into
MainVirtualIF_close after the NULL-adapter check and before HNAT/carrier/queue/
RTMPInfClose/VIRTUAL_IF_DOWN mutations. It holds only the dedicated transition
lock across the state update, releasing it before existing teardown calls.
The main-close source and extracted full wrapper fixture are assembled into
the shared queue/MCU/adapter output, not maintained as a disconnected patch.

Strict host compilation/execution of the actual generated wrapper passed base,
HNAT and IFUP_IN_PROBE variants, checking mutation ordering, lock release,
NULL adapter and subsequent BSS admission refusal. Evidence:
C:/Users/ANDRZEJ/AppData/Local/Temp/iot-merged-adapter-07uv56fd/bundle-main-close.
The ABI workflow now includes these three sanitizer fixtures; CI was not run.
This verifies one wrapper with injected primitives, not a full target driver.
main_close_invalidation_staged is true, while entrypoints_bound and retirement
proof remain false. Actual open/reset/secondary-close gates and mandatory-close
completion are still required; this hook alone does not serialize all mutations
or prove adapter lifetime. No production source/image/device changed.

## Main-open failure reference repair — 2026-10-22

Pinned MainVirtualIF_open increments module use count before adapter lookup;
its NULL-adapter return and VIRTUAL_IF_UP failure previously leaked that
reference. Adapter candidate now decrements on both failures and returns -1
for NULL instead of reporting success. Successful open still retains exactly
one reference for normal close. The shared bundle carries the repaired actual
wrapper and its extracted fixture; no standalone parallel implementation.

Strict host fixture passed base, AP/HNAT and IFUP_IN_PROBE variants. The probe
fixture has an immediately successful sanity check; it does not prove bounded
probe waiting or failed probe cleanup. Existing IFUP_IN_PROBE loop remains
unbounded and needs cancellation/deadline review before full open admission
binding. AP_MAIN_OPEN occurs before VIRTUAL_IF_UP, so reference balance does
not establish rollback of beacon intent/hardware on failed first open.
Evidence: Temp/iot-merged-adapter-07uv56fd/bundle-main-open. ABI steps updated,
not run. No production driver/image/device changed. Main-open transition
reservation/retirement remains unbound and must precede AP_MAIN_OPEN mutation.

## Effective lifecycle macro evidence — 2026-10-22

Pinned mt76x3 os/linux/config.mk and config.mk.cfg80211 set
HAS_IFUP_IN_PROBE_SUPPORT=n; grep found the -DIFUP_IN_PROBE emitter only in
the cfg80211 file. This supports the non-probe source path, but is not final
build evidence and must not be generalized to all router configurations.

The existing capacity probe now records effective_lifecycle_macros for
IFUP_IN_PROBE, MULTI_CORE_SUPPORT and KTHREAD_SUPPORT from its actual target
rtmp_chip.o preprocessing command. This scope is labeled explicitly: it does
not establish the macros of rt_main_dev.o or all other translation units.
Unavailable evidence remains null, not false. Feature presence follows #ifdef
semantics, so a defined macro with value 0 is still reported as present.

Capacity self-test passed normal and feature-enabled synthetic Kbuild inputs,
including =0 presence, absent/ambiguous command, missing compiler and injected
timeout refusal. Host compiler execution used approved escalation. The updated
probe will run via the existing build diagnostic; no new firmware CI was started.
Target-command evidence remains pending. Resume normal main-open admission
binding first; retain probe-mode timeout/cancellation as a separate required
variant gate rather than infer that it blocks the selected source configuration.

## Main-open admission staged — 2026-10-22

Generated MainVirtualIF_open now reserves START or MAIN_OPEN under the dedicated
adapter lock before AP_MAIN_OPEN. It releases the spinlock before vendor calls.
Admission refusal balances the module reference; VIRTUAL_IF_UP failure retires
the ticket as faulted. Successful wrapper return retires via finish_unverified,
which publishes UNVERIFIED rather than main readiness. The change is part of
the existing shared bundle and main_open_admission_staged is true; complete
entrypoint/retirement proof remains false.

Pinned cmm_cfg.c:894-907 shows normal SANITY_CHECK tests only INTERRUPT_IN_USE;
RESET/HALT/NIC checks are conditional on IFUP_IN_PROBE. It therefore cannot be
used as the complete main-ready observation. UNVERIFIED must remain closed to
IoT until a separately proved same-generation radio observation is integrated.
This intentional pending state is not a production-ready main-open backend.

Extracted actual wrapper passed strict host base, AP/HNAT and probe-immediate-
success fixtures: NULL/ref balance, refusal while closing before mutations,
failed-open ticket release, no spinlock across AP mutation and successful
wrapper retirement with readiness false. Initial AP fixture compile failed due
to a shadowed test variable; its macro now dereferences the actual argument and
all three reran successfully. Evidence:
Temp/iot-merged-adapter-07uv56fd/bundle-main-admission-fixed.
ABI include path updated; CI/target driver/full concurrency not run. Probe wait
still needs cancellation/deadline; partial AP_MAIN_OPEN failure rollback, BSS/
reset/close exclusion and adapter retirement remain open. No device mutation.

## Same-generation observation admission — 2026-10-22

Added WR_RADIO_VERIFY and verify_finish to the shared candidate. VERIFY may
reserve UNVERIFIED/READY hardware state only while main is not inhibited;
it clears published readiness for the duration of observation and excludes
other admitted operations. The caller releases the short lock for reviewed
hardware reads, retaining adapter lifetime and its ticket, then takes that
same lock to complete. verify_finish returns acceptance only for a successful
readback on the unchanged epoch with READY/main_ready still true. A close or
main-down during reads may retire the ticket but cannot accept readiness.

Strict host fixture passed software-open remaining UNVERIFIED, verification
success, readback failure, main-down and adapter-close injected during reads;
all unsuccessful cases refuse BSS open and retire the ticket. This validates
the synchronization contract only. Actual radio reader and registered
open/reset/close writer coverage remain incomplete; no real hardware result
was supplied or inferred from IRQ/sanity flags. Next implement the bounded
MT7603 observation callback with precise register/state validity checks and
bind it to this ticket before permitting IoT BSS admission. Existing source/
module capacity and driver booleans alone do not satisfy the observation.

## Bounded MT7603 configuration readback candidate — 2026-10-22

Added mt7603-main-observe.h using actual pinned driver types/macros. With the
caller retaining VERIFY admission and adapter/netdevice lifetime, it takes the
beacon lock and checks chip identity, START_UP/IRQ, absent halt/reset/NIC/radio-
off/dequeue-disable flags, bounded BSS count, main netdevice identity/admin-UP
and beacon intent, candidate ra2 admin-DOWN/no beacon intent. It performs one
ARB_BCNQCR0 read, rejects all-ones, requires main bit0 enabled and candidate
bit2 disabled, and rechecks failure flags. No writes, sleeps or retries.

Source basis: rtmp_chip.h:212 defines IS_MT7603; rtmp_def.h START_UP documents
initialized Tx/Rx; cmm_asic_mt.c:1490-1493 starts main beacon queue with bit0;
ap_mbss.c uses BssId-indexed bits for secondaries. These register/intent states
are configuration evidence, not observed beacon delivery or RF silence. Existing
unbound reset/radio writers still prevent a claim of complete atomic observation.
Do not automatically promote VERIFY to READY from this partial evidence alone.

Seventeen strict host fixture cases plus NULL refusal passed, including chip/
flags/down-main/live-candidate/count bounds, all-ones MMIO and reset during read;
reads are bounded to one and lock is released. Header carried by shared bundle;
host sanitizer CI step added, not run. Whole-driver/MIPS macro compilation,
actual hardware access and device runtime remain unverified. Next validate the
callback against actual target headers and integrate required readback scope
with all transition writers before binding acceptance.

## Actual-header target compile gate staged — 2026-10-22

check-capacity.py now offers --check-main-observer. It reuses the actual recorded
rtmp_chip.o compiler/flags, substitutes a new small TU including rt_config.h and
the real observer header, compiles outside the kernel source tree and requires
ELF32 little-endian MIPS output. It records object/header SHA256, compiler command
and object path. Original source, module and firmware image are not changed.
The WR1200JS post-build MT7603 diagnostic now requires this check; requested
compile failure returns nonzero independently of the capacity requirement.
This gate checks actual driver types/macros but not the full modified driver.

Local execution context has no confirmed Linux MIPS compiler. wsl --list --quiet
returned its usage/install help rather than a distribution listing; no WSL or
system configuration changed. Existing capacity self-test and new compile-runner
control cases passed. Compile-runner cases explicitly inject a minimal MIPS ELF,
host ELF and compile failure, and verify ambiguous source refusal. They verify
the runner only, not real target compilation. The actual-header gate remains
CI-pending; do not claim mt7603-main-observe.h is target-compatible until it runs.
No new workflow run or firmware build was started. Continue remaining source
writer integration while waiting for an authorized target result.

## Deferred mandatory reset admission — 2026-10-22

Pinned cmm_mac_pci.c:1982 defines VOID PDMAResetAndRecovery. PSE recovery calls
it at :2432 after earlier PSE hardware mutations; PSEWatchDog :2595-2602 sets
and then clears its legacy pse_reset_flag around that call. A busy-return from
PDMA alone would therefore lose/reset-acknowledge an incomplete parent sequence.
Do not install such a guard. Top-level PSE recovery must own one admission ticket
across its nested PDMA work; direct PDMA callers need equivalent admission.

Shared admission candidate now latches reset_pending before any top-level reset
mutation, invalidates queued epochs, and clears readiness. A current operation
may retire but cannot overwrite the pending reset. Repeated pending requests
coalesce; a new request during admitted reset remains pending for another pass.
New open/VERIFY work is refused, RESET consumes the pending request and completed
adapter CLOSE cancels it. Strict host cases passed these orderings and late
observation rejection. The state helper does not schedule a worker or prove a
retry deadline; caller-owned retry/lifetime handling and main-inhibited reset
policy still require integration. No actual reset entry was modified here.
Next bind top-level PSE/direct-PDMA callers and their completion outcomes before
adding any early return inside raw recovery routines. Never hold the short lock
over polls, worker joins or the recovery body.

## Reset scope and startup request retention — 2026-10-22

Corrected reset request admission during active START: physical phase is still
DOWN until completion, but a busy START must retain a reset request rather than
ignore it as an idle, powered-down adapter. Late startup completion leaves the
pending reset intact and readiness false.

reset_pending now carries a PDMA/PSE scope mask. Explicit request_reset_kind
validates/coalesces kinds and the admitted RESET ticket captures only the
consumed mask. A new request arriving during that reset remains pending with
its own scope for the next pass. The legacy unspecified helper requests PSE,
which includes PDMA in the pinned source; production bindings must use explicit
scope and execute PSE once when its bit is present, not PDMA as a substitute or
both redundantly. Invalid kind requests leave state unchanged.

Strict host fixture passed idle-DOWN refusal, request during START, coalesced
PDMA+PSE scope, no extra epoch increment on coalescing, invalid-kind refusal,
and next-pass PDMA request surviving a PSE-capable active reset. This verifies
the state machine, not actual watchdog scheduling or completion. Top-level
vendor reset wrappers/retry scheduling and raw-result evidence remain pending.

## Top-level reset wrappers and periodic retry staged — 2026-10-22

prepare-reset-admission.py now pins cmm_mac_pci.c, renames the two original
hardware routines to private raw functions and routes the nested PSE->PDMA call
to raw PDMA. Public PSE/PDMA wrappers include reset-admission.inc: request the
explicit scope under the dedicated lock, reserve RESET, release lock for raw
hardware work and retire UNVERIFIED. Busy requests remain pending rather than
pretending a reset completed. The raw VOID return never publishes main readiness.

The existing queue/MCU/adapter assembler carries this stage, adds the drain
prototype to the staged adapter header and invokes drain after the existing
MlmePeriodicExec command-thread dispatch under MT7603+DMA_RESET_SUPPORT. It
updates final merged-source hashes. This supplies a real periodic retry hook,
not a proven deadline: worker/timer shutdown, suspended operation, main-inhibited
policy and adapter references remain required integration gates. Do not install
this candidate before mandatory-close/reset termination is proved.

Strict host execution of the shared wrapper fragment passed busy-START deferral,
PSE invoking raw PDMA once, public PDMA requested reentrantly during raw PSE
retained for next pass, explicit drain and no work after close latch. Pinned
bundle generation confirmed private nested call, one periodic hook and matching
final hashes. Evidence: Temp/iot-merged-adapter-07uv56fd/bundle-reset. ABI host
sanitizer fixture added, not run. Full raw hardware functions/target compilation,
reset result observation and shared exclusion with secondary BSS remain pending.
Existing separate beacon/reset-error bundle has not yet been merged into this
cmm_mac_pci.c; overlapping function edits must be reconciled explicitly next.
No production image/router state changed.

## Reset and beacon/error candidates unified — 2026-10-22

The shared radio queue assembler now invokes the existing radio-error assembler
and carries its reviewed files, not a replacement implementation. The only
shared cmm_mac_pci.c delta allowed is the pinned PDMA function and first MT
RT28xx_UpdateBeaconToAsic function. It verifies reverting those error-stage
functions yields the exact original, then applies them to the reset-wrapper
source, renaming the guarded PDMA body to its private raw entry. Arbitrary
additional overlap fails. Final records have one hash per path with provenance;
existing manifests retain false installation/lifetime/target/RF claims.

Initial local git-archive extraction failed the original enqueue blob identity;
no source gate was weakened. A new temporary source fixture was populated from
ls-tree plus binary cat-file --batch and each blob hash checked. Exact-source
assembly passed. Final hash/marker checks, queue composition, beacon-kickout and
PDMA-gate host fixtures passed strict GCC. The overlap functions in the final
file are verified equal to their checked error-stage versions, modulo the
reviewed PDMA private-name change. This is not whole-driver compilation.
Evidence: Temp/iot-unified-radio-9h9m7gcq/bundle-exact. Failed archive/bundle
fixtures retained for inspection; user source tree unchanged.

This supersedes the earlier unmerged beacon/reset-error bundle status. The
existing ABI queue-bundle invocation will assemble all these pieces; it has not
run for local edits. Secondary BSS admission, mandatory close/adapter retirement,
full target driver and runtime remain open. Continue those bindings rather than
creating another independent radio bundle.

## Secondary-BSS open admission staged — 2026-10-22

The unified assembler now keeps the already reviewed abort/refcount repairs in
private wr_iot_mbss_open_raw and wraps public MBSS_VirtualIF_Open with dedicated
adapter admission before any MBSS_OPEN mutation. NULL/main-netdevice inputs are
refused; UNVERIFIED/closing/reset-pending states cannot admit BSS_OPEN. The short
lock is released across vendor calls. Failure retires faulted; raw zero return
retires UNVERIFIED because ignored CR_ENABLE results are not hardware proof.
No new unconditional VIRTUAL_IF_DOWN rollback was introduced.

prepare-mbss-admission-check.py extracts the actual final raw wrapper and shared
admission fragment. Strict host base/MT_MAC/MT_MAC+HNAT cases passed refusal,
exclusive mutation, earlier open/virtual-up abort/reference failure behavior and
unverified software completion. Evidence: Temp/iot-unified-radio-9h9m7gcq/
bundle-mbss-open. Three equivalent ABI sanitizer cases added, not run.

This is source/host evidence only. Secondary close still has no admission or
retained teardown mechanism; CR_ENABLE-error cleanup, actual same-generation
readback and adapter lifetime remain unproven. Do not enable the partial bundle
or claim production IoT. Next bind mandatory BSS close without falsely completing
Linux ndo_stop when raw teardown was deferred or uncertain, and reconcile count/
last-interface close with adapter-wide ownership.

## Mandatory-stop semantics and trust-preserving teardown — 2026-10-22

Pinned Linux 4.4 net/core/dev.c:1394 clears __LINK_STATE_START before driver
stop; :1418 invokes ops->ndo_stop(dev) without inspecting its return value.
An -EBUSY return is not a retry contract and cannot establish that an IoT BSS
was stopped. A production wrapper must finish required teardown or pin all
remaining device/adapter/module resources in explicit recovery before returning,
with completed/uncertain status preserved for the activation controller. Admin
DOWN alone does not prove driver/RF quiescence.

Corrected selective-close admission: permit READY, UNVERIFIED and FAULT baselines
when no other ticket owns mutation, including with reset pending. Ticket now
captures prior phase/readiness. Successful BSS_CLOSE restores that trust level
and preserves main-down/reset intent; it cannot promote an unverified or faulted
main radio to READY. Failure remains FAULT. Last-reference close still requires
adapter-wide CLOSE, not this selective operation.

Strict host fixture passed all three prior trust levels and pending-reset
teardown without readiness promotion. This fixes the admission model, not actual
ndo_stop completion or netdevice/reference lifetime. Next implement the required
teardown/retained-resource composition with an atomic last-reference decision;
do not wrap the vendor ndo_stop with a simple failed-admission return.

## RTNL serialization for reset versus netdevice stop — 2026-10-22

Pinned net/core/dev.c asserts RTNL in __dev_open (:1313) before ndo_open (:1335)
and __dev_close_many (:1385) before ndo_stop (:1418). The driver already uses
RTNL in RtmpOSNetDevProtect/registration (os/linux/rt_linux.c). Reset drain now
uses rtnl_trylock before transition admission; on refusal it returns without
consuming pending scope. On accepted work it retains RTNL across raw reset and
releases it after ticket retirement. Adapter spinlock stays short. Request
wrappers release the spinlock before trying RTNL, avoiding reverse held-lock
order. A caller already holding RTNL also defers rather than recursively locks.

Strict host reset-wrapper fixture passed simulated externally held RTNL with
zero hardware mutation and preserved pending scope, retry after release, raw
PSE/PDMA requiring RTNL, reentrant request retention and all lock-release paths.
This prevents the modeled stop-joins-worker/worker-waits-RTNL cycle because the
worker never blocks on RTNL. Linux scheduling, full reset call-context audit,
actual target compilation and adapter lifetime remain unverified. IRQ/atomic
callers must not be assumed safe for mutex_trylock: every actual reset entry's
context still requires review before installing this candidate.

This is not global radio exclusion: direct radio-off/ATE, observation callers
and raw close lifetime still require consistent RTNL/transition admission.
Mandatory stop may use the kernel's existing RTNL ownership only after all
other ticket owners obey the same outer ordering; do not silently return busy
from ndo_stop. The source candidate remains excluded from production.

## Last-secondary close boundary confirmed — 2026-10-22

Read pinned c25283e mt76x3 ap/ap_mbss_inf.c MBSS_VirtualIF_Close and
common/cmm_cfg.c CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN (around 1081).
The secondary stop performs CR_DISABLE, queue stop, MBSS_CLOSE, HNAT dereg,
then VIRTUAL_IF_DOWN and module-reference decrement. The DOWN dispatcher
unconditionally decrements VirtualIfCnt and invokes rt28xx_close(main netdev)
when the count reaches zero. Consequently a secondary ndo_stop can be the
physical adapter shutdown after main administrative down. Treating every
secondary stop as selective BSS_CLOSE would leave transition state alive
across physical teardown and permit stale pending reset/lifetime assumptions.

Next implementation must select selective versus adapter-wide close before
raw mutations under the shared ownership protocol; audit all VirtualIfCnt
writers before relying on its value. Zero/invalid counts need explicit handling
rather than an unconditional decrement. Preserve mandatory ndo_stop teardown:
returning EBUSY is not retry because Linux ignores that return. RTNL excludes
the staged reset drain but does not alone prove exclusion of every vendor
writer, VERIFY user or adapter free path. No stop wrapper added until these
preconditions are bound. No build/test/device command run in this source audit.

Also enumerated reset calls: cmm_cfg.c:1728/1761 (private configuration),
cmm_mac_pci.c:2151 (fallback under !DMA_RESET_SUPPORT), :2432 (nested PSE),
:2598 (watchdog). The fallback must be included in context/config review;
its presence is not proof it compiles in the selected target configuration.

## Count-writer inventory and stop reservation candidate — 2026-10-22

Pinned mt76x3-wide git grep found VirtualIfCnt storage and plain INC/DEC/NUM
macros in include/rtmp.h:5151,10055-10057; all direct mutations in this tree
are cmm_cfg.c:1046 (first open),1049 (failed-first-open rollback),1063
(additional open),1081 (close). These macros have no intrinsic locking.
That inventory does not prove that every caller is covered by our owner.

Added wr_iot_radio_begin_stop to the shared candidate: zero count refuses
without mutation; count one requests adapter CLOSING then reserves CLOSE;
count above one reserves selective BSS_CLOSE. Busy last-close retains closing
intent so late completion cannot restore readiness. Caller must stabilize
count and prove this interface owns a reference, pin resources and complete
mandatory stop or retry internally; zero return is never completed ndo_stop.
No real stop entry bound, no vendor counter decremented by this helper.
No new tests or compilation run this turn; candidate remains unverified.

## Shared-count caller coverage expanded — 2026-10-22

Pinned mt76x3 call-site inventory shows five interface families, not only
main/MBSS: main rt_main_dev.c:129/180; MBSS ap_mbss_inf.c:145/196;
AP-client ap_apcli_inf.c:114/164; WDS ap_wds_inf.c:74/100; optional sniffer
rt_profile.c:1451/1478 under CONFIG_SNIFFER_SUPPORT. All use rt_os_net.h
VIRTUAL_IF_UP/DOWN wrappers and the same cmm_cfg.c counter dispatcher.
The inline DOWN wrapper returns VOID and discards dispatcher status. Thus
adding a failure return in the dispatcher alone cannot report an unsuccessful
mandatory close to the caller, and an underflow guard alone cannot establish
completed teardown. UP supplies rt28xx_open/close callbacks; a dispatcher-level
owner must avoid recursive admission around those physical callbacks.

The current candidate wraps main and MBSS open only. AP-client/WDS/sniffer
can still change shared count outside that owner. RTNL coverage of their actual
entry calls and configuration guards must be proved; a main/MBSS-only lock is
insufficient to classify last reference. Preferred integration point is the
shared dispatcher plus explicit wrapper lifetime/teardown result protocol,
with outer admission before each family's pre-dispatch mutations. Preserve
AP-client/WDS functionality; do not disable them merely to simplify IoT.
Next trace actual dispatch callers/registration and pre-dispatch mutations for
these families, then stage count/stop ownership in one merged candidate.
No source candidate bound to production and no build or device operation run.

## Shared dispatcher arithmetic guard staged — 2026-10-22

Added prepare-interface-count-guards.py pinned to cmm_cfg.c blob
cb3e9607326e473436862132b18de9679cc6c154. UP refuses UINT maximum before
increment; DOWN refuses zero before decrement/callback. Unified assembler
includes this stage and records count serialization as unproven. This avoids
arithmetic wrap only when caller concurrency is already controlled; guards
are not a lock, per-interface reference ownership or a completed stop protocol.
DOWN status remains discarded by the legacy VOID wrapper. No generated bundle,
compile or test executed this turn; production remains excluded. Next integrate
shared ownership and explicit last-close result/lifetime handling.

## Stop-reservation host cases passed — 2026-10-22

Extended check-radio-transition.c for begin_stop: zero count preserves epoch,
readiness and idle state; count two takes selective BSS_CLOSE and preserves
verified main state; count one enters CLOSING then reaches DOWN; busy BSS_OPEN
plus last-stop intent refuses a new ticket, repeated stop leaves epoch stable,
late completion cannot restore readiness and retry can reserve physical CLOSE.
Strict host command gcc -std=c11 -Wall -Wextra -Werror -O2 passed and executable
passed. This sequential injected model does not prove actual count stability,
caller ownership, kernel concurrency, hardware close or adapter retirement.
Python AST parse of counter preparer and unified assembler passed; this does
not execute source transformations or compile a generated driver. Next stage
actual dispatcher and family wrapper ownership, including stop completion.

## Exact counter-source transformation verified — 2026-10-22

Executed preparer on c25283e cmm_cfg.c obtained as exact Git blob. Candidate
contains precisely the two intended guards; each precedes the relevant counter
mutation. Removing those insertions reproduces original normalized text; source
bytes stayed unchanged. Manifest retains production/count-serialization false.
Evidence: Temp/iot-counter-stage-spp2g2oc/verification.json and candidate/.
First sandbox attempt failed creating nested Temp source directory (WinError 5);
approved local-only escalation completed verification. No target compile or
runtime claim. Source/fixture evidence retained, no deletion attempted.

## Auxiliary netdevice entry audit and failed-open references — 2026-10-22

rt_linux.c:1676-1677 maps supplied hook open/stop to ndo_open/ndo_stop;
AP-client registrations ap_apcli_inf.c:79-80, WDS ap_wds_inf.c:49-50,
monitor rt_profile.c:1492-1493. Normal Linux netdevice entry therefore uses
RTNL, but direct/vendor calls still need inventory. AP-client close performs
APC_CLOSE and HNAT dereg before DOWN; WDS stops queue/HNAT before DOWN;
monitor performs SNIFF_CLOSE/HNAT before DOWN. Dispatcher-only admission is
too late to exclude these mutations from other radio owners.

Found AP-client/WDS failed VIRTUAL_IF_UP returns leak the module reference
incremented at entry. Added exact-blob preparer prepare-auxiliary-open-refs.py
to balance only those failure branches and included it in unified assembler.
No successful-open or close behavior changed. Optional monitor has analogous
failure pattern, still pending a reviewed merge with adapter rt_profile edits.
Python syntax and whitespace checks passed; transform/host/target execution
not performed for this new stage. Production and router unchanged.

## Monitor reference repair and exact composition verified — 2026-10-22

Adapter preparer now balances failed Monitor_VirtualIF_Open UP references in
its existing rt_profile.c stage, preserving transition-lock free code. Executed
both auxiliary and adapter preparers on exact pinned blobs. AP-client/WDS
reverse-diff checks show only intended failure-reference repairs; monitor
branch and adapter-free insertion both present. Python syntax/whitespace passed.
Evidence Temp/iot-aux-ref-6h3p3gr8/verification.json. Initial fixture destination
AUX failed because it is a Windows reserved device name; rerun in auxiliary
succeeded using same source. Actual assembler uses aux-refs, not AUX.
No MIPS compile, injected driver runtime or device acceptance established.
Next complete outer family admission and mandatory-stop shared ownership.

## Unified counter/auxiliary/monitor composition passed — 2026-10-22

Executed full prepare-radio-queue-candidate.py against exact pinned driver
source. New counter and auxiliary stages merged with adapter/monitor, queue,
ACK, reset, beacon/error and MBSS stages without rejected overlaps. Verified
unique manifest paths and SHA256 for every final driver record. Retained false
production installation, target compile and count serialization fields.
Compiled and ran extracted final main-open/main-close host fixtures in base,
HNAT/AP-HNAT and IFUP_IN_PROBE variants (six strict GCC builds/executions).
All passed; primitives are injected, probe uses immediate-success case only.
Evidence Temp/iot-unified-radio-9h9m7gcq/bundle-counter-aux/
composition-verification.json and final manifest. This verifies composition
and existing wrapper scope, not auxiliary hardware behavior or complete driver
compilation. Actual stop admission, all family ownership, lifetime and IoT
network isolation remain unresolved; no production/image/device mutation.

## PCI removal lifetime boundary traced — 2026-10-22

Pinned tree exact-name invocation search found family open/close definitions
and declarations, not direct named calls; registration through function pointers
is the observed path. This is not proof against indirect calls.
rt_linux.c:1619 RtmpOSNetDevDetach uses unregister_netdevice, then frees netdev
ops; RtmpOSNetDevProtect wraps RTNL. pci_main_dev.c rt_pci_remove around
388-433 calls RtmpPhyNetDevExit, then RtmpRaDevCtrlExit, iounmap/release and
root netdev free. rt_main_dev.c:729-768 removes AP-client, WDS, MBSS, optional
monitor before protecting main unregister with RTNL. Whole removal does not
hold one continuous RTNL lifetime boundary across adapter destruction.

Therefore reset trylock RTNL cannot by itself pin pAd through remove/free;
a worker reaching reset after netdev unregistration may race destruction unless
worker/timer retirement is proved. Required removal protocol: publish removal
intent before family unregister, prevent new reset/VERIFY/open admissions,
retire producers and admitted operations without joining while holding a lock
they need, then free transition lock/adapter and unmap MMIO. Main/secondary
ndo_stop still must execute cleanup during removal, so a blanket rejection of
all tickets after marking CLOSING would be wrong. Do not install a removal
flag without matching mandatory-stop admission and drain semantics.
Next trace RtmpRaDevCtrlExit and worker/timer shutdown to choose the actual
quiescence point before adapter free. Source audit only, no runtime operation.

## Removal admission model staged — 2026-10-22

RtmpRaDevCtrlExit at rtmp_init.c:2431-2470 destroys semaphores/rings and calls
RTMPFreeAdapter; no new worker join in that function. Physical-close init_inf
contains timer/task exits at 888/998; init-failure path has separate 620/625.
Removal must prove those paths completed rather than assume destructor drains.
Added idempotent retiring latch to shared model: main-down epoch invalidation,
refusal of new start/open/verify/reset requests, continued selective/final stop
admission. Retiring survives DOWN and cannot be cleared by late success or
fresh START. It is not a resource reference, wait or worker quiescence proof.
Strict host fixture passed admitted-open retirement, duplicate retire epoch,
new-work refusal, selective then final close and no reopen after DOWN.
No actual PCI/remove hook bound yet; mandatory-stop/lifetime integration pending.

## Physical-exit removal intent bound in candidate — 2026-10-22

Adapter preparer now inserts retire under short transition lock at entry of
RtmpPhyNetDevExit, before all child removals and main unregister, releasing
lock before existing teardown. Manifest records phy_exit_retirement_intent_staged.
Exact-source preparer execution passed. Extracted final function strict GCC
host fixture passed AP-client/WDS/MBSS/monitor/main removal ordering with
injected primitives asserting retiring/main-not-ready and no held short lock.
Initial fixture lacked stddef.h for NULL; corrected fixture only and reran.
Evidence Temp/iot-aux-ref-6h3p3gr8/adapter-retire/check-phy-exit.c and executable.
This binds intent only: no worker/producer quiescence, active-ticket wait or
mandatory stop ownership claimed; no production installation/target compile.

## Worker termination failure is not quiescence — 2026-10-22

Physical close in rtmp_init_inf.c runs APShutdown, RtmpNetTaskExit, MlmeHalt,
RtmpMgmtTaskExit (:888), later disables RX/TX/IRQ, exits MCU/rings, clears
START_UP and releases timer list (:998). RtmpMgmtTaskExit in rt_rbus_pci_drv.c
:190 marks CmdQ STOPED, calls RtmpOSTaskKill, logs failure but continues and
sets queue UNKNOWN. Thus reaching its return is not unconditional join proof.

rt_linux.c __RtmpOSTaskKill (:921) has configuration-dependent behavior:
KTHREAD_SUPPORT joins with kthread_stop when pointer exists; legacy path can
fail KILL_THREAD_PID and skip wait_for_completion. Wrapper variant at3124
frees OS-task storage via RtmpOSTaskFree even when returned status failed;
separate variant at4578 directly returns the helper. Effective target macro/
wrapper selection and task lifetime require evidence before changing this.
Timer deletion implementation uses del_timer_sync (:191), but complete timer
producer/rearm coverage and ordering against resource destruction remain open.

Do not translate VOID RtmpMgmtTaskExit completion into successful retirement.
Next propagate a checked shutdown result through candidate close/free paths,
retain task/adapter resources on unjoined failure and define recovery; a local
free guard alone leaves the outer adapter destructor unsafe. No speculative
production change added. Source-only evidence, no runtime/compile this turn.

## Failed task-join storage retained in isolated candidate — 2026-10-22

Pinned config.mk defaults HAS_KTHREAD_SUPPORT=n (:119), emitting the macro
only when y (:379-380). No effective target rt_linux TU macro report found in
inspected local artifact directories; default is not final config proof.
Added prepare-task-join-retention.py pinned to rt_linux.c blob
db61215d188d82a50f3468747fff871318fc4b72. OS-task wrapper now frees storage
only after NDIS_STATUS_SUCCESS, preserving it after failed join. Other wrapper
variant unchanged. Included stage in unified candidate, not production.
This repairs one premature free but does NOT retain outer adapter/rings/MMIO:
checked failure propagation through MgmtTaskExit and close/remove is mandatory
before installation. Syntax/whitespace passed; transform/target execution for
this new stage pending. No device/build mutation.

## Failed-join wrapper execution verified — 2026-10-22

Executed task-retention preparer against exact pinned rt_linux source. Reverse
change restored original normalized text, establishing only intended wrapper
edit. Extracted generated RtmpOSTaskKill compiled strict GCC and passed injected
failure retaining pContent/no free, retry success freeing once, and absent
pContent returning failure without invoking kill/free. Evidence:
Temp/iot-unified-radio-9h9m7gcq/task-retention-check/verification.json.
Actual kernel kill/completion and target wrapper selection are not injected
fixture evidence. Next checked MgmtTaskExit result must keep STOPED rather than
publish UNKNOWN on failed join and propagate retention through close/remove;
existing VOID callers currently cannot enforce this, so production stays gated.

## Checked command-thread shutdown entry staged — 2026-10-22

Queue preparer now inserts wr_iot_command_task_exit_checked beside legacy
MgmtTaskExit; adapter header declares it. It marks STOPED under CmdQLock,
releases lock across kill/join, preserves STOPED on any non-success, publishes
UNKNOWN under lock only on success and refuses missing handles as unproven.
Legacy VOID path unchanged until outer close/remove failure propagation is
implemented; checked function covers command worker only, not WSC/timers/IRQs.
Exact helper text from preparer AST compiled strict GCC and passed injected
failed kill, successful retry and absent-handle cases; no lock held across kill.
Evidence Temp/wr-iot-command-stop.c and executable. Full transform/target ABI
not verified this turn. No production integration or adapter-lifetime claim.

## Close-result propagation and PM scope narrowed by artifact — 2026-10-22

Pinned rt28xx_close (rt_main_dev.c:215-236) calls VOID RTMPDrvClose then
returns zero; cmm_cfg.c final-reference DOWN ignores its callback result.
The legacy VOID DOWN wrapper drops dispatcher status too. Checked command
stop therefore needs a result path across all three layers, plus PCI remove
retention. Returning early only inside RTMPDrvClose is not a safe end-to-end fix.

Found direct PCI suspend/resume physical close/open calls at pci_main_dev.c
:123/:209 bypassing family wrappers; suspend continues to PCI power-down and
resume ignores failed open by returning zero. These functions and registration
are CONFIG_PM-guarded. Locally preserved #533 and #535 kernel-effective.config
line498 explicitly contain '# CONFIG_PM is not set', so PM is excluded for
those historical images. This reduces active integration scope for that config,
not for future boards/configs; require the same effective-config check for a
new candidate before treating PM as excluded. KTHREAD/OS_ABL TU selection
remains unknown. No PM rewrite added and no device assumption made.

## Actual rt_linux translation-unit macro probe prepared — 2026-10-22

Added check-task-config.py to read exactly one .rt_linux.o.cmd, require the
requested compiler and exact driver/os/linux/rt_linux.c source, replay non-output
Kbuild flags with -E -dM and report KTHREAD_SUPPORT, OS_ABL_FUNC_SUPPORT,
CONFIG_PM, RTMP_TIMER_TASK_SUPPORT and WSC_INCLUDED. It records command/source
hashes, returns failure on missing/ambiguous evidence and has a 60-second bound.
No shell execution or object/source output. It is standalone, not wired to
production CI until its parser/control cases and target environment are checked.
Syntax passed; no actual target preprocessing ran. This addresses the missing
TU-specific evidence needed before checked shutdown integration, not quiescence.

## Task TU probe controls passed and CI collection staged — 2026-10-22

Added check-task-config-selftest.py; six synthetic host controls passed valid
valueless/defined-zero macros, missing/ambiguous command, compiler mismatch,
wrong source and preprocessing failure. Evidence Temp/iot-task-config-controls-
jhwrwmi7/summary.json. Synthetic source/host GCC explicitly not target evidence.
Firmware workflow now stages actual rt_linux probe after capacity probes and
stores mt76x3-task-config.json with existing always-uploaded evidence. Missing
or invalid target evidence fails that step; no workflow dispatched. Actual
MIPS macro report still pending future authorized publication/CI. Whitespace
and shell continuation checks passed. Next actual checked close-chain integration.

## Shutdown candidate overlap resolved and final extraction checked — 2026-10-22

Full assembly initially refused rt_linux.c overlap between task retention and
older netdev-create failure repair. Extended explicit merge to transplant only
RtmpOSNetDevCreate from error stage into task-retention source; restoring that
function must reproduce exact baseline, and existing target function must match
baseline before insertion. Unknown overlap/deltas still rejected.
New full bundle assembly passed. Unique paths and every manifest hash matched;
both rt_linux repairs present. Extracted checked command-stop from FINAL merged
source compiled strict GCC and passed existing injected failure/retry/missing
handle cases. Evidence Temp/iot-unified-radio-9h9m7gcq/bundle-shutdown-merged/
shutdown-composition-verification.json. Initial incomplete bundle-shutdown-checked
retained for diagnosis, no successful manifest claimed. Outer close/free result
propagation remains unbound; no target build, production/image/device claim.

## WSC failed-join resources retained in candidate — 2026-10-22

Close before command join already performs APShutdown, MlmeHalt, table exits
and tasklet exit; retrying whole RTMPDrvClose is not established idempotent.
WscThreadExit is BOOLEAN (wsc.c:8951), not VOID, but legacy MgmtTaskExit ignores
it. Original WSC code logs failed kill then frees buffers/locks used by worker.
Task-retention stage now also patches exact wsc.c blob
3281fb30199c425e67916ae4796242b6618178ea: non-success returns FALSE before
resource frees. Exact-source transformation and Python syntax passed; no WSC
host/target execution this turn. Shared assembler includes WSC output.
Evidence Temp/iot-unified-radio-9h9m7gcq/task-wsc-retention. This protects local
WSC resources only; outer adapter retention, WSC result consumption and staged
resume after partial shutdown still mandatory. No production installation.

## Resumable checked management joins staged — 2026-10-22

Added joined_workers mask to adapter transition candidate, initialized fresh
and cleared only on admitted fresh START. New wr_iot_mgmt_exit_checked requires
current CLOSE operation/serial and one caller per ticket, drops short lock
before joining, records command success and WSC success separately, and retries
only unfinished stages. Does not retire CLOSE or authorize freeing hardware.
WSC inclusion follows effective WSC_INCLUDED; it uses guarded WscThreadExit.
Legacy close remains unchanged pending propagation of this result and staged
pre/post-worker teardown. Ticket owner must remain held across retries.
Exact helper text compiled strict host GCC and passed command failure (no WSC),
command success/WSC failure, WSC retry without repeated command kill, repeated
success without duplicate teardown and invalid serial refusal. Evidence Temp/
wr-iot-mgmt-stop.c. Injected joins do not prove WSC cleanup or target lifetime.
No production binding/target compile/device mutation.

## Resumable physical-close source candidate staged — 2026-10-22

Added prepare-checked-close.py pinned to rtmp_init_inf.c blob
232b6c3d68224e896aaf9364aad871b787bdc578. It preserves legacy RTMPDrvClose
and adds checked variant with current CLOSE-ticket validation, pre-join stage
once, checked command/WSC joins, then post-join cleanup once. Adapter state
stores shutdown_stage and clears it with joined-worker bits only on fresh START.
A failed join returns before post-join resource release and keeps the ticket/
stage for continuation; it does not retire CLOSE or free outer adapter.
Exact-source generation, Python syntax and whitespace passed. Evidence Temp/
iot-unified-radio-9h9m7gcq/checked-close-stage. No whole-function compile or
hardware success claim: vendor VOID cleanup and radio-off error logging remain,
pre-join resource accesses versus live worker need audit, and actual legacy
callers plus PCI remove retention are not replaced. Single caller per ticket
required. This source candidate remains excluded from production.

## Physical-close base host retry cases passed — 2026-10-22

Extracted checked-close function compiled with injected primitives and minimal
base configuration. Failed join left stage1 and skipped final cleanup; retry
ran no second preparation, completed post-cleanup once and reached stage2;
subsequent call repeated neither cleanup nor join. Strict GCC passed after
fixture TRUE definition and explicit net_dev unused cast (also in preparer for
configs without IRQ use). CRLF prevented first fixture insertion, corrected.
Evidence Temp/wr-iot-physical-close.c/exe. This is base conditional configuration
only: AP/PCI/WSC branches and real headers are not compiled by this fixture.
Prejoin live-worker safety and actual callers/free retention remain open.
No production/device mutation.

## AP/PCI checked-close host branches and invalid-stage guard — 2026-10-22

Extended extracted-function fixture with CONFIG_AP_SUPPORT, RTMP_MAC_PCI and
RTMP_PCI_SUPPORT plus injected operations. Passed AP preparation once, no PCI
cleanup on failed worker join, PCI cleanup once after successful retry and no
repeat on completed call. Base and AP/PCI variants also passed invalid stage3
refusal after replacing >=2 success with explicit >2 failure / ==2 success in
preparer. Evidence Temp/wr-iot-physical-close[-ap-pci].c/exe.
Fixtures use synthetic types, IRQ flag false and radio-off success; no real
headers, MT_MAC, IRQ-release execution, failed-radiooff or hardware proof.
Inherited radio-off failure logging still cannot justify hardware readiness
or resource safety. Next actual close result propagation and prejoin safety
review; production remains excluded.

## Checked close refuses failed PCI radio-off — 2026-10-22

Checked-close preparer now retains stage3 and returns failure after vendor
radio-off failure diagnostic, before downstream IRQ/ring/resource release.
Stage3 refuses later calls, so no blind repetition of partially completed
post-join hardware operations. Generated AP/PCI fixture with injected failure
passed no UserCfg final cleanup, no repeated PCI work, and failure retention.
Evidence Temp/iot-unified-radio-9h9m7gcq/checked-close-radiooff/check-radiooff.c.
After fixture, moved inserted failure return below existing diagnostic to keep
logging; syntax checked, final log-preserving ordering needs regeneration.
This is not hardware recovery or safe PCI remove by itself: outer caller must
retain mappings/adapter and provide an explicit recovery path before deployment.
IRQ-active and real target headers remain unverified. Production unchanged.

## Repeatable final-assembly checked-close fixture passed — 2026-10-22

Saved synthetic AP/PCI template and prepare-checked-close-check.py extractor
in tools/iot; unified assembler hashes template/preparer inputs. Regenerated
full bundle-close-final with checked close, WSC retention and management joins.
Extracted final function via committed-path tools, strict GCC build/run passed
join failure/retry/completed/invalid-stage/radiooff-failure cases. This includes
final diagnostic-preserving failure ordering. Evidence Temp/iot-unified-radio-
9h9m7gcq/bundle-close-final and Temp/wr-iot-final-close.c/exe.
Staged same final-source fixture in ABI workflow with sanitizers, not executed
in CI. Actual target headers and outer close/remove binding still unverified;
fixture is synthetic AP/PCI, not device proof. Production/router untouched.

## Physical-close result bridge staged — 2026-10-22

Adapter preparer inserts separate wr_iot_rt28xx_close_checked next to legacy
rt28xx_close, using physical-close-result.inc. It rejects NULL device/adapter/
ticket, propagates checked DrvClose non-success as -1, and performs WIFI_DIAG
exit only after software success once via close_notified latch. Fresh START
clears latch; caller exclusively owns CLOSE ticket and pins lifetime/retries.
Legacy physical callback unchanged until dispatcher/remove retention is bound.
Strict host check-physical-close-result.c passed invalid inputs, failure without
diagnostics/latch, success and repeated success with one diagnostic cleanup.
Injected lower close means actual ticket validation/hardware not proven by
this test. Preparer syntax/whitespace passed; new generated composition pending.
Next propagate checked bridge through final-reference DOWN and outer lifetime,
with explicit failed-close quarantine/recovery rather than false completion.

## Checked virtual-down result chain staged — 2026-10-22

Added virtual-down-checked.inc and declaration/generated inclusion in counter
stage. Candidate validates current CLOSE/BSS_CLOSE ticket. Selective down needs
count>1 and decrements once; last down needs count1, decrements once before
physical checked close, and stores pending stage so retry at count0 does not
decrement again. Completion is remembered for same ticket; new close ticket
resets this stage. Physical failure propagates, keeping owner/resources with
caller; it never finishes ticket or frees adapter. Legacy DOWN untouched.
Strict check-virtual-down.c passed selective/no callback, repeated selective,
last failure/count0, stale ticket refusal, successful retry and no double down.
All count writers must share owner; real wrapper/PCI retained resources and
single caller per ticket remain prerequisites. Preparer syntax/whitespace passed;
new combined generation/target headers not yet verified. No production/device.

## Composed final down/physical-close chain host-verified — 2026-10-22

Full bundle-down-chain generation passed. Added repeatable prepare-close-chain-
check.py extracting checked DrvClose and final bridge/down fragments from the
assembled driver. It also verifies actual newline/include in cmm_cfg.c.
Strict GCC with FINAL bundled header passed integrated last-reference decrement,
failed join retained count0, stale ticket rejection, join retry without second
preparation, no double down and radiooff failure without downstream cleanup or
repeated PCI operations. Worker/hardware primitives remain injected.
Evidence Temp/wr-iot-down-chain.c/exe and bundle-down-chain. Staged sanitizer
version in ABI workflow, not executed there. Actual family wrappers, all count
writers, ndo_stop completion/recovery and PCI removal retention remain unbound;
no full MIPS driver or device acceptance claim. Production unchanged.

## Per-interface reference evidence checked — 2026-10-22

Inspected pinned wifi_dev definition (rtmp.h:1760 onward), MBSS_Open (:351)
and MBSS_Close (:410) plus ioctl dispatch ap_cfg.c:14928 onward. Beacon intent
bBcnSntReq is set by MBSS_Open BEFORE VIRTUAL_IF_UP completes and cleared by
MBSS_Close, with optional AirPlay behavior. It is not an acquired-count ownership
bit. wifi_dev interface identity/security/allow_data_tx fields do not supply
proof of successful VIRTUAL_IF_UP ownership in the inspected definition.
netif_running is also insufficient during ndo_stop because kernel has already
cleared START. Thus neither can authorize decrementing VirtualIfCnt.

Required bookkeeping must identify netdevice plus generation, set acquisition
only after successful UP, undo failed-open owned acquisition, and consume once
on DOWN while retaining pending last-close state across failure. It must survive
administrative main-down without relying on reset-reinitialized MBSS memory,
and clear only after callers/queued references retire. Do not infer ownership
from count>0 or beacon intent. Next choose adapter-owned reference bookkeeping
and bind it to all five families before redirecting legacy DOWN. Source-only
audit, no production/device changes.

## Per-registration interface-reference bookkeeping model — 2026-10-22

Added interface-reference.h with device identity, registration generation,
monotonic acquisition token and IDLE/RESERVED/OWNED/CLOSING phases. Only actual
successful vendor UP marks OWNED; later setup failure must close/rollback this
owned reference. Failed UP returns IDLE without a DOWN. Close consumes once
only after checked DOWN success; failure keeps CLOSING. Old tokens, wrong device
or registration generation refuse without mutation; wrap cannot reuse token0.
Registration generation is distinct from radio epoch: reset/main-down must not
erase administratively owned references. Reinitialization requires quiescent
registration, never a live record. Caller holds common lock and pins lifetimes.
Strict persistent check-interface-reference.c passed failed-UP, duplicate/stale
close/open completion, wrong identity/generation and token exhaustion cases.
This is bookkeeping model only; storage mapping/capacity and actual five-family
UP/DOWN binding remain unimplemented. No production/image/device claim.

## Adapter-lifetime interface reference storage staged — 2026-10-22

Pinned rtmp_def.h:531 defines WDEV_NUM_MAX from HW_BEACON_MAX_NUM, MAX_WDS_ENTRY,
MAX_APCLI_NUM, MAX_P2P_NUM, MAX_MESH_NUM; adapter wdev_list uses it (:4782).
Candidate adds independent wr_iot_interface_refs[WDEV_NUM_MAX+1] in adapter
alongside transition owner, with extra monitor slot since monitor is absent
from that formula. Registration-generation counter and all idle records are
initialized at final successful adapter publication, after failing allocation
branches. They are not placed in reset-reinitialized MBSS memory or reset at
radio START. Pool admission must refuse full capacity rather than overwrite.
Exact adapter preparer generation confirmed header include, storage fields and
init fragment; syntax/whitespace passed. Evidence Temp/iot-unified-radio-
9h9m7gcq/adapter-interface-storage. Real target memory/layout/compile and actual
registration mapping/retirement remain unverified. No production/device change.

## Interface registry capacity/reuse helpers checked — 2026-10-22

Added interface-registry.h: caller-locked bounded slot registration refuses
duplicate device/full pool/exhausted generation without advancing sequence;
lookup requires identity+generation; release refuses RESERVED/OWNED/CLOSING.
Caller must prove queued callback/reference quiescence before releasing IDLE:
helper state is not that proof. Slot reuse receives new monotonic generation,
so old registration callbacks cannot match reused pointer. Registry is carried
with adapter candidate storage/header; real registration hooks remain pending.
Strict check-interface-registry.c passed capacity/duplicate, active release
refusal, consume/release/reuse, stale generation and sequence exhaustion.
Initial fixture-only uninitialized dummy int warning fixed; no behavior claim
about real netdevice lifetime. Syntax/whitespace passed. Target compile and
registration/unregister/refcount integration still unverified; production unchanged.

## MBSS registration bridge bound in source candidate — 2026-10-22

Shared RtmpOSNetDevAttach installs ndo callbacks then chooses register_netdev
or register_netdevice via needProtcted; no typed adapter parameter. Existing
reviewed MBSS_Init candidate already checks attach failure, unlike original
AP-client/WDS/monitor paths. Added driver-side wr_iot_netdev_attach_checked:
reserve registry slot under short lock before OS publication, release lock
across attach/RTNL, release idle reservation on failed attach, reject retiring/
full/duplicate before publication. Caller serializes construction vs removal.
Unified assembler redirects ONLY reviewed MBSS_Init attach call to this bridge
and updates final hash; legacy other families remain unchanged.
Persistent strict host bridge test passed prepublication visibility, failed
attach rollback, retry new generation, duplicate/full/retirement refusal.
Syntax/whitespace passed; final composed MBSS generated fixture and real
registration callbacks/target headers still pending. Successful unregister
registry retirement remains unbound; do not enable production before all-family
lifetime and constructor error cleanup paths are complete.

## Final MBSS constructor plus registry composition passed — 2026-10-22

Full bundle-registry-attach generated successfully. Added repeatable extractor
prepare-mbss-registry-check.py: replace prior init fixture function with FINAL
MBSS_Init, include final registry attach fragment and header, track occupied
records across constructor failure scenarios. Strict GCC host execution passed
wdev registration failure, OS attach failure and success; failed current BSS
private ops/device freed once, successful earlier BSS retained and occupied
registry count equals successfully beacon-initialized interfaces. Lock released
at every checked boundary. Evidence Temp/wr-iot-mbss-registry.c/exe and full
bundle-registry-attach. Sanitizer ABI equivalent staged, not run in CI.
Injected constructor primitives are not Linux register/unregister or lifetime
proof; actual successful unregister record retirement and other families remain
next. No production/image/device change.

## MBSS unregister kernel/vendor lifetime boundary traced — 2026-10-22

Pinned MBSS_Remove (:185 onward) deinitializes beacon buffer before netdevice
unregister, then wraps RtmpOSNetDevDetach in RtmpOSNetDevProtect, unregisters
wdev index, frees netdevice and clears if_dev. Kernel unregister_netdevice_queue
(dev.c) schedules net_set_todo; rtnl_unlock (rtnetlink.c:79) calls
netdev_run_todo, which runs rcu_barrier and netdev_wait_allrefs. Thus the return
from RtmpOSNetDevProtect(0), not just Detach, is the observed kernel-reference
retirement boundary for this path. Vendor queued pointers still need separate
ownership/producer drain; kernel netdevice ref wait is not proof of those.

rtmp_wdev_idx_unreg (tx_rx/wdev.c:30) only clears wdev_list under irq_lock; it
has no vendor-worker drain. Beacon deinit (wdev.c:133) returns FALSE if MT beacon
is not idle; MBSS_Remove ignores this return. Consequently registry release
cannot be safely installed as an unconditional line after Detach or index
unregister. Required checked removal checkpoints: mandatory stop completion,
kernel unregister completion, vendor/beacon quiescence, record consumption,
then wdev/netdevice release. Record unregister progress so retry does not call
unregister twice. No actual ordering rewrite added without these results.
Source audit only; no target/runtime operation this turn.

## Published-registration removal milestones gated — 2026-10-22

Reference record now tracks published/removing/removal_stage, initialized fresh.
Attach bridge marks published after successful OS registration. Removal intent
blocks new acquisition; kernel-done requires consumed/IDLE reference, vendor-
done requires kernel-done, and published-record release requires both. Failed
unpublished attach still releases idle reservation without pretending unregister.
Milestone helpers record caller-proven events, not perform or prove kernel/
vendor synchronization. No real unregister binding yet.
Strict reference, registry and attach bridge host checks passed; registry adds
active-close kernel-done refusal, stage ordering, duplicate kernel completion,
no new acquisition during remove and no early published release. Producer/
callback drain and actual beacon handling remain required before runtime use.
No production/image/device change.

## MBSS open acquisition bound to registration record — 2026-10-22

Final MBSS admission wrapper now looks up published device registration under
shared transition lock, refuses missing/removing/non-IDLE record, reserves its
acquisition token atomically with BSS_OPEN ticket and calls reviewed raw open.
On raw error the record returns IDLE; on zero it becomes OWNED because reviewed
raw paths have acquired vendor UP even though CR_ENABLE hardware success is
still unchecked. Unverified radio completion remains unchanged. A failed
reservation cancels only the just-admitted unstarted ticket under same lock.
Removal can invalidate radio readiness but cannot erase an acquired reference.

Full bundle-mbss-reference assembled. Updated final-source MBSS fixture passed
strict base/MT_MAC/MT+HNAT variants, asserting IDLE for refusal/open/UP failures
and OWNED only on success, preserving abort/module refs. Evidence Temp/iot-
unified-radio-9h9m7gcq/bundle-mbss-reference/check-mbss-reference.c and exes.
No full target headers/device proof. Actual MBSS close consumption, other-family
ownership and retained-resource/remove paths remain pending; production gated.

## Checked MBSS close consumes reference once — 2026-10-22

Added separate wr_iot_mbss_close_checked beside legacy close in assembler.
Current CLOSE/BSS_CLOSE owner identifies published record; acquisition changes
OWNED->CLOSING with owner serial. Stages check CR_DISABLE, direct MBSS_Close
result (legacy ioctl discarded it), queue/HNAT steps once, then checked DOWN.
Failed DOWN retains CLOSING/stage3 for retry; success consumes reference and
module ref exactly once. Repeated same-owner completed call returns without
another decrement. Uncertain CR/MBSS failure quarantines stage5, not blind retry.
Record reservation clears old close progress on a later acquisition.
Strict persistent host cases passed base/MT/MT+HNAT, injected DOWN failure and
retry, stale owner refusal, one-time module decrement and CR/MBSS error paths.
No real CR/hardware/readback proof; legacy ndo_stop remains unredirected until
retained-resource continuation and mandatory-stop semantics are integrated.
New full generated composition/target compile pending. No production/device change.

## Final MBSS open-to-close bookkeeping chain passed — 2026-10-23

Full bundle-mbss-open-close generation passed. Added repeatable extractor
prepare-mbss-open-close-check.py combining FINAL raw/admitted open, checked MBSS
close and virtual DOWN with final registry/transition headers. Strict base,
MT and MT+HNAT cases passed failed UP/no count acquisition, successful UP/count2,
selective close/count1, reference/module consume once and repeated close no-op.
Physical close is not called for selective case. IO/MBSS_Close/worker semantics
remain synthetic, not hardware or real target-header proof.
Initial fixture macro lacked VOID* cast; later OPEN-only ioctl assertion failed
on CR_DISABLE; fixed fixture mapping, stopped failed session and reran all three
successfully. Evidence Temp/iot-unified-radio-9h9m7gcq/bundle-mbss-open-close/
check-open-close-owner.c and check-owner exes. Sanitizer ABI equivalent staged,
not executed in CI. Legacy ndo_stop retention/recovery, other families and
actual unregister/vendor drain remain open. No production/router mutation.

## Last-MBSS physical-close chain host-verified — 2026-10-23

Added repeatable final-source prepare-mbss-last-close-check.py combining checked
MBSS close with final virtual DOWN, rt28xx bridge and DrvClose. Strict host test
passed last MBSS after simulated main-down: failed join leaves count0 but retains
CLOSING acquisition/module reference; successful continuation consumes once,
without repeating MBSS/preparation. Injected radio-off failure keeps reference/
module held and refuses repeated partial PCI cleanup. Evidence Temp/iot-unified-
radio-9h9m7gcq/bundle-mbss-open-close/check-last-close.c/exe.
Sanitizer ABI equivalent staged, not run. Worker joins, MBSS_Close and hardware
are injected; this does not prove actual adapter pinning during PCI unbind,
mandatory ndo_stop completion or runtime cleanup. Those bindings remain open;
no production, workflow dispatch or device mutation.

## Target-toolchain availability rechecked and TU evidence preservation added — 2026-10-23

Read-only local inventory found wsl.exe but --list --quiet returned installation
usage, not installed-distribution evidence. Docker/clang absent from PATH;
no actual .rt_linux.o.cmd or MIPS compiler executable found in inspected local
#533/#535/.working-build-474/source-backup paths. This is scoped inventory,
not proof none exists elsewhere. #535 mt76x3 capacity report confirms limit16
and MAX_APCLI_NUM1, but has no rt_linux lifecycle macro evidence.

Task-config probe now preserves exact Kbuild command bytes, actual preprocessing
argv and stdout macro artifact/hashes alongside JSON, including preprocessor
failure evidence. Existing always-upload directory covers these future files.
Six synthetic host controls passed again with new artifact/argv assertions;
evidence Temp/iot-task-config-controls-0cbvt2ag. Actual MIPS flags/build still
pending future CI; no workflow dispatched, system installed or router changed.
Continue independent actual lifecycle integration; do not call host proof MIPS.

## Beacon disable is not DMA/TxS retirement — 2026-10-23

Pinned mbss_cr_disable clears secondary TBTT/queue-start bits and returns;
reviewed candidate adds short BcnRingLock serialization but deliberately no
flush/completion wait. BCM state becomes IDLE in tx_rx/txs.c BcnTxSHandler
(:98) on TxS, but also in reset and watchdog/recovery paths (cmm_mac_pci.c:2082,
cmm_asic_mt.c:1394 and AP initialization). IDLE alone is not proof that all
prior-generation TxS callbacks retired. TxS callback selects MBSSID by Priv
BSS index, not registration generation; pointer-generation registry checks
cannot distinguish an old hardware completion after BSSID-slot reuse.

Do not mark registry vendor_done from CR_DISABLE success or one IDLE sample.
For dynamic MBSS removal/reuse, required evidence includes blocked new beacon
submission, completed DMA/ring work and retired TxS delivery for that index,
under the same adapter lifetime. Full adapter IRQ/tasklet shutdown may provide
a boundary on final close, but selective close needs per-BSS retirement or a
no-reuse-until-adapter-restart rule explicitly accepted in the design. Current
full IoT requirement is unchanged; no limited behavior substituted or installed.
Next trace beacon DMA and TxS queue flushing/completion paths, then bind a real
retirement event before allowing unregister slot reuse. Source audit only.

## Beacon completion paths do not yet provide selective retirement — 2026-10-23

At pinned source `c25283e915a2a00a763774dd255b14aff997285e`,
`RTMPHandleBcnDmaDoneInterrupt` (`common/cmm_data_pci.c:2663-2760`) advances
the shared beacon ring under `BcnRingLock`, unmaps completed DMA packets and
clears each ring-cell packet pointer. It derives a BSSID index from TMAC
`own_mac`, but records only `BCN_TX_DMA_DONE` and a TSF sample. This is a DMA
completion path, not a TxS retirement acknowledgement for a registration
generation. Its index selection also requires bounds/lifetime review before
using it for per-BSS accounting.

`BcnTxSHandler` (`tx_rx/txs.c:77-115`) takes `Priv` as a BSSID index and writes
`BCN_TX_IDLE`. `ParseTxSPacket` (`txs.c:676-770`) dispatches that handler by
packet type after `RemoveTxSStatus`; the observed callback has neither a
registration generation nor a queue-drain barrier. `ExitTxSTypeTable` sets
`TxSValid=FALSE` for the whole adapter, so it cannot serve as a selective
IoT-BSS stop while the main BSS stays up.

`APCheckBcnQHandler` (`hw_ctrl/cmm_asic_mt.c:1338-1394`) does poll the beacon
flush registers, but it is a recovery path that re-enables beacon start and
forces IDLE. Original timeout branches continue; the separate candidate
guards return on timeout. This path does not prove old TxS callbacks retired.

Consequently, do not call `wr_iot_interface_registry_vendor_done` or reuse a
published BSSID index based on the existing DMA interrupt, IDLE state or
recovery flush alone. The next implementation gate is an explicit per-BSS
producer-stop and completion protocol, including TxS callback quiescence,
with adapter lifetime pinned. If hardware cannot provide that boundary, keep
the index reserved until a verified adapter-wide shutdown/reinitialization;
that fallback needs product acceptance before dynamic IoT reuse is claimed.
This is source evidence only; no driver binary or router was changed.

## Beacon TxS PID reuse blocks a naive generation tag — 2026-10-23

Pinned `ap/ap_connect.c:127` assigns `mac_info.TxSPriv = apidx` for beacon.
`mac/mt_mac.c:1009-1011` passes that value to `AddTxSStatus` for the enabled
per-packet-type host status. `tx_rx/txs.c:774-795` stores the `Priv` in a
256-entry table addressed by the eight-bit `TxSPid`; if the selected entry is
still `TXS_USED`, the code increments `TxSFailCount` but **overwrites** it and
advances the wrapping PID. `RemoveTxSStatus` (`:798-813`) clears the slot and
returns its currently stored `Priv`; it does not check that the response
belongs to the allocation that originally held this PID. `ParseTxSPacket`
(`:676-770`) ignores the removal result and dispatches by those returned
fields. The same removal code also reads `TxRate` using current `TxSPid`
instead of the completed `TxSPid`; that is a separate status-data bug, not a
retirement signal.

Therefore, simply packing registration generation into `TxSPriv` would not
make a late completion distinguishable after PID wrap or occupied-slot
overwrite. Before any per-BSS completion counter can authorize
`vendor_done`, the candidate needs a checked PID allocation and an explicit
overflow/unknown-status policy; all producers of TxS PID must be included.
The completion path must account for missing/late reports and prove quiescence
after beacon submission stops. A timeout must quarantine the slot rather than
declare it retired. This is a design gate, not a working implementation.

## TxS ownership audit before changing the global allocator — 2026-10-23

The pinned source has four `AddTxSStatus` call sites, all in `mac/mt_mac.c`
(`:973`, `:1009`, `:1291`, `:1326`): management/per-packet and data paths can
share the same 256-entry PID space. The single completion entry is
`common/cmm_data.c:611` -> `ParseTxSPacket` -> `RemoveTxSStatus`; there is no
observed alternate per-BSS completion queue. `RemoveTxSStatus` returns success
unconditionally even when the slot was unused, and `ParseTxSPacket` does not
check that return. The TxS type registration lock is released before the
beacon callback (`txs.c:761-764`), so it is not a callback-quiescence barrier.

Any real allocator correction must cover all four submission paths and the
common parser together, synchronize metadata access with a dedicated lock,
reject unknown/duplicate responses, and define what hardware guarantees when
the eight-bit PID is reused after a completed report. If that guarantee cannot
be established, a counter or `Priv` tag must not authorize BSS slot release.
Keep the IoT candidate unbound until this condition and the beacon producer
stop/DMA drain are proved in the target build and, later, on the router.

## Pinned TxS parser correction staged in partial candidate — 2026-10-23

`tools/iot/prepare-txs-status-candidate.py` requires original `tx_rx/txs.c`
blob `ece66c6ef0263a07015783f620fb968d065fc36f`. It stages three narrow
changes: reject an out-of-range or unused completion PID before dispatch,
read `TxRate` from the completed PID rather than the allocator's next PID,
and clear that slot after copying its metadata. The unified partial assembler
now carries `tx_rx/txs.c` as stage `txs-status` and records explicit false
claims for PID collision resolution and callback quiescence.

Local exact-source stage and unified partial assembly completed in separate
workspace directories `iot-txs-candidate-20261023` and
`iot-unified-txs-20261023`. Reviewed generated diff contains only the parser
and removal changes described above. This is not synchronized against
concurrent AddTxSStatus/RemoveTxSStatus, does not prevent occupied PID
overwrite, and has no MIPS compile or runtime evidence. Do not install it as
a production fix in isolation or treat it as a BSS-retirement proof.

## Extracted TxS removal behavior checked — 2026-10-23

`tools/iot/prepare-txs-status-check.py` extracts the actual staged
`RemoveTxSStatus` body from the assembled `driver/tx_rx/txs.c` into a host
fixture. The fixture differentiates the completed PID's `TxRate` from the
allocator's next PID and exercises first completion, duplicate completion and
unused PID. Local MinGW GCC with `-std=c11 -Wall -Wextra -Werror -O2` passed:
`TxS completed PID, duplicate and unused cases passed`. The same generated
fixture is staged after unified assembly in `band-steering-abi.yml`, where
Linux GCC address/undefined sanitizers will run after the workflow is pushed.
No GitHub workflow has run for this local edit. The host fixture does not test
`ParseTxSPacket`, concurrency, hardware PID reuse or target ABI; those gates
remain open. Evidence files are sibling workspace
`iot-txs-status-check-20261023.c/.exe` and `iot-unified-txs-20261023`.

## TxS status metadata lock staged — 2026-10-23

The exact-blob TxS stage now also requires pinned `mt_mac.h` blob
`30de2ef29743fda3c600e4e47448165ed24dc81e` and adds
`TxSStatusLock` to `TXS_CTL`. `InitTxSTypeTable` allocates it before status
table initialization; `ExitTxSTypeTable` frees it after the existing type
table cleanup. `AddTxSStatus` reserves/copies metadata/advances PID under one
IRQ-safe short lock and returns its saved PID; `RemoveTxSStatus` checks state,
copies fields and clears state under that same lock, releasing it on both
success and failure. No handler is called under the new metadata lock.

Reassembled the separate partial driver from pinned source into sibling
`iot-unified-txs-lock-v2-20261023`; generated diffs show only the described
header and TxS source changes for this stage. The extracted actual Add/Remove
functions compiled and ran with strict local MinGW GCC, covering returned PID,
wrap at 255, correct completed-slot rate, duplicate/unused rejection and lock
release on each path. This is a host fixture with a model lock, not a target
concurrency or IRQ/lifecycle proof. Occupied PID overwrite is **still present**;
TxS type-table shutdown and adapter lifetime are not synchronized by this
lock. Do not ship or use it as selective BSS retirement proof yet.

## Occupied TxS PID overwrite prevented in isolated candidate — 2026-10-23

Pinned `mac/mt_mac.c` blob `8aa1a977e043cb6060990dcc89a5ebe605af0918`
has exactly four `AddTxSStatus` callers. The isolated candidate changes the
shared allocator to return status plus an out-PID, scans up to 256 entries for
an unused PID under `TxSStatusLock`, and never overwrites a `TXS_USED` record.
When full, it increments `TxSFailCount`, returns failure without altering the
caller's out-PID, and all four TMAC construction sites leave `pid=0` and set
`tx_status_2_host=0` for that packet. The header prototype is updated with
the implementation. The explicit manifest claim is only
`txs_occupied_pid_overwrite_prevented=true`, while
`txs_pid_reuse_safety_proved=false`.

The extracted actual Add/Remove functions passed strict local GCC checks for
free allocation, skipped occupied slot, wrap at 255, full-table failure,
correct completed rate, duplicate/unused rejection and modeled lock release.
The unified partial bundle was regenerated at sibling
`iot-unified-txs-no-overwrite-v2-20261023`; the candidate remains uninstalled
and not target compiled. A full table intentionally loses a host TxS report;
any per-BSS retirement protocol must record that uncertainty and quarantine
the BSS rather than treating a missing report as success. PID reuse after a
completed report, late/duplicate hardware responses, frame enqueue failure,
IRQ quiescence and adapter shutdown remain unproved. Do not enable dynamic IoT
BSSID reuse or infer device acceptance from this host fixture.

## Beacon ring admission is separated from TxS reservation — 2026-10-23

Pinned `ap/ap_connect.c:614-620` checks `GET_BCNRING_FREENO` before frame
construction, outside `BcnRingLock`. The same function later calls
`write_tmac_info_beacon` (`:1705`), which reserves a TxS PID through
`mac/mt_mac.c`, then `RT28xx_UpdateBeaconToAsic` (`:1724`). That final function
(`common/cmm_mac_pci.c:2678-2715`) takes `BcnRingLock` only around
`HAL_KickOutMgmtTx`; it does not recheck ring capacity or cancel the previously
reserved PID on an early return (for example, missing `BeaconPkt` or the
candidate's close/dequeue guard). The PCI kickout macro resolves to
`RtmpPCIMgmtKickOut` (`common/cmm_data_pci.c:750-852`), which writes the current
ring cell, advances the CPU index and returns zero; the reviewed body has no
ring-full or DMA-map failure branch. Its zero return is not an independent
per-frame completion proof.

The existing precheck reduces ordinary overflow risk but is outside the ring
lock; concurrent BSS producers can invalidate it before kickout. A usable IoT
retirement counter therefore needs admission and PID reservation tied to an
actual accepted ring submission, or a checked rollback/quarantine for every
failure after reservation. Recheck space while holding the ring lock and avoid
overwriting a live ring cell. Do not mark producer/DMA/TxS quiescence from the
current precheck or kickout return. This source audit did not change the
candidate, driver, image or router.

## DMA-map failure is not propagated by beacon kickout — 2026-10-23

Pinned `BCN_RING_SIZE` is 20 (`include/os/rt_linux_cmm.h:481`).
`RtmpDrvPciMapSingle` (`common/cmm_mac_pci.c:3161-3196`) checks
`dma_mapping_error` and returns zero on failure. Yet
`RtmpPCIMgmtKickOut` (`common/cmm_data_pci.c:750-852`) stores the returned
address into the ring descriptor and advances the CPU index without testing
it; the caller discards its unconditional zero result. Thus the current path
cannot tell the TxS owner that PCI mapping failed after PID reservation.

The next candidate must check ring capacity under `BcnRingLock`, propagate a
real DMA-map/submit result, and settle the reserved TxS PID on every failure
before hardware submission. A successful CPU-index write is still only an
enqueue event; DMA completion and TxS delivery remain separate evidence.
The partial assembler now states `beacon_ring_admission_atomic=false` and
`beacon_pid_submission_accounted=false`. No target or router execution was
performed for this audit.

## Beacon PID ownership at the submit boundary — 2026-10-23

The pinned MT_MAC beacon builder (`ap/ap_connect.c:106-135`) passes
`TxSPriv=apidx` to `write_tmac_info` and writes a complete `TMAC_TXD_L` into
the beacon packet. The descriptor's fifth dword contains the 8-bit PID and
`tx_status_2_host` flag (`include/mac/mac_mt/mt_mac.h`). However the descriptor
is transformed in place on the big-endian path immediately before submission
(`common/cmm_mac_pci.c:2701-2703`). The current `VOID`
`RT28xx_UpdateBeaconToAsic` interface carries neither the reserved PID nor a
submit result. Parsing packet bytes at a later failure point is therefore not
a portable ownership proof; a generic `RemoveTxSStatus(pid)` would also be
unsafe unless that exact packet is known never to have reached hardware.

For the candidate, carry a typed reservation token (PID plus valid flag) from
TMAC construction to the locked enqueue boundary, before endian conversion.
The native-format extraction point is immediately after
`write_tmac_info_beacon` in `ap/ap_connect.c:1699`, where the `TMAC_TXD_L`
still resides in `tmac_info`. `MTMacInfoEndianChange` in `include/rtmp.h:6205`
swaps every 32-bit TMAC word in place, so reading its bitfields in the PCI
submit function after that conversion is incorrect on big-endian builds.
There is exactly one MT_MAC call from this beacon builder to the submit
function; the separate RTMP/RLT implementation shares the C name under a
different compile branch and must keep its ABI intact.
Under `BcnRingLock`, check capacity and PCI DMA mapping before publishing the
descriptor/CPU index. On a failure proven to precede publication, cancel only
that reservation under `TxSStatusLock`; after publication, retain ownership
until an observed TxS or a separately proved quiescence barrier. Propagate a
checked enqueue result instead of interpreting the existing unconditional
zero as acceptance. This is the required design boundary, not implemented
production behavior. The router remains unchanged here.

## Generation-tagged TxS pre-submit cancellation candidate — 2026-10-23

The separate TxS preparer now adds a monotonically advancing 32-bit
reservation generation to each allocated slot and returns `(PID, generation)`
to all four TMAC construction callers. `CancelTxSReservation` clears a slot
only if it is still used and both values match. The generated host fixture
checks a stale-generation refusal, one successful cancellation and a duplicate
refusal alongside the existing allocation/completion cases. It compiled with
strict MinGW GCC and ran successfully from the new isolated output
`iot-txs-generation-20261023`; no source tree was modified.
The unified partial bundle was also assembled afresh at
`iot-unified-txs-generation-20261023`; its manifest records the same three
TxS file hashes, `generation_tagged_pre_submit_cancel_staged=true`,
`beacon_cancel_caller_bound=false`, `production_installed=false`, and
`target_compiled=false`.

This is **not** a beacon rollback yet: the generation is not carried from
TMAC construction to `RT28xx_UpdateBeaconToAsic`, no ring/DMA failure is
propagated, and the API has no production caller. A 32-bit generation can also
wrap, and an old hardware TxS contains only the 8-bit PID; this change cannot
by itself prove safety against late reports or selective BSS retirement. Its
only permitted future call site is a path that has proved the exact packet was
never published to hardware. Manifest flags continue to keep production,
target compile and PID reuse proof false.

## TxS generation reaches MAC_TX_INFO in partial candidate — 2026-10-23

The pinned `MAC_TX_INFO` source (`include/mac/mac.h`, blob
`0dd885ca5b1b08e84542e17e8418aa10177fee1e`) is now included in the
isolated TxS stage. Its MT_MAC-only part gains
`TxSReservationGeneration`. `write_tmac_info` clears the output field on
entry and copies the allocated generation on its two `MAC_TX_INFO` TxS paths;
the other two `TX_BLK` paths still use the same allocator API without exposing
this output. This preserves the public `write_tmac_info` signature and lets
the beacon wrapper retrieve a generation after TMAC construction. The unified
partial bundle assembled at `iot-unified-txs-token-output-20261023`; inspection
found one initialization and two success assignments in the generated source.

No beacon wrapper consumes this output yet. The descriptor PID and generation
must be captured together before endian conversion, then passed to a checked
enqueue result. This stage does not prove that capture, cancellation, target
compilation or runtime safety; manifest flags keep the caller unbound and
production/target states false.

## Beacon builder exposes TxS generation in partial bundle — 2026-10-23

The unified assembler now changes both local `write_tmac_info_beacon`
variants from `VOID` to `UINT32`. The MT_MAC variant returns the generation
recorded by `write_tmac_info`; the RTMP/RLT variant returns zero only after
its existing `SPECIFIC_TX_POWER_SUPPORT` block. Existing call sites may ignore
the return. The corrected isolated output is
`iot-unified-beacon-generation-v2-20261023`; inspection confirmed the legacy
power-adjustment block still executes before the new return. The first
generated attempt placed that return too early and must not be used.

The main beacon caller does not yet capture this return, and no PID/generation
token reaches the locked submit path. The bundle remains partial and
uninstalled; it was not target compiled or exercised on the router.

## Beacon reservation reaches submit ABI in isolated candidate — 2026-10-23

The candidate now carries both the reserved PID and generation as a
`WR_BCN_TXS_RESERVATION` value from `APUpdateBeaconFrame` to
`RT28xx_UpdateBeaconToAsic`. `write_tmac_info` initializes both output fields
and fills them only on successful `MAC_TX_INFO` TxS allocation. The MT_MAC
beacon builder returns the generation and optionally writes the PID; the
RTMP/RLT builder returns zero after its existing power adjustment. The
initial legacy-only beacon construction passes a null PID output. The active
beacon update captures both values before any big-endian descriptor swap.

The unified assembler updates the common declaration and both PCI plus SDIO
definitions together. Its corrected isolated output is
`iot-unified-beacon-token-v3-20261023`; two earlier output folders failed
assembly and have no completed manifest. Inspection confirms the token at
the active call and three matching definitions. **The submit functions do not
consume it yet**: ring admission, DMA mapping failure, cancellation, target
compilation, and device behavior remain unproved. Manifest flags distinguish
`beacon_reservation_token_passed_to_submit=true` from
`beacon_reservation_token_consumed_by_submit=false` and keep production and
target compilation false.

## Beacon pre-publication admission and rollback candidate — 2026-10-23

The next isolated bundle is `iot-unified-beacon-admission-v2-20261023`.
`RtmpPCIMgmtKickOut` now maps the packet before changing a ring cell; a zero
mapping result returns `-1` without writing packet ownership, descriptor or
CPU index. In the MT PCI beacon submit branch, the final
`GET_BCNRING_FREENO` check and kickout run under `BcnRingLock`. A full ring,
disabled dequeue, failed `BeaconTransmitRequired`, missing packet or failed
DMA map reaches a pre-publication path that calls
`CancelTxSReservation(pid, generation)` only for a valid token. Successful
kickout retains the reservation for later TxS evidence. Non-PCI and legacy
branches keep their existing kickout path. The initial ring precheck in the
builder is still present as an early shortcut; the new locked check is the
last admission decision.

This is **partial code, not acceptance**. The assembler verified exact source
anchors and produced the bundle, but it is not target compiled or installed.
The caller still has a `VOID` submit interface and cannot distinguish success
from failure. A cancellation refusal is only logged; BSS quarantine and
late/duplicate TxS safety are unresolved. DMA completion, TxS delivery and
adapter shutdown are not proved by the PCI kickout return. Manifest flags mark
the staged locked admission and pre-submit cancel true, but keep
`beacon_pid_submission_accounted=false`,
`beacon_cancel_failure_quarantined=false`, `target_compiled=false` and
`production_installed=false`. The earlier non-v2 admission bundle has stale
manifest flags and should not be used for status claims.

## Explicit beacon submit result and MCU-offload guard — 2026-10-23

The latest isolated partial bundle is
`iot-unified-beacon-submit-offload-guard-20261023`. The common declaration,
MT/legacy PCI variants, and SDIO stub now return `INT32` consistently. The
MT PCI path returns `0` after the CPU-index publication, `-1` on known
pre-publication rejection with successful token settlement, and `-2` when
generation-matched cancellation fails. `APUpdateBeaconFrame` stops before
recording its success timing when the result is nonzero. Legacy PCI returns
zero after its existing register update and `-1` on invalid input; the empty
SDIO stub returns `-1`. These values do **not** assert DMA or TxS completion.

The pinned `os/linux/config.mk` defaults
`HAS_BCN_EVENT_UPDATE_SUPPORT=n`; setting it to `y` defines
`BCN_OFFLOAD_SUPPORT`. In that mode `APUpdateBeaconFrame` can submit a beacon
to MCU before the PCI call, invalidating the candidate's assumption that a
PCI rejection proves no publication. The MT PCI candidate therefore has a
compile-time error for the combination of `BCN_OFFLOAD_SUPPORT` and
`RTMP_PCI_SUPPORT` until an MCU ownership/rollback path is designed. The
effective board build flags have not been verified by target compilation.

The assembler completed with these source changes, but no target build or
router check ran. A failed cancellation is reported as `-2` and logged; safe
BSS quarantine, late TxS and final callback quiescence remain open. The
candidate is not installed in firmware. Earlier admission and submit-result
bundles are superseded for current-state claims.

The existing post-build IoT capacity inspector now records
`effective_beacon_offload_support` and `effective_pci_support` from its actual
MT7603 Kbuild command in the archived `wr1200js-iot-radio-capacity` report.
This is a diagnostic for the `rtmp_chip.o` translation unit, not yet the
`cmm_mac_pci.o` compile command or a completed candidate driver build. The
source tree and current workflow do not explicitly set
`HAS_BCN_EVENT_UPDATE_SUPPORT=y`; the pinned `config.mk` default is `n`.
The effective beacon-submit flags therefore remain unverified until the
post-build report and the submit translation unit are inspected.

The inspector now also locates the actual `.cmm_mac_pci.o.cmd`, verifies its
pinned compiler and single C input, and preprocesses that translation unit
into `beacon_submit_probe`. Missing or ambiguous command files are reported
as unavailable rather than inferred from `rtmp_chip.o`. This remains a
post-build diagnostic: no new target build ran. A local self-test attempt
stopped before its assertions because Windows denied creating its temporary
fixture directory, including when `%TEMP%` pointed inside the workspace.
The same targeted self-test subsequently passed with approved elevated local
execution; its injected compiler-timeout case prints `UNAVAILABLE` by design.
Both edited Python files parsed in memory and `git diff --check` passed. This
self-test uses a host compiler and synthetic Kbuild commands, not a target
MIPS driver build.

## Beacon TxS callback BSS bound — 2026-10-23

Pinned `tx_rx/txs.c` registers `BcnTxSHandler` for beacon reports. That
handler takes `Priv` as the BSS index and immediately accesses
`ApCfg.MBSSID[bss_idx]`, then sets `bcn_state=BCN_TX_IDLE`. The callback
receives only the hardware report PID; the candidate's reservation generation
is not present in that report. A late report for a reused 8-bit PID can
therefore still consume the new reservation and mark the wrong beacon idle.

The isolated bundle `iot-unified-beacon-txs-bound-v2-20261023` now checks
`Priv` against both the current `BssidNum` and `MAX_MBSSID_NUM(pAd)` before
the narrowing cast and array access. Its completed manifest records
`beacon_txs_index_bounded=true`. This bounds the direct array access but
does not synchronize BSS count/lifetime with the callback, distinguish stale
reports, quiesce callbacks or quarantine cancellation failure. The manifest
retains those readiness flags as false; no target compile or device run was
performed. The earlier non-v2 bound bundle is superseded.

The beacon DMA completion handler is another BSS state writer. Pinned
`common/cmm_data_pci.c` starts its decoded `own_mac` index at zero, leaving
unknown values mapped to BSS 0, and then indexes `MBSSID` without a bound.
The newer isolated bundle `iot-unified-beacon-dma-bound-20261023` starts with
an invalid sentinel, accepts only the existing descriptor mappings, and
checks both current BSSID count and chip capacity before the state update.
It still reclaims the DMA ring cell on an invalid index. Generated source and
manifest were inspected (`beacon_dma_bss_index_bounded=true`), without target
compilation or router execution. This supersedes the earlier bound bundle.

Retirement remains unresolved: DMA completion changes
`WRITE_TO_DMA -> DMA_DONE` under `BcnRingLock`, the Type 1 beacon TxS path
releases its TxS type lock before the callback sets `IDLE`, and
`wdev_bcn_buf_deinit` checks `IDLE` then
sets `STOP` without the same lock. The TxS report structure carries an 8-bit
PID but no driver reservation generation. Bounds alone cannot serialize
these writers or prove that a late report belongs to the current BSS epoch.
Before production binding, define one beacon-state/lifetime owner and a
source-backed rule for report completion, PID reuse and callback quiescence.

The shared-lock conversion also requires teardown reordering. In pinned
`os/linux/rt_profile.c`, `RTMPFreeAdapter` frees `BcnRingLock` before it calls
`wdev_bcn_buf_deinit` for the main BSS. The other deinit call is in
`MBSS_Remove` (`ap/ap_mbss.c`); callers include AP configuration and main
netdev removal. A lock added inside deinit with current main teardown order
would access a freed lock. The completion design must first establish when
IRQ/TxS producers stop, keep `BcnRingLock` alive through both main and
secondary beacon deinit, and make `IDLE -> STOP` atomic with competing DMA
and TxS state updates. The current candidate does not stage or prove that
ordering. Moving the deinit call alone would not establish producer
quiescence or make an ignored deinit failure safe.
`RTMPFreeAdapter` also appears on the PCI probe error path, so any reordered
lock or beacon cleanup must handle partially initialized adapters; normal
netdev removal invokes secondary `MBSS_Remove` before final adapter free.

The isolated bundle `iot-unified-beacon-lock-order-20261023` stages a narrow
ordering repair: on the PCI path it moves main beacon deinit before
`NdisFreeSpinLock(&BcnRingLock)`, while the non-PCI path retains its original
cleanup location. The generated source shows the PCI call before lock free
and a separate `#ifndef RTMP_MAC_PCI` cleanup; manifest flags the ordering
stage true, but `beacon_lock_lifetime_proven=false`. This does not yet take
the lock in deinit or callback, handle ignored deinit failure, establish
IRQ/TxS producer quiescence or prove partial-init safety. No target compile,
production installation or device execution occurred. The previous DMA-bound
bundle is superseded as the latest candidate.

Normal PCI remove calls `RtmpPhyNetDevExit` before `RtmpRaDevCtrlExit`; the
`RTMPDrvClose` path disables Tx/Rx and releases IRQ before its later
`ExitTxSTypeTable`. This ordering is relevant but does not yet prove every
callback has returned or that an IoT-only BSS close follows the same path.
The PCI probe error path calls `RTMPFreeAdapter` directly. The next design
must cover both normal remove and partial initialization, then handle a
failed `wdev_bcn_buf_deinit` result rather than ignoring it.

The next isolated bundle, `iot-unified-beacon-state-lock-v2-20261023`,
stages `BcnRingLock` around the PCI beacon TxS callback's BSS index/state
update and around deinit's `IDLE -> STOP` decision. The Type 1 parser releases
its TxS type lock before invoking `BcnTxSHandler`, avoiding that nested lock
at this call site. The callback rejects `STOP` under the beacon lock, and DMA
completion already uses that same lock. The bundle retains main deinit before
lock free and leaves non-PCI behavior under its existing branch. The initial
non-v2 state-lock bundle is superseded because its TxS lock guard did not
also require `MT_MAC`.

This is still a partial concurrency stage. `RTMPAllocAdapterBlock` creates
the beacon lock before publishing a successful adapter; a failed allocation
does not call `RTMPFreeAdapter`, while later PCI probe errors do. This supports
lock existence on those PCI cleanup paths, but not callback quiescence.
`APShutdown`/BSS-specific close, startup/reset state writers, failed deinit,
late TxS after PID reuse and DMA packet ownership remain unproved. Manifest
flags `beacon_txs_state_lock_staged` and `beacon_stop_state_lock_staged` true,
but lock lifetime, target compile, production installation and runtime false.

Further audit of pinned `ap/ap.c` at `c25283e9` identifies additional
direct beacon-state writers: `APStartUp` sets each configured BSS to
`BCN_TX_IDLE` at line 967, and `APStop` sets each BSS to IDLE at line 1412
after setting `fRTMP_ADAPTER_HALT_IN_PROGRESS` at line 1359. PCI
`APShutdown` calls `APStop`; other reconfiguration paths call it too.
`APStopBssOnly` has a similar write at line 1580, but a repository-wide
search of this pinned mt76x3 tree found only its definition and declaration,
no caller. Do not treat it as the current IoT selective-close path.

The isolated bundle `iot-unified-ap-state-lock-20261023` now stages the
`APStartUp` and `APStop` IDLE writes under PCI `BcnRingLock`, guarded by
`MT_MAC` and `RTMP_MAC_PCI`. The assembler pins the original `ap/ap.c` blob
`e452c6f5`, records the generated file hash and marks
`ap_start_stop_beacon_state_lock_staged=true`. Its generated source and
manifest were inspected. The HALT flag and this lock still do not prove
that TxS/DMA callbacks have drained, that a late TxS belongs to the current
PID reservation, or that reset/deinit is safe. Target compile, production
installation and device run remain false.

The pinned direct-assignment inventory also found `APCheckBcnQHandler` in
`hw_ctrl/cmm_asic_mt.c:1394`. It is called from `ap/ap_connect.c:628` when
the beacon state is not idle, and can flush/re-enable the beacon queue before
publishing IDLE. The earlier `radio-errors` stage already guards the final
hardware re-enable and state publication with `BcnRingLock` and checks BSS
eligibility; adding a second lock there would deadlock. The newer isolated
bundle `iot-unified-beacon-recovery-stop-20261023` adds only a STOP-state
rejection inside that existing critical section. A line-level comparison of
the generated file against the radio-error stage shows exactly this one
added condition. The intermediate `beacon-recovery-lock` and `merged` bundles
are superseded and must not be installed. The generated manifest contains
one record for this file and keeps target/production/runtime false.

Other pinned direct assignments are the debug `BcnStateCtrl` handler
(`ap/ap_cfg.c:14609`, already using `BcnRingLock` around its write), PCI
reset (`common/cmm_mac_pci.c:2082`, already under the ring lock), PCI submit
(`:2712`), DMA completion (`common/cmm_data_pci.c:2738`), TxS callback
(`tx_rx/txs.c:98`), and beacon init/deinit (`tx_rx/wdev.c:125,143`).
`APStopBssOnly` remains without a pinned call site. This inventory does not
prove that every read is serialized or that DMA ownership, callback drain,
PID reuse and BSS lifetime are safe; those remain the next acceptance gates.

The `BcnStateCtrl` command is registered under `DBG` in pinned `ap/ap_cfg.c`;
the pinned AP configuration adds `-DDBG`. Its source handler originally used
the ioctl BSS index before a bounds check, narrowed `simple_strtol` to UCHAR
before range validation, and read state before taking `BcnRingLock`. The
isolated bundle `iot-unified-beacon-debug-guard-v2-20261023` stages a BSS
bound, LONG parse/range validation and one IRQ-safe state read/write, with
logging after unlock. It merges into the existing radio-error stage output;
the manifest has one final `ap/ap_cfg.c` record. The first debug-guard bundle
is superseded because it logged while holding the IRQ lock. Generated source
and manifest were inspected, not target compiled or installed.

Target compile feasibility was checked locally without extraction or build:
the saved `mipsel-linux-uclibc.tar.xz` contains a GCC executable with ELF
magic (`7f454c46`), while `wsl.exe --list --quiet` exited 1 and did not
identify an installed Linux distribution. The Windows `tar.exe` also failed
to initialize its xz filter; Python `tarfile` could read the archive. Thus
this local Windows session has not yet provided an executable Linux host for
the MIPS toolchain. None of this is evidence that the staged driver compiles.

The DBG setter still could write IDLE over a stopped BSS. The newer isolated
bundle `iot-unified-beacon-lock-forms-20261023` rejects `BCN_TX_STOP`, HALT
and NIC disappearance while holding `BcnRingLock`; the previous v2 debug
bundle is superseded. It also records the lock forms found in each assembled
C file. The partial bundle contains both `RTMP_SEM_LOCK` and `RTMP_IRQ_LOCK`
users of `BcnRingLock`; pinned `ap/ap_nps.c` is outside this partial bundle
and also uses the SEM form. In pinned `rt_linux_cmm.h`, SEM maps to
`RtmpOsSpinLockBh`; under `MULTI_CORE_SUPPORT`, IRQ maps to
`spin_lock_irqsave`, otherwise to the BH form. Pinned `config.mk` emits
`MULTI_CORE_SUPPORT` only in the BB_SOC/CONFIG_MIPS_TC3262 branch, but the
effective flags for each WR1200JS translation unit have not been observed.
Therefore the manifest explicitly keeps `beacon_lock_semantics_proven=false`
and `effective_multi_core_support=null`. Before production binding, verify
the effective flags and audit all users, including files outside this
partial bundle; normalize lock/interrupt ownership if the forms differ.

The existing post-build `check-capacity.py` now reports
`beacon_submit_probe.effective_multi_core_support` from the actual
`.cmm_mac_pci.o.cmd` preprocessing, alongside its beacon offload and PCI
macros. Its scope is exactly that translation unit; it does not prove flags
for AP, TxS, DMA or other lock users. The targeted capacity self-test passed
with defined and undefined feature cases; its injected timeout line is an
expected unavailable-path test, not a real compiler timeout. No target
compiler or router was used in that self-test.

## TxS PID retirement audit — 2026-10-23

In pinned mt76x3 source `c25283e9`, `include/mac/mac_mt/mt_mac.h` defines
`TxSPid` as `UINT8` and `TXS_STATUS_NUM` as 256, with no reservation
generation in `TXS_STATUS`. `tx_rx/txs.c:774-794` increments the 8-bit PID;
when the selected slot is already `TXS_USED`, `AddTxSStatus` only increments
`TxSFailCount` and still overwrites that slot. `RemoveTxSStatus` at lines
798-812 unconditionally marks the indexed slot unused and does not verify
its prior state or reservation identity. It also reads `TxRate` through the
current `TxSPid` rather than the reported `TxSPid`. The Type 1 report path
calls this removal before looking up the beacon handler (`:691-768`), and
`mac/mt_mac.c` calls `AddTxSStatus` while preparing descriptors. A late old
report can therefore consume a newer reservation after wraparound; a
software-only generation stored outside the hardware report cannot by
itself distinguish the two. This is a source finding, not a measured runtime
failure on WR1200JS.

Before using TxS completion as the IoT BSS retirement barrier, establish a
hardware-backed drain/quiescence rule for all pending reports before PID
reuse or prove a report identity that survives reuse. Make slot allocation,
removal and teardown synchronized; reject an unused/stale report without
invoking its callback. Preserve existing non-IoT TxS users when designing
the change. The current isolated beacon bundle does not satisfy this gate.

The isolated assembler manifest already marks occupied-PID overwrite
prevention and TxS slot validation as staged. Those candidate edits address
the pinned baseline's direct overwrite/unused-slot behavior; they do not
identify a late report after a slot has been freed and reused. Keep the
separate `txs_pid_reuse_safety_proved=false` manifest gate closed.

The hardware TxS PID arrives in an RX report packet: pinned
`common/cmm_data.c:581-617` handles `RMAC_RX_PKT_TYPE_RX_TXS` and passes
`txs_d4->pid` to `ParseTxSPacket`. Consequently, draining only the beacon TX
ring cannot establish that old reports are gone. Normal `RTMPDrvClose` in
`common/rtmp_init_inf.c` exits net tasklets, disables Rx/Tx and interrupts,
releases the IRQ, frees/reset rings, then calls `ExitTxSTypeTable`. Its
`RTMPHandleRxDoneInterrupt` call after interrupt disable is commented out.
This is not an explicit RX TxS report drain, nor is it the IoT-only BSS close
path. A safe selective close/reopen needs a source-backed barrier for pending
RX reports and in-flight callbacks while keeping other BSS traffic alive;
normal whole-radio teardown ordering alone cannot be reused as that proof.

The same pinned TxS report has a 12-bit `sn` field in `TXS_D_4`
(`include/mac/mac_mt/mt_mac.h:1228-1247`), but the existing beacon handler
only stores it for `DBG` history (`tx_rx/txs.c:102-105`). The descriptor
reservation in `mac/mt_mac.c` records PID/Priv, not an expected beacon SN;
no source-backed submit-to-report SN comparison was found in the inspected
beacon path. SN may be worth investigating as an additional discriminator,
but its 12-bit wrap and hardware assignment must be proved before it can
replace the pending-report drain barrier. Do not claim PID+SN uniqueness yet.

Closer MT7603 beacon submit trace: `ap/ap_connect.c:106-137` creates
`MAC_TX_INFO` with `NSeq=TRUE` and `TxSPriv=apidx`, but no expected SN.
`mac/mt_mac.c:770-1011` clears the long TMAC descriptor, assigns the beacon
owner MAC and reserves an 8-bit TxS PID; the inspected path does not set
`txd_3->sn` or `txd_3->sn_vld`, even though those 12-bit/valid fields exist
in `include/mac/mac_mt/mt_mac.h:291-319`. The beacon header is made through
`MgtMacHeaderInit` in `ap/ap_connect.c`, and this source path does not bind
its sequence number to the TxS reservation. This supports only the narrow
conclusion that the current software has no expected-SN match at submit.
Whether hardware assigns SN and how to read it before PID reuse require
target evidence. Until then, SN is diagnostic rather than a retirement key.

Selective BSS close is narrower than whole-radio shutdown. Pinned
`ap/ap_mbss.c:410-458` `MBSS_Close` stops the virtual netdev queue, kicks
that BSS's stations, clears `bBcnSntReq`, then rebuilds the beacons for all
BSSs. It does not wait for this BSS's outstanding beacon TxS reports or
deinitialize its beacon buffer. `MBSS_Remove` at `:183-211` later attempts
secondary beacon deinit while detaching virtual netdevs. The unused
`APStopBssOnly` in `ap/ap.c:1466-1580` is not a suitable shortcut: it
disables PCI interrupts and shared Pre-TBTT/synchronization, which can
disturb the main and guest networks. The IoT close contract therefore needs
a BSS-scoped stop-admission, report/callback retirement and state transition
on the existing `MBSS_Close` path, with the main radio and other BSSs kept
active. Current pinned code does not implement that contract.

The isolated assembler now records both `beacon_report_sn_matching_proved`
and `selective_bss_txs_retirement_proved` as false, alongside the existing
false PID-reuse and production gates. The assembled bundle at
`..\iot-unified-beacon-selective-gates-20261023` is a partial driver tree;
these explicit gates document missing behavior rather than supply it.

## Secondary BSS CR-disable readback candidate — 2026-10-23

The pinned virtual `ndo_stop` calls `CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE`
before `MBSS_Close`. The command dispatcher propagates a nonzero
`mbss_cr_disable` result, and the isolated `wr_iot_mbss_close_checked`
candidate already preserves that failure as an uncertain close. The staged
`mbss_cr_disable` first clears the target BSS beacon request and writes its
LPON TBTT and `ARB_BCNQCR0` queue bits under `BcnRingLock`; previously it
returned success without a register readback. The new isolated bundle
`..\iot-unified-beacon-cr-readback-20261023` reads those two register
locations after writing and returns failure while retaining the close
ticket if the target BSS's TBTT/queue bits remain set. It does not read
or alter the main BSS control bits. The assembler is anchored to the exact
pinned function and marks `bss_cr_disable_readback_staged=true`, but runtime
proof and selective TxS retirement remain false. Only generated
`ap/ap_mbss.c` differs from the preceding bundle; all 51 manifest file
hashes matched. Register readback proves only the control bits seen by the
CPU, not RF silence or completion of already queued RX TxS reports.

The successor `..\iot-unified-beacon-cr-readback-v2-20261023` corrects the
signed BSS-count versus unsigned array-capacity comparison in the CR
generator. A host fixture from the generated `mbss_cr_disable` compiles
under `-std=c11 -Wall -Wextra -Werror` and passes normal readback, sticky
TBTT, sticky queue, neighboring BSS preservation and invalid-index cases.
Its 51 generated files match the manifest hashes. This is not a MIPS target
build or a proof that hardware has stopped transmitting; selective TxS
report retirement and callback quiescence are still required.

The pinned tree also contains `CmdFlushFrameByWlanIdx` in
`mcu/andes_mt.c:1997-2024`. Its one in-tree caller is the
`FAST_DETECT_STA_OFF` station-deletion branch in `ap/ap.c:2427-2431`, where
the argument is the removed station's WCID. The command uses
`AndesInitCmdMsg(..., FALSE, 0, FALSE, FALSE, 0, NULL, NULL)` and sends
`EXT_CMD_FLUSH_FRAME_WCID` without a response callback or a report-drain
check. Beacon TxS reservations in the inspected path carry the BSS index in
`TxSPriv`, not a proved IoT-only WCID. Consequently this command cannot yet
serve as the selective beacon-report retirement barrier: neither its scope
for a beacon BSS nor completion of queued RX TxS reports is established.
Do not wire it into IoT close as a substitute for TxS callback quiescence.

## Isolated beacon TxS callback accounting — 2026-10-23

The Type 1 parser removes the PID slot before invoking `BcnTxSHandler`.
Scanning occupied slots alone can therefore report zero while that handler
still runs. `tools/iot/prepare-beacon-txs-callback-ledger.py` stages a
per-BSS in-flight callback counter under `TxSStatusLock`: removal increments
it before freeing a beacon slot, and all three Type 1 parser exits decrement
it after either handler completion or handler rejection. A counter mismatch
sets a sticky fault; `WrBeaconTxSOutstanding` returns an error rather than
claiming an idle BSS. The helper also scans still-occupied beacon slots for
the selected BSS. This source is assembled only into
`..\iot-unified-beacon-txs-ledger-v5-20261023`, not the firmware tree.

The host fixture extracts the actual staged allocation, removal, parser,
completion, cancellation and query functions. With injected locks and one
handler it compiled under `gcc -std=c11 -Wall -Wextra -Werror` and passed
reservation, callback-window, completion, missing/mismatched handler,
peer-BSS, cancellation, saturation and accounting-fault cases. All 51
assembled file hashes matched the manifest; only `tx_rx/txs.c` and
`include/mac/mac_mt/mt_mac.h` differ from the preceding bundle.

This ledger is a software snapshot. It has no production close binding and
cannot identify a delayed report after the 8-bit PID is reused. The target
driver has not been compiled or run. RF silence, TxS report uniqueness,
adapter lifetime and a bounded fail-closed close wait remain unproved.

## Checked BSS close TxS snapshot gate — 2026-10-23

The follow-up isolated bundle `..\iot-unified-beacon-txs-close-gate-v2-20261023`
adds `WrBeaconTxSOutstanding` to `wr_iot_mbss_close_checked` after successful
CR-disable readback and `MBSS_Close`, before HNAT deregistration and virtual
reference consumption. A positive query retains the stage-2 close ticket for
retry. A negative query or invalid secondary BSS index enters the existing
uncertain stage; it cannot silently finish the close. The host MBSS fixture
extracted the final checked-close fragment and passed a pending-then-retry
case and an accounting-fault case under strict GCC warnings. The TxS parser
fixture still passes. All 51 generated file hashes match the manifest;
compared with the callback-ledger bundle, only the checked-close include
changed. The manifest distinguishes `beacon_txs_snapshot_gate_staged=true`
from `beacon_txs_close_barrier_bound=false`.

Pinned `RT28xx_MBSS_IdxGet` finds the BSS by comparing `wdev.if_dev` with
the virtual device. The inspected `MBSS_Close` clears beacon request and
updates beacons without removing that device mapping, so the staged
post-close lookup has a source-backed index at this point. Concurrent
mutation of `BssidNum` or virtual-device teardown is still not excluded.

This query is **not** a completion barrier. The candidate has no bounded
wait or wakeup, no proof that all producers are excluded while the snapshot
is taken, and no way to reject a delayed report after PID reuse. The checked
close is not wired into mandatory production `ndo_stop`; the generated
driver remains a partial, uncompiled tree. Target and device acceptance
remain open.

## TxS PID claim through parser exit — 2026-10-23

The ledger-only candidate freed an accepted PID before the beacon callback
returned. `tools/iot/prepare-txs-claimed-slot.py` now stages a third
`TXS_CLAIMED` state in the isolated driver. `RemoveTxSStatus` atomically
claims a used PID; `AddTxSStatus` allocates only `TXS_UNUSED` slots.
`WrTxSCompleteClaim` releases the claim after the Type 0 or Type 1 parser
path exits, including missing handler, mismatched format and unknown type.
A completion-state mismatch sets the sticky TxS accounting fault. The
per-BSS query treats both `TXS_USED` and `TXS_CLAIMED` beacon slots as
outstanding, so a callback cannot expose an idle snapshot merely because
its counter has already decremented.

The latest partial bundle is `..\iot-unified-txs-claimed-slot-v2-20261023`.
Strict GCC host fixtures extracted the generated TxS parser, status
functions and checked BSS-close fragment. They passed a same-PID allocation
attempt during callback, Type 0/Type 1 success and rejection exits,
cancellation, overflow and pending-close retry. All 51 file hashes and 74
preparer-input hashes match the manifest; only the TxS C/header files differ
from the prior close-gate bundle. The result proves the software slot cannot
be reused *while its accepted parser invocation is active* in the tested
host model. It does not distinguish a delayed or duplicate hardware report
after claim completion and later PID reuse. Hardware report identity or a
source-backed drain is still required, as are producer exclusion, bounded
close wait, target compilation and device runtime acceptance.

### Reused-PID late-report negative witness — 2026-10-23

`tools/iot/prepare-beacon-txs-ledger-check.py` now extracts the current
candidate allocator, parser and ledger functions and models a duplicate old
hardware report after the old callback has exited and the same 8-bit PID has
been assigned to a different BSS. The new reservation has a different local
`Generation`, but `ParseTxSPacket` receives only PID and format. The strict
GCC host run demonstrated that the old report invokes the new BSS handler,
reduces its outstanding count to zero and leaves its later real report
unmatched. This is a deliberately injected report-order model, not evidence
that the hardware actually duplicates reports. It disproves safety under
that ordering. Do not bind the candidate to selective IoT BSS retirement
until the actual report format or a source-backed producer/DMA/RX drain rules
out that ordering before PID/BSS reuse. The existing partial driver bundle
was not regenerated after this fixture change; its preparer-input snapshot
belongs to the earlier tool version. No production image or router change.

### TxS receive-path coverage for a retirement barrier — 2026-10-23

The pinned MT driver parses TxS reports in `common/cmm_data.c:579-613`,
passing only `txs_d4->pid`, format and report bytes to `ParseTxSPacket`.
`common/cmm_data_pci.c:1834-1838` invokes that parser while fetching from an
RX ring; `tx_rx/wdev_rx.c:2875-2878` uses ring 0 in the normal RX tasklet.
That tasklet stops on RADIO_OFF/RESET/NIC-missing or START_UP false unless
POLL_IDLE is set (`wdev_rx.c:2822-2829`), and processes a bounded batch before
rescheduling (`:2837-2841`). An idle ring sample alone therefore is not a
producer-stop or completed-callback proof.

There is another source entry: `mcu/andes_core.c:426-456` passes a queued MCU
message to the same `parse_rx_packet_type` from `AndesCmdMsgBh`. Whether this
path can carry beacon TxS on the effective WR1200JS build is **unverified**;
inspect its effective preprocessor configuration and MCU routing before
choosing a retirement barrier. A barrier that only samples ring 0 is not
source-proven to cover that queued path. `hw_ctrl/cmm_asic_mt.c:4803-4818`
returns immediately for HIF_MT in `StopDmaRx`, so that helper cannot be
assumed to drain MT7603 RX. Next establish all compiled report producers and
consumers, then a BSS-scoped quiescence/identity rule that keeps main/guest
traffic alive. No driver or router change was made in this source audit.

The existing WR1200JS #535 `kernel-effective.config` selects MT7603E as a
module with `CONFIG_MT7603E_RTMP_PCI_SUPPORT=y` and `CONFIG_MT7603E_MT_MAC=y`.
The pinned `os/linux/config.mk:1509-1526` adds
`-DCONFIG_ANDES_SUPPORT` for `CHIPSET=mt7603e`. These inputs support a
source/configuration expectation, not an actual per-translation-unit result:
the downloaded #535 artifacts do not contain `.andes_core.o.cmd` or the
receiver units' compiler commands. `tools/iot/check-capacity.py` now adds a
diagnostic `txs_receive_units_probe` for `cmm_data.c`, `cmm_data_pci.c`,
`wdev_rx.c` and `andes_core.c`. It preprocesses each unit from its own
recorded Kbuild command; absent or failed commands remain `unavailable` with
null flags. The synthetic self-test passed present/missing-command cases,
including an injected compiler timeout. A future exact-image CI report must
confirm these flags before concluding which receiver code was compiled;
even compiled code alone does not prove MCU TxS routing or a drain barrier.

### Type 1 TxS registration lifetime — 2026-10-23

The pinned Type 1 `ParseTxSPacket` path reads `TxSType` under
`TxSTypePerPktTypeLock`, unlocks, then dereferences
`TxSType->TxSHandler`. `RemoveTxSTypePerPktType` and `ExitTxSTypeTable`
free registration entries. That ordering permits an entry to be freed between
unlock and handler dereference. The isolated overlay
`tools/iot/prepare-txs-handler-snapshot.py` copies the function pointer under
the lock and calls the snapshot afterward. The extracted host fixture poisons
the registration on unlock and confirms the copied handler still runs.

The rebuilt partial bundle is `..\iot-unified-txs-handler-snapshot-v2-20261023`:
the strict GCC fixture compiled and ran, all 51 generated file hashes and 75
preparer hashes matched its manifest. This only removes the unlocked entry
dereference in the tested Type 1 path. Callback quiescence, teardown of the
handler's code/context and delayed reports after PID reuse remain unproved.
The same fixture still demonstrates that a late old report can consume a new
BSS's reused PID slot. No MIPS target build, production binding or router
runtime validation was performed; do not install this partial driver.

The remaining teardown race is concrete in the generated source:
`tx_rx/txs.c:390` stores `TxSValid = FALSE`, then `:392-422` removes
registrations and frees both registration-lock arrays and `TxSStatusLock`.
The parser reads `TxSValid` at `:746` before acquiring those locks at `:766`
or `:798`. A parser that passed the check can still enter while exit frees
the locks, and an already-snapshotted handler can still be executing. The
normal whole-radio close calls `RtmpNetTaskExit` at
`common/rtmp_init_inf.c:875` before releasing IRQ, exiting MCU control,
freeing rings and exiting the TxS table at `:943-984`. The PCI task exit
kills `rx_done_task` and, under `CONFIG_ANDES_SUPPORT`, `rx1_done_task`
(`os/linux/rt_rbus_pci_drv.c:106-112`). `MCU_CTRL_EXIT` resolves to
`AndesCtrlExit` through `mcu/mcu.c:188-191`; its PCI exit kills
`cmd_msg_task` before clearing the MCU queues (`mcu/andes_core.c:626-645`).
The wrapper maps tasklet kill to `tasklet_kill` or `cancel_work_sync`.
These are explicit whole-radio quiescence calls, subject to confirming the
effective WR1200JS compile flags and all producers. The commented-out
RX-drain call at `rtmp_init_inf.c:912` is not an additional barrier. A production
candidate needs an explicit, source-backed admission stop and completion
barrier before freeing TxS locks or handler context, including both compiled
report paths. It must preserve main/guest traffic for an IoT-only close.
Stopping these shared RX/MCU tasklets to close only IoT would interrupt the
other BSSs; the candidate needs a selective rule instead.

### Beacon TxS cannot be disabled as a close shortcut — 2026-10-23

The pinned `BcnTxSHandler` (`tx_rx/txs.c:77-114`) marks the addressed
`MBSSID[Priv].bcn_buf.bcn_state` as `BCN_TX_IDLE` and resets its non-idle
counter. `ap/ap_connect.c:622-632` normally refuses the next beacon update
while the state is non-idle, and `tx_rx/wdev.c:132-145` refuses to free a
non-idle beacon buffer. Omitting beacon TxS would therefore require a
separate, verified completion mechanism; disabling its report alone can
stall beacon refresh or prevent clean BSS teardown.

`APCheckBcnQHandler` in `hw_ctrl/cmm_asic_mt.c:1194-1395` has a BSS-indexed
recovery path: after a non-idle threshold it writes flush controls, polls
them with a timeout, **re-enables** beacon start and marks the BSS idle.
This is a recovery action, not a selective IoT close barrier. Its register
polls do not establish that previously emitted TxS reports have left RX/MCU
queues, and a timeout still proceeds through the function. Do not reuse it
to justify PID retirement or removal of the IoT BSS. The next candidate
must preserve TxS-driven beacon completion while proving BSS-specific
producer stop and old-report identity or drain before PID reuse.

### Available TxS report fields do not identify a beacon BSS — 2026-10-23

The pinned `TXS_STRUC` in `include/mac/mac_mt/mt_mac.h:1113-1255`
contains rate/error data, timestamp/noise, `wlan_idx`, `rxv_sn`, an
8-bit `pid` and 12-bit `sn`, but no `own_mac` or BSS index. Beacon submit
sets `MAC_TX_INFO.WCID = 0` for all BSSs and stores `TxSPriv = apidx`
(`ap/ap_connect.c:118-127`). `mac/mt_mac.c:847-854` encodes the BSS in
the transmit descriptor's `own_mac`, while `:1001-1011` allocates a Type 1
TxS PID and retains `TxSPriv` only in software. The receive parser gets the
PID and format, then loads the current slot's `Priv`; it does not receive
the original descriptor's `own_mac`. Therefore `wlan_idx` is not a
source-backed BSS discriminator for these beacon reports: every submitted
beacon uses WCID 0.

The report `sn` remains a possible investigation target, not a verified
identity token. Beacon setup sets `NSeq = TRUE`, but the inspected descriptor
writer does not store a per-submission expected SN with its PID or set a
verified `sn_vld` value. The candidate's software `Generation` likewise is
not carried in the report. A future identity approach must prove hardware
SN assignment, uniqueness/wrap handling and exact reservation matching on
WR1200JS; otherwise the close path needs a real old-report drain before PID
reuse. No production or device behavior was changed in this source audit.

### Selective beacon producer gate is staged but lock semantics remain open — 2026-10-23

The isolated checked close calls `CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE` before
`MBSS_Close` (`include/wr-iot-mbss-close-checked.inc:35-55`). In the generated
`ap/ap_mbss.c:329-390`, `mbss_cr_disable` clears only the target
`bBcnSntReq` under `BcnRingLock`, disables that BSS's TBTT/queue bits and
reads them back. The generated PCI submit in `common/cmm_mac_pci.c:2726-2749`
takes `BcnRingLock` and rechecks `BeaconTransmitRequired` immediately before
`HAL_KickOutMgmtTx`; a frame prepared before close is refused once the BSS
request has been cleared. This excludes submissions through that specific
beacon path; it is not a complete producer exclusion and does not establish
that already submitted beacons or their TxS reports have drained.

The same partial tree still uses both `RTMP_SEM_LOCK` and `RTMP_IRQ_LOCK` on
`BcnRingLock`. Under `MULTI_CORE_SUPPORT`, the Linux wrapper maps the former
to a BH spin lock and the latter to `spin_lock_irqsave`; without that macro,
both use the BH wrapper (`include/os/rt_linux_cmm.h:264-302`). The effective
per-translation-unit setting and all owners have not been proven for the
WR1200JS build. Mixed interrupt masking on one lock may leave an IRQ-context
acquirer able to interrupt its holder; do not mark this gate atomic or
production-safe until the complete lock map and target flags are verified
and a coherent locking scheme is used. The candidate manifest correctly
keeps `beacon_ring_admission_atomic=false`,
`beacon_lock_semantics_proven=false` and
`selective_bss_txs_retirement_proved=false`.

### Separate TIM queue producer requires an activation audit — 2026-10-23

The pinned AP-mode build list includes `ap/ap_nps.o`
(`os/linux/Makefile.6:336-352`). `ap/ap_nps.c:33-47,51-79` has an independent
`tim_buf.bTimSntReq` gate and can submit a TIM packet through
`HAL_KickOutMgmtTx(..., Q_IDX_BCN, ...)` while holding `BcnRingLock`.
`wdev_tim_buf_init` sets that request flag (`ap/ap_nps.c:285-305`). The
candidate `mbss_cr_disable` clears `bcn_buf.bBcnSntReq`, not this separate
TIM flag. A live TIM path would therefore bypass the candidate's beacon
request check and must be stopped or excluded for the target BSS before
selective close. TIM descriptors use `PID_MGMT` (`ap/ap_nps.c:87-112`), so
this is a second beacon-*queue* producer, not proof that it creates the same
Type 1 beacon TxS report.

The only source call to `APMakeAllTimFrame` is in
`RTMPHandlePreTTTTInterrupt` (`common/cmm_data_pci.c:1514-1524`); a full
source search found no caller for that interrupt handler. The PCI
`WF_MAC_INT_4` branch reads `HWISR4`, masks asserted sources in `HWIER4`
and returns without scheduling or invoking the PRETTTT handler
(`os/linux/rt_rbus_pci_drv.c:1574-1586`). Thus the inspected source has
no live software call chain from this interrupt to TIM packet submission;
the mere inclusion of `ap_nps.o` does not make this path active. The private
`TimEnable` command is registered as development-only
(`ap/ap_cfg.c:1279,14466-14546`), allocates the TIM buffer and writes
PRETTTT/BTIM controls. This establishes a compiled, user-reachable control
and a potential queue producer, **not** that the WR1200JS runtime currently
dispatches PRETTTT or transmits TIM frames. Before production binding,
confirm the effective target build and interrupt dispatch, then either
exclude this path by a source-backed invariant or give it the same BSS-scoped
admission stop and DMA completion accounting. Keep
`beacon_ring_admission_atomic=false` until every active producer is covered.

### Complete pinned-source beacon-lock owner map — 2026-10-23

Full-tree search of pinned driver revision
`c25283e915a2a00a763774dd255b14aff997285e` found these active
`BcnRingLock` owners before the IoT transform:

| Owner | Lock form | Source anchor |
| --- | --- | --- |
| TIM packet submission | SEM/BH | `ap/ap_nps.c:77-79` |
| private beacon-state control | SEM/BH | `ap/ap_cfg.c:14608-14610` |
| ring-memory release | SEM/BH | `common/cmm_mac_pci.c:1490-1534` |
| beacon ring cleanup | IRQ | `common/cmm_mac_pci.c:1889-1930` |
| PDMA reset/recovery | IRQ | `common/cmm_mac_pci.c:2067-2095` |
| beacon packet submission | SEM/BH | `common/cmm_mac_pci.c:2710-2713` |
| beacon DMA completion | SEM/BH | `common/cmm_data_pci.c:2663-2760` |

The lock is allocated at `common/rtmp_init.c:136` and freed at
`os/linux/rt_profile.c:1742`. The only alternate acquire/release names found
for this lock are commented-out `NdisAcquireSpinLock` lines in
`common/cmm_mac_pci.c:1491,1535`; no additional live alias was found in this
snapshot. The isolated candidate adds owners in other units, so its full
generated tree also needs the same audit. Under `MULTI_CORE_SUPPORT`, a
SEM/BH holder can be interrupted locally by a hard IRQ while an IRQ-form
owner attempts the same lock. Do not normalize just the new IoT sites or
promote the atomicity gate from a partial-tree scan. The next code change
must establish actual callback contexts and target per-unit macro flags,
then use one compatible lock discipline across every compiled owner,
including the original DMA completion and cleanup paths. This map is a
source inventory, not a target-build or runtime proof.

### Caller netdev in private UP/DOWN request — isolated candidate, 2026-10-24

`tools/iot/prepare-virtual-if-identity-candidate.py` prepares a separate copy
of the pinned MT76x3 tree. It extends `RT_CMD_INF_UP_DOWN` with `if_dev` and
passes the actual caller `netdev` from all five open/close families (main,
MBSS, AP-client, WDS and profile/monitor). The source-coverage gate sees one
UP and one DOWN in each family; the preparer verifies the exact new call
arguments. The two generated main-interface host fixtures compile under
strict C11 and pass. This is caller identity plumbing only: `common/cmm_cfg.c`
still ignores `if_dev` and its count transition is not serialized with the
registration generation, reset and physical radio lifecycle. Do not integrate
this candidate into the production driver until the shared owner and failure
propagation are implemented and target build/runtime gates pass.

The staged driver registers all five netdev families through
`wr_iot_netdev_attach_checked`: main (`pci_main_dev.c`), MBSS (`ap_mbss.c`),
AP-client (`ap_apcli.c`), WDS (`ap_wds.c`) and monitor (`sniffer_radiotap.c`).
`check-virtual-if-call-coverage.py` now gates these five registration paths
as well as all ten UP/DOWN call sites. A source scan found that only MBSS
currently calls `wr_iot_ref_reserve`, `wr_iot_ref_open_finish`,
`wr_iot_ref_begin_close` and `wr_iot_ref_consume`; the other four families
have registry entries but no reference phase transition. Therefore a common
consumer cannot yet require `OWNED` for every DOWN or infer ownership from
registration alone. The next implementation must bind those four families
to the shared owner, carry registration generation with each request, and
propagate a failed DOWN without decrementing the physical-open count.

### Virtual DOWN failure semantics across five families — 2026-10-24

The pinned staged source confirms why changing `VIRTUAL_IF_DOWN` from `VOID`
to `INT` alone is insufficient. Its private dispatcher decrements
`VirtualIfCnt` before the last physical `rt28xx_close` call and discards that
call's result. Existing wrappers also tear down other state before issuing
DOWN and then return success:

| Family | Work before DOWN | Result after DOWN |
| --- | --- | --- |
| Main | invalidates readiness, deregisters HNAT, stops queue/carrier, calls `RTMPInfClose` | decrements module use and returns 0 |
| MBSS raw path | disables BSS beacon request, stops queue, calls MBSS close, deregisters HNAT | decrements module use and returns 0 |
| AP-client | calls APC close and deregisters HNAT | decrements module use and returns 0 |
| WDS | stops queue and deregisters HNAT | decrements module use and returns 0 |
| Monitor | calls sniffer close and deregisters HNAT | decrements module use and returns 0 |

`wr_iot_virtual_down_checked` already models a retained retry stage for the
last physical close, but only the isolated MBSS checked path calls it. It
cannot protect other callers while they still use the legacy dispatcher.
The shared owner must first reserve the exact `(netdev, generation, ticket)`
under one lock, make every family participate, then preserve an uncertain
close for a bounded retry/teardown instead of reporting success or freeing
its registration. Reissuing a partly completed physical close also needs
source-backed idempotence or a staged resume path. No production path was
modified by this audit.

### Auxiliary interface transition tickets — isolated model, 2026-10-24

The host-only `radio-transition.h` now has distinct `AUX_OPEN` and
`AUX_CLOSE` operations for AP-client, WDS and monitor rather than treating
them as MBSS. `AUX_OPEN` requires an already ready physical radio;
`AUX_START` covers a zero-reference physical start without claiming the
main interface is ready. Both share the exclusive mutation ticket and reset
fence. Auxiliary selective close
preserves the prior radio phase/readiness; the last reference uses the
physical `CLOSE` path. `virtual-down-checked.inc` recognizes an auxiliary
selective close without repeating its count decrement. Strict C11 fixtures
`check-aux-radio.c`, `check-radio-transition.c` and `check-virtual-down.c`
passed on 2026-10-24. These are sequential host model checks. The three
vendor ndo wrappers are **not** bound to these operations, and first-open
when the main interface is down requires a separate source-backed policy.
No target driver, firmware image or router behavior is established here.

The first-open path was rechecked against every child initializer. `rt28xx_open`
calls MBSS, WDS, AP-client and monitor init, but all four have persistent
already-initialized guards (`FlgMbssInit`, `flg_wds_init`, `flg_apcli_init`,
`monitor_initiated`). The earlier model rule that refused every auxiliary
first-open at `VirtualIfCnt == 0` was too restrictive and has been removed.
The isolated `wr_iot_radio_begin_aux_open` now chooses `AUX_START` for a
caller-stabilized zero count and `AUX_OPEN` otherwise. Successful `AUX_START`
marks the physical radio ready while leaving `main_ready` false and preserving
`main_inhibited`; a later explicit `MAIN_OPEN` can establish main readiness.
The strict C11 fixture checks this sequence, reset fencing and last-close
failure. The production wrappers still need the shared owner, child init
idempotence review across full teardown/reinit, target build and runtime
proof before this policy can be installed.

A reset requested during `AUX_START` or `AUX_OPEN` advances the epoch and
latches `reset_pending`. The isolated finish path now demotes a late successful
completion to `UNVERIFIED` rather than publishing `READY`; the auxiliary
fixture covers both interleavings. This is a software state assertion only:
the reset worker and hardware readback still need their production binding.
The same fixture covers main-interface DOWN during an admitted `AUX_START`:
late success leaves `main_inhibited` set and the phase `UNVERIFIED`. It cannot
establish main readiness or admit another auxiliary open until reconciliation.
This host-model check does not prove vendor close-path serialization.

Do not acquire a second transition ticket in the common virtual-UP case.
The current isolated MBSS wrapper already calls `wr_iot_radio_begin` and
`wr_iot_ref_reserve` under `wr_iot_transition_lock` before entering
`wr_iot_mbss_open_raw`; that raw path performs `MBSS_OPEN` and then calls
`VIRTUAL_IF_UP`. A dispatcher that independently begins an open would reject
this valid caller as busy, after `MBSS_OPEN` had already mutated the driver.
Use one ticket spanning wrapper preflight, family-specific mutation, common
count/physical-open step, and checked finish. The request must identify that
same ticket, device and registration generation; the dispatcher must verify
them under the owner lock and must never infer identity from a pointer alone.
Other families need equivalent outer admission before their first side effect.

`tools/iot/virtual-open-claim.h` now models the shared-dispatcher acceptance
check without opening a second ticket or changing vendor state. Under the
caller-held owner lock it requires the exact device, registration generation,
radio operation/serial/epoch and a published `RESERVED` record whose token
matches that ticket; reset, retirement and PM intent invalidate the claim.
The strict C11 `check-virtual-open-claim.c` covers MBSS, auxiliary first and
later open, stale/reused identity, wrong operation and invalidated intent.
This is **only** an admission predicate. It does not carry the claim through
`RT_CMD_INF_UP_DOWN`, perform physical open/count accounting or stage family
rollback; target compilation and device behavior remain open.

An isolated follow-up candidate at
`.iot-local-check/virtual-open-claim-v4-20261025` now does carry the MBSS
claim from its outer reserved ticket through `RT_CMD_INF_UP_DOWN` to
`cmm_cfg.c`. There, the MBSS path verifies device/generation/ticket under
`wr_iot_transition_lock` and increments `VirtualIfCnt` under that same lock
before beacon refresh. It rejects a partial claim rather than falling back to
legacy UP. `tools/iot/prepare-virtual-open-claim-candidate.py` reproduces the
transform, and the five-family call/registration gate accepts exactly this
single claimed MBSS caller while still checking the prior candidate. The v4
preparer overlays the current radio-transition, registry, MBSS admission,
checked-close and virtual-DOWN fragments; v3 inherited older copies and is
superseded. The
other four families and virtual DOWN remain legacy and cannot safely coexist
as a production owner; there is no target MIPS compile or radio observation.
Two earlier generated attempts (`virtual-open-claim-v1-20261025` and `v2`)
stopped on source-anchor checks. The executor rejected native removal of
those two local scratch copies. The preparer now preflights all known anchors
before copying; a rejected source left no new output directory in its test.

A repeated claimed UP before outer MBSS finish could otherwise increment
`VirtualIfCnt` twice with the same valid ticket. The owner now carries a
per-ticket `virtual_up_stage`, reset on admission and set atomically with the
claimed count increment. `virtual-open-claim.h` rejects a replay. The new
`prepare-virtual-open-dispatch-check.py` extracts the **actual** claimed
branch from v4 `cmm_cfg.c`; its strict C11 host fixture verifies one count
increment and beacon refresh, then rejects replay, wrong device and a
partially populated claim without further mutation. Adjacent radio/auxiliary,
registry and virtual-DOWN host fixtures passed. This is host evidence only;
the generated driver still lacks a target MIPS compilation and runtime proof.

The vendor `MBSS_ABORT_OPEN` ioctl can fail (`ap/ap_cfg.c` propagates
`MBSS_AbortOpen` failure). If claimed virtual UP fails after `MBSS_OPEN` and
abort also fails, the earlier wrapper released its module pin and reset the
registration to `IDLE` despite possible vendor mutation. The isolated v4
candidate now returns a distinct `-2` from this raw failure, retains the
module pin, marks the same generation/token `WR_REF_UNCERTAIN_OPEN`, and
finishes the radio ticket as failed. Registry release/removal and another
open are refused. The source gate checks this branch, and strict C11
reference/registry fixtures cover the retained state. This is fail-closed
bookkeeping, **not recovery**: a bounded cleanup owner, hardware observation,
target compile and device tests are still required before binding ndo_open.

Correction after inspecting the upstream `BndStrg_SetInfFlags` implementation:
its ready flag is **band-wide**, not per BSS. Calling `FALSE` when an IoT BSS
aborts can mark the still-active main 2.4-GHz interface unready. The isolated
candidate therefore leaves vendor `MBSS_AbortOpen` unchanged: it clears the
IoT beacon request only. `prepare-mbss-abort-check.py` extracts the vendor
abort body and checks that main BSS beacon intent remains set. Band Steering
state and daemon convergence require a separate per-band ownership design;
neither the earlier `FALSE` call nor a ready-flag readback proves per-BSS
cleanup. The v6 isolated candidate removes both band-wide ready/unready
updates from secondary `MBSS_Open`/`MBSS_Close`; main AP startup/shutdown
still owns those updates. The source gate rejects any such update in all
three secondary open/abort/close paths. This depends on main-radio lifecycle
serialization, which is still unresolved; do not bind this candidate to
production ndo_open yet.

Main-stop admission now has a host-only helper
`wr_iot_radio_begin_main_stop`: under the shared transition lock it latches
main-down before it attempts exclusive teardown using the stabilized virtual
interface count. A busy IoT-open ticket makes the claim fail, so the caller
must wait for that ticket to retire, recount and retry before `RTMPInfClose`
or `VIRTUAL_IF_DOWN`. Current isolated `MainVirtualIF_close` still lacks that
wait/claim binding and can mutate concurrently with the admitted IoT open.
The helper and C11 interleaving test define the needed ordering; they do not
make the staged driver safe for a production build.
Repeated stop admission while another ticket is busy must not advance the
radio epoch on every retry. The helper now latches main-down only once;
the host interleaving check asserts the epoch remains stable across a second
refused claim. This bounds ticket invalidation to the first stop intent.
The model now records `retired_serial` on successful finish or unmutated
abort, giving a waiter a ticket-specific completion predicate. Tests verify
that a stale abort does not satisfy it and that admitted IoT open retirement
does. The vendor adapter still lacks a ticket-drain wait queue and wakeups;
the predicate alone cannot make `MainVirtualIF_close` wait safely.
The isolated v8 tree now adds an adapter ticket wait queue, initializes it,
and defines a bounded wait helper that reads `retired_serial` under the common
transition lock. MBSS-open, main-open and reset retirement paths wake the
queue after unlocking. The source gate checks the queue and wakeup coverage;
the extracted helper passes a strict C11 host fixture for immediate success,
bounded completion, timeout and invalid input. `MainVirtualIF_close` still
does not invoke the helper: count ownership and checked close result remain
unresolved, so v8 must not be packaged as production firmware.
The next host-only main-stop gate compares the published `OWNED` registry
records with the vendor `VirtualIfCnt` under one adapter lock. It rejects
missing main ownership, mismatched counts, reserved/closing/uncertain records,
and a close request for a different netdevice before latching main-down.
`check-main-stop-owned.c` passed. The current vendor main/AP-client/WDS/
monitor paths do not yet acquire those records consistently, so the gate is
intentionally closed for the current isolated driver; it is not a shortcut
around migrating all five caller families.
The first family to migrate is main `ra0`. A host-only main claim predicate
now requires the exact adapter main netdevice, published reserved record,
matching generation/ticket/epoch, and a count of zero for physical START or
positive for MAIN_OPEN. A separate unmutated main-ticket abort restores prior
state only before `AP_MAIN_OPEN` and dispatcher mutation; C11 tests cover
first open, reopen, replay, wrong device/count and reset fencing. This is not
yet wired into `MainVirtualIF_open`: the zero-count physical `rt28xx_open`
may fail after partial hardware mutation, and the present dispatcher has no
checked main rollback/uncertain-owner result. Calling the predicate alone
cannot safely consume or release its module/reference pin.

The five-family identity candidate still has an unbound consumer. In its
`common/cmm_cfg.c`, virtual UP/DOWN receive `RT_CMD_INF_UP_DOWN.if_dev` but do
not inspect it: both paths change only `VirtualIfCnt`, the first UP calls
`rt28xx_open(pAd->net_dev)`, and the last DOWN calls
`rt28xx_close(pAd->net_dev)` while discarding its return. Passing `if_dev`
through the caller is therefore necessary but does not yet establish owned
references or safe rollback. The dispatcher must validate device plus
registration generation under the common owner lock, reserve/consume the
corresponding record exactly once, and keep the physical-open/close result
observable before changing the count. AP-client and monitor also perform
`APC_OPEN` / `SNIFF_OPEN` after virtual UP without testing those ioctl results;
their close paths perform specific teardown, HNAT deregistration and module
reference release before the current void virtual DOWN. The common owner
cannot safely report a recoverable failure until these wrapper side effects
are staged or given a reviewed rollback. WDS likewise stops its queue and
releases HNAT/module state before void DOWN. These are source-backed
integration requirements, not implemented runtime behavior.

Main first-open failure classification (2026-10-25): the isolated
`MainVirtualIF_open` invokes `RTMP_DRIVER_AP_MAIN_OPEN` before virtual UP.
The latter may call `rt28xx_open`; that routine clears MCU sleep, loads the
profile, requests IRQ, initializes the driver, then sets up MBSS/WDS/AP-client/
monitor and opens the adapter. `rt28xx_init` has err0–err9 cleanup labels, but
their existence does not prove complete hardware rollback. Thus a failure
after `AP_MAIN_OPEN` begins, including IRQ-request failure, must retain the
registration and module pin as `UNCERTAIN_OPEN` until a separate checked
recovery owner proves teardown. Only a refusal before `AP_MAIN_OPEN` is an
unmutated abort allowed to return the record to IDLE and release its pin.
`wr_iot_ref_complete_main_open` and its strict C11 fixture encode this
three-way result for the host model. The current isolated main wrapper still
releases the pin on `VIRTUAL_IF_UP` failure and is **not safe to bind**; next
implementation must reserve the main record before vendor mutation and
propagate dispatcher/physical-open outcomes to this owner.
The host-only `wr_iot_main_open_reserve` now joins ticket admission and the
published main-netdev registry reservation under one caller-held adapter
lock. If reservation fails after ticket admission, it aborts the unmutated
ticket; it never authorizes `AP_MAIN_OPEN` without a reserved record.
Strict C11 tests cover first START, positive-count MAIN_OPEN, replay, count
overflow and reservation failure. Generated isolated v11 contains the helper
and passed the five-family source gate, but `MainVirtualIF_open` and the
dispatcher do not call it yet. This is an admission contract, not a runtime
fix or a reason to package the candidate.
An isolated v12 source candidate now calls that reservation from
`MainVirtualIF_open` before `AP_MAIN_OPEN` and sends the ticket/generation
through `VIRTUAL_IF_UP_CLAIM`. The common dispatcher validates START or
MAIN_OPEN against the registered main netdevice and count under the adapter
lock; physical START runs after the short lock, and failed physical open
attempts to restore the count only when the same ticket still owns count 1.
The wrapper retains its module pin and an uncertain record on post-mutation
failure. `IFUP_IN_PROBE` deliberately fails compilation in this candidate
until its separate ownership path is designed. Source coverage and Python
syntax gates passed, **not** MIPS compilation or runtime. v12 remains unsafe
to package: legacy AP-client/WDS/monitor count writers bypass the common
owner, and `MainVirtualIF_close` still mutates teardown without waiting for
the open ticket or consuming a checked reference. Those paths can race with
v12's unlocked physical open and invalidate its count rollback.

Main-stop model correction (2026-10-25): after confirming an OWNED main
record and a nonzero vendor count, `wr_iot_main_stop_owned` now latches
main-down **before** requiring the registry count to match. A secondary
RESERVED or uncertain reference can therefore delay the stop ticket without
letting its admitted open publish main readiness. Repeated refused claims do
not advance the epoch again. Wrong device, missing main ownership and zero
count still refuse without changing radio state. Strict C11 main-stop and
radio-transition fixtures passed. The actual `MainVirtualIF_close` still
does not call this gate. Its ticket-drain wait must be reviewed against the
context of `ndo_stop` and any callback that needs RTNL before binding; a
bounded timeout alone cannot make that wait safe.

The Linux v4.4 `__dev_close_many` source confirms that `ndo_stop` executes
under RTNL and its return is ignored before `IFF_UP` is cleared. A failed
`MainVirtualIF_close` therefore needs a retained `CLOSING` reference/module
pin and an explicit recovery owner; returning an error does not preserve an
administratively open interface. Host-only `wr_iot_main_stop_complete`
encodes that release boundary: checked DOWN is required for selective close,
and checked DOWN plus physical verification for last-reference close. The
source and test details are in
`docs/evidence/WR1200JS-IOT-NDO-STOP-RTNL-2026-10-25.md`.
Current v12 ticket producers were traced in
`docs/evidence/WR1200JS-IOT-TICKET-RTNL-CONTEXT-2026-10-25.md`:
main/MBSS opens are `ndo_open` callbacks under RTNL; reset admission uses
`rtnl_trylock` and retires before releasing RTNL. No direct ticket wait is
bound in main `ndo_stop`. Keep it that way until a separately reviewed
adapter-lifetime-safe recovery owner can complete a deferred close after
the callback returns. The existing periodic command-worker retry is not a
liveness guarantee across worker failure and teardown.
The host `wr_iot_main_stop_request` now returns an explicit outcome:
invalid owner, deferred busy ticket (with serial), deferred recovery for an
unmatched state, or admitted stop. `ndo_stop` must hand either deferred
result to an adapter-pinned owner after returning, not wait or release the
module pin itself. The classification is tested but no workqueue/lifetime
binding has been added.

PCI removal adds an adapter-lifetime gate for any deferred close owner:
`rt_pci_remove` currently ignores `RtmpPhyNetDevExit` failure and then calls
`RtmpRaDevCtrlExit`, which frees the adapter. A netdev hold alone cannot
protect that adapter. Host-only `wr_iot_adapter_release_gate` now requires
retired child families, a physically verified DOWN radio, no active ticket,
OS TX, reset, registration or deferred owner, released registry slots and
callback quiescence. Strict C11 fixture passed. The gate is not bound to PCI
remove; the concrete hazard and remaining retirement contract are recorded
in `docs/evidence/WR1200JS-IOT-PCI-REMOVE-DEFERRED-OWNER-2026-10-25.md`.
