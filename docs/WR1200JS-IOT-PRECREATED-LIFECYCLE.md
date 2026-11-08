# WR1200JS precreated BSS lifecycle

Status: incomplete integration; source/host and scoped target evidence only.
See [acceptance contract](IOT-WIFI-IMPLEMENTATION-CONTRACT.md).

## Owner's pre-reservation acceptance checklist (2026-11-07)

The attached MBSSID pre-reservation request is part of the active IoT task.
Architecture A is preferred. Neither hidden SSID (B) nor a speculative vendor
command (C) is an accepted fallback. A credential mismatch must refuse runtime
activation, not silently regenerate the profile or restart the radio. First
provisioning and credential changes need a separately designed cold-apply path;
ordinary ON/OFF must use only the already provisioned BSS.

| Required completion label | Current status and evidence boundary |
|---|---|
| THIRD BSS RESERVED | Cold generator and scoped MIPS compilation verified; loaded ra2 pending |
| IOT RUNTIME ENABLE/DISABLE VERIFIED | Host controller fixture only; production backend unbound |
| NO PHYSICAL WIFI RESTART DURING IOT TOGGLE | Host reserved-mode dispatch excludes profile/radio preparation; real driver path pending |
| NO CHANNEL SCAN DURING IOT TOGGLE | Source design only; instrumented physical test pending |
| MAIN/GUEST REGRESSION TESTED | Injected state preservation only; associated clients pending |
| NETWORK ISOLATION VERIFIED | Earlier native network fixtures only; final image/device IPv4 and IPv6 tests pending |
| BUILD VERIFIED | Exact-revision scoped evidence in acceptance contract; latest full integration not built |
| PHYSICAL RUNTIME VERIFIED | RUNTIME PENDING; no device operation performed for this checklist |

`check-precreated-activation.c` now exercises every ten OFF recovery stages,
including persistent failure and subsequent retry. Failure of quiescence keeps
the live BSS attached and isolation retained; later failures never reopen it.
Successful retry retains the reserved profile and the current Main/Guest model
state. These are injected backend assertions, not evidence of RF quiescence.

The prepared RC user-config loader now filters whole logical lines, rather
than independently filtering each 255-byte `fgets` chunk. Long comments and
forbidden parameters no longer leak their continuation into the profile;
permitted long values retain continuation bytes even when a chunk begins with
`#`, `;` or a forbidden key prefix. The executable fixture extracts both the
actual prepared loader and actual vendor filter. Eleven cases pass host
ASan/UBSan, including exact chunk boundaries and unterminated final lines.
This is not a loaded-driver configuration receipt or proof that every radio
profile override is compatible with the reserved BSS.

Physical acceptance must record the firmware SHA, loaded profile identity,
Main/Guest client association and continuous traffic before, throughout and
after at least 100 IoT ON/OFF cycles. Record physical open/close, MCU restart
and channel-scan counters or equivalent traced call evidence (define the
instrumentation before testing). Required delta for ordinary toggles is zero.
For each cycle check IoT DHCP/DNS/internet, bidirectional IPv4/IPv6 isolation
from LAN and Guest, and actual RF silence/client rejection after OFF. Include
saved OFF/ON reboot cases and failed enable/disable recovery. A missing counter,
packet capture or observation remains pending, never a presumed zero. Flash,
reboot and state-changing device tests require separate owner authorization.

```mermaid
flowchart TD
    C[Cold profile generation] --> S[Capture Main/Guest/IoT configuration]
    S --> V{Valid saved credentials or factory OFF entropy?}
    V -->|No| M[Keep Main/Guest profile; IoT unavailable]
    V -->|Yes| P[BssidNum=3; SSID3; WPA2PSK/AES]
    P --> I[Driver initializes reserved ra2]
    I --> D[ra2 remains administratively DOWN]
    D --> R{Runtime ON request}
    R --> L[Own config and adapter lifetime; bind immutable request]
    L --> K[Compare requested SSID/security/PMK with loaded BSS]
    K --> N[Prepare isolated bridge, firewall and DHCP/DNS]
    N --> T[Acquire BSS_OPEN ticket and current netdev generation]
    T --> A{Main READY; nonzero owned radio reference; proof current?}
    A -->|No| X[Refuse; retain isolation if rollback uncertain]
    A -->|Yes| O[Virtual MBSS open; beacon queue submission]
    O --> Q[Observe BSS and network state before reporting active]
    Q --> F[Runtime OFF: quiesce BSS and observe queue/DMA]
    F --> E{Quiescence proven?}
    E -->|No| X
    E -->|Yes| B[Detach owned bridge; restore services; retain reserved BSS]
    B --> D
```

Runtime request transport, configuration lease and production backend calls in
this diagram are required integration work, not implemented receipts. The
existing one-use proof and key matcher are unbound components. A separate
readback ioctl followed by UP does not hold RTNL across both calls.

Pinned vendor references (c25283e):

| Path | Operation and limitation |
|---|---|
| ap/ap_mbss_inf.c:132 | MBSS_VirtualIF_Open dispatches MBSS_OPEN, virtual UP, CR_ENABLE |
| common/cmm_cfg.c:1034 | Physical open only at zero reference count; Main ownership must remain valid |
| common/cmm_cfg.c:1076 | Physical close on last reference; ordinary IoT OFF must not release Main |
| ap/ap_connect.c:1720 | Optional beacon MCU update under BCN_OFFLOAD_SUPPORT |
| mcu/andes_mt.c:2191 | CmdBcnUpdateSet requests no response; send result is not completion |
| common/cmm_mac_pci.c:2678 | MT_MAC beacon DMA submission under BcnRingLock |
| common/cmm_data_pci.c:750 | PCI kickout publishes descriptor/CIDX; submission is not drain |

Exact target macro evidence is now available for optional run42407287069,
revision7e2a644d: [AP/beacon reports](evidence/WR1200JS-IOT-AP-BEACON-TARGET-2026-11-07.json).
Both actual AP and beacon translation units have MBSS_SUPPORT=true and
BCN_OFFLOAD_SUPPORT=false, AIRPLAY_SUPPORT=false, WH_EZ_SETUP=false. Archived
macro/command hashes and the actual ELF32 MIPS module hash were independently
checked. This excludes the guarded beacon MCU update for this exact build,
not every possible MCU command during open/close. The MT_MAC CR enable/disable
in ap/ap_mbss.c:246/293 uses LPON/ARB MMIO. Its success alone is not DMA drain.
AsicSetMbssMode in hw_ctrl/cmm_asic_mt.c:566 also uses MMIO; the zero-reference
physical-open branch remains excluded only while the owned Main reference is
valid. Firmware startup/restart and data/station descendants remain separate.

The existing extracted vendor reference-count test passed1000 third-reference
cycles with zero physical open/close hook calls and distinct first/last-reference
behavior. It is now included in optional CI as vendor-virtual-no-restart.json;
it explicitly does not model beacon descendants, concurrency or merged driver
behavior. These limits must remain visible when using its result.

The RC disable-controller now has an explicit precreated mode:
`wr_iot_disable_begin_precreated` captures current service settings without
taking a radio-file snapshot; `wr_iot_disable_apply_services` uses the same
scoped DNS/gate teardown; `wr_iot_disable_apply_reserved` requires bridge
absence, administrative BSS DOWN and current settings ownership, and records
completion without changing the radio file. Commit retries retain this mode
and never fall through to legacy profile removal. The actual composition
fixture verifies no profile take/remove/commit calls, service failures,
bridge/DOWN/ownership refusal and finalization retry. Full controller TU also
compiles with actual headers using the CI gnu11 dialect. Target verification
and activation/backend call-site binding remain pending. RF/DMA quiescence,
loaded credential proof and Main/Guest lifetime remain the outer owner's
obligations; administrative DOWN is insufficient for those claims.

Target follow-up (2026-11-08): ABI run42410701865 succeeded for6e7b018.
The actual 15444-byte ELF32 little-endian MIPS ET_REL controller object was
independently parsed; its defined symbol table contains nonempty reserved
begin/apply and commit functions. See [object evidence](evidence/WR1200JS-IOT-RESERVED-OFF-TARGET-2026-11-08.json).
This closes the scoped target translation-unit gate, not linked RC/image,
activation binding or device runtime. Optional run42436571351 verifies the
same exact revision separately.

No ACK allocation/reuse changes are part of this strategy. Initial startup and
ordinary radio restart can still encounter the unresolved ROM ACK issue.
Physical WR1200JS tests must establish Main/Guest continuity, no channel scan,
IoT RF silence when OFF, DHCP/DNS/internet and IPv4/IPv6 isolation. A successful
build or DMA submission cannot establish those properties.

Integrated host follow-up: the request-snapshot fixture now links the actual
request-stage, request-snapshot, disable-services, disable-controller and
profile units. All six partial temporary-credential cleanup failures retain
reserved mode, lock and receipt, keep gates closed and complete on retry.
A foreign credential change after reserved-apply refuses commit without writes;
it remains untouched and ownership stays retained. ASan/UBSan passes. DNS,
NVRAM and netdev hooks remain injected; no RF or production backend claim.
ABI workflow now links these units for this fixture; new CI execution pending.

Owner decision (2026-11-08): a new documented Linux RC-to-driver API is
explicitly authorized. Firmware protocol and stale-ACK protection remain
unchanged. New driver-api-wire.h defines a144-byte OPEN request: WRI1/op1,
BE64 adapter epoch and netdev generation,16-byte nonzero request identifier,
explicit SSID/key lengths, zero reserved bytes and canonical zero padding.
Decoder wipes output on refusal and its temporary credential copy on every
exit. Syntax acceptance grants no driver permission. Admission must validate
UTF-8/security, derive and compare PMK under task/config ownership, revalidate
registry/ticket/epoch, and invoke the existing MBSS open within that ownership.
No key/PMK may be returned. Retry/status must use nonsecret transaction identity.

Transport audit: pinned net/core/dev_ioctl.c serializes SIOCDEVPRIVATE through
RTNL, but its default private branch does not itself check CAP_NET_ADMIN.
The new driver entry must check namespace capability explicitly. Vendor
rt_os.h's0x8BE0 SIOCDEVPRIVATE fallback applies only to WIRELESS_EXT<=11;
normal Linux private-device range and WEXT range must not be conflated.
No ioctl number, dispatcher binding or production activation is installed yet.
The existing wr_iot_linux_ioctl_raw wrapper holds a control admission; blindly
routing OPEN beneath it would conflict with the BSS_OPEN owner. Resolve this
explicitly when binding the new entry, retaining all non-IoT admission rules.

New API entry implementation is staged as driver-api-open-entry.inc, still
uninstalled: under the kernel ioctl RTNL contract it checks namespace
CAP_NET_ADMIN before copying144 bytes once, rejects non-MT7603/already-running
interfaces, decodes the request, requires strong request_enter ownership, calls
existing dev_open, always leaves an entered owner, and reports EUCLEAN if owner
release cannot be confirmed. Both local wire and decoded credentials are wiped.
Its success is netdev-open completion only; RF/network observation is separate.
The extracted actual entry passes host ASan/UBSan privilege, copy, syntax,
stale-owner, open-error and leave-error tests with injected kernel hooks.
No permissive owner implementation, ioctl number or dispatcher was added.
The CI host fixture list now includes wire/entry tests; target proof pending.

OPEN owner model now reserves the existing BSS_OPEN ticket and registry slot
before dev_open, under the transition lock. It refuses active control users,
blocked control/bootstrap state, stale expected epoch/generation or missing
owned Main/vendor count. MBSS must borrow that same ticket and consume the
request once for the same task/netdev; it must not start a second ticket.
Unconsumed current reservation can be canceled when dev_open fails before
ndo_open. Uncertain consumed/ticket retirement poisons the owner and wipes
credentials/task pointer while retaining nonsecret claim/ticket recovery
identity; retained pointer identity is not a lifetime pin. No automatic poison
clear is supplied. Host ASan/UBSan model tests pass. Driver adapter fields,
control exclusion, credential compare and MBSS entry binding remain required.

Adapter request enter/leave wrappers are implemented locally in
 driver-api-owner-binding.inc. Enter checks actual MT7603 third-netdev mapping
and bounded BssidNum while holding wr_iot_transition_lock, then reserves against
actual registry/vendor count/control/bootstrap state. Leave uses the same lock
and propagates uncertain owner state into wr_iot_control_poisoned. The actual
wrappers, OPEN entry and owner model pass a composed ASan/UBSan fixture; only
kernel/netdev hooks and device-open body are injected. A fixture-only current
macro initially collided with the wrapper task argument and was corrected to
use a distinct current_task_identity symbol. No target-source change was needed
for that harness failure. Driver fields/dispatcher and MBSS borrow/key proof
still need a checked generator; this code is not installed or target-verified.

Checked candidate installer prepare-driver-api.py is implemented locally.
It refuses changed manifests/anchors or an existing literal0x89ff collision,
adds/initializes adapter owner storage, guards control admission while owner
is active/poisoned, and routes WR_IOT_DRIVER_IOCTL_OPEN0x89ff before the ordinary
control lease. The audited pinned driver uses WEXT private0x8be0+ commands;
this newly allocated Linux device-private slot is an explicit new API.
Third-BSS MBSS open consumes its already reserved request/ticket, compares
loaded PMK outside the spinlock, and revalidates the same claim before raw open.
Main/Guest retain their previous admission path. No firmware command added.

Installer applied successfully to an exact hash-checked copy of the retained
channel-scan candidate, after its precreated-admission layer. Source ordering
checks pass; four API host fixtures pass ASan/UBSan. This retained candidate
predates latest CI and this is not target proof. The temporary source copy
was removed automatically. Installer is not yet enabled in the full pipeline:
existing extraction checkers need to understand the changed wrapper, and fresh
whole-TU/module compilation must pass before publication. A nonsecret identity
query for RC to obtain the expected epoch/netdev generation is also required.

The actual transformed MBSS wrapper now passes an executable host fixture:
correct key/Main accepts one borrowed ticket; key mismatch or reset during
key work never reaches raw-open; ordinary third-BSS open without an API owner
refuses; Guest follows its previous path. Post-open observation failure leaves
radio UNVERIFIED and the API owner refuses clean completion. The owner binding
also wakes ticket waiters outside its lock when canceling before ndo_open.
The composed entry test verifies this early cancellation and waiter wake.

The installer/checker is now staged at the end of peer82 preparation, after
predecessor extraction fixtures and before final source copy/hash/Kbuild.
The API's transformed wrapper has its own executable fixture. Predecessor
fixture success must not be represented as exercising final API semantics.
Fresh GitHub target compilation and nonsecret identity query remain pending.

Local API follow-up adds CLOSED-BSS identity ioctl0x89fe. It requires RTNL and
namespace CAP_NET_ADMIN, verifies exact third BSS, owned Main/vendor references,
idle/nonpoisoned control/bootstrap and READY/nonreset/PM state under the same
transition lock, then copies a zero-initialized32-byte WRI1/op2 response outside
the lock. Response contains only BE64 adapter epoch and netdev generation;
no SSID/key/PMK and no admission ticket. OPEN still rejects stale identities.
Wire tests cover64-bit endianness, exact lengths, reserved bytes and zero output
on refusal. Actual query entry is composed with adapter owner in ASan/UBSan
fixture: privilege before copy, wrong-device/reset/poison refusal, copy error,
correct response and no ticket/owner mutation all pass. Checked installer routes
both new ioctls and audits both literal numbers. Retained-source generation and
MBSS regression pass. New identity code remains local; MIPS query proof pending.

RC transport now has driver-api-client.c/.h: fixed ra2, CLOEXEC datagram socket,
strict identity response decode and canonical OPEN encoding. Failure before
OPEN ioctl is NOT_SUBMITTED; any attempted ioctl error or subsequent close
error is OPEN_UNCERTAIN. OPEN_COMPLETED means synchronous netdev-open only,
never device/network acceptance. No automatic ioctl retry or logging of keys.
The client wipes its wire credential buffer on all exits. Actual client host
fixture passes ASan/UBSan with injected socket/ioctl/close, including partial
outcome classification. Prepared RC stages/links the client and ABI workflow
compiles its MIPS object; the actual staging block/native TU and YAML parse
pass locally. Full fresh generation and target client proof remain pending.
Activation call sites still need to map uncertainty into retained recovery.
