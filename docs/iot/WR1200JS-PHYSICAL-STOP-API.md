# Experimental Linux physical-stop transactions

Scope: WR1200JS MT7603, isolated immutable ra2 no-host candidate only.
Not installed in the standard image. Firmware ACK protocol is unchanged.
Host/source tests do not certify RF, DMA, IRQ or device acceptance.

The existing private `WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG` (`0x89fd`) routes
64-byte requests with the exact `WPSQ` prefix to the physical-stop wrapper.
The route follows RTNL, namespace CAP_NET_ADMIN and MT7603 checks. The wrapper
rechecks privilege, exact Main device and third BSS identity, copies and validates
its own complete request. Its second input copy is independently validated;
the routing copy does not authorize an operation or supply retained identity.
Existing CLOSED/recovery requests retain their earlier dispatch.

Request version1: action at byte5; reserved bytes6/7 zero; big-endian u64
fields epoch8, IoT registration generation16, original IoT OPEN token24,
IoT CLOSE serial32, physical attempt40; nonzero 16-byte nonce48. ARM attempt
must be0; QUERY/CANCEL/RELEASE must use the exact assigned nonzero attempt.
Responses use `WPSR`, action5, status6 and reserved7, echo the request identity
and assigned attempt. See physical-stop-wire.h and physical-stop-response.h.
These are Linux metadata, not firmware command fields.

Use the same retained issuing task for the transaction. Its extra task/module/
Main-netdev references persist in adapter storage. A numeric PID is not accepted
as owner identity. Main registry identity and original IoT identity are separate.

1. Complete normal owned IoT OFF and reference release; preserve isolation.
2. ARM on Main validates that released IoT CLOSE and snapshots live Main/radio
   identity. It acquires extra references and publishes ARMED. It never issues
   DOWN. Retrying an identical ARM observes the same record without extra holds.
3. The existing Main close path delegates physical shutdown to its recovery
   worker. The worker captures its exact ticket and atomically claims the record
   RUNNING before checked DOWN. An already cancelled record cannot execute DOWN.
4. QUERY never submits work or waits. Exact request validation precedes recording
   already-completed Main software receipts. Unknown/uncertain state returns an
   error and retains ownership; it does not authorize reopening.
5. CANCEL is permitted only before Main starts closing and only for ARMED. It
   returns extras outside locks, ends the lifetime and retains a CANCELLED reply.
6. RELEASE requires the exact post-reference-return Main receipt, shutdown2,
   radio-off4, virtual-down2, idle executor and closed/drained peer table. It
   returns extras, ends lifetime and retains a RELEASED reply. Those stages are
   existing software receipts, not an independent hardware retirement proof.
7. Duplicate terminal replies do not repeat cleanup. A new valid ARM with a
   different nonce may replace the same issuer's old terminal cache; failed
   admission restores it. Final raw-free fencing returns the PID reference only
   after physical lifetime/pin bundles and existing recovery owners are absent.

The implementation keeps transition, beacon and MacTab locks disjoint. The
current target must have CONFIG_PM=n; zero-interface PCI suspend synchronization
is unfinished. RC orchestration, full target verification of this endpoint and
physical WR1200JS acceptance remain required. Do not enable production startup
or permit post-OPEN RC restart based solely on these source fixtures.

`physical-stop-client.c` provides fixed-ra0 userspace transport for these four
operations. It returns NOT_SUBMITTED for invalid input/socket acquisition,
UNCERTAIN after attempted ioctl/close/response validation failure, and
ACKNOWLEDGED only for an exact typed reply. It performs no automatic retry and
never changes interface flags. The separate fixed DOWN helper is linked into
the experimental RC candidate but neither helper is called by production RC
or the current initial-only radio-stop callback. Retained RC orchestration and
Main/Guest stop order remain pending.

`physical-stop-session.c` now retains the exact issuing PID and request across
one-operation advances in the experimental RC link. Lost ARM replies retry the
identical ARM before DOWN; DOWN is submitted at most once. NOT_SUBMITTED DOWN
selects CANCEL; possibly submitted DOWN selects QUERY. ARMED/RUNNING/FAILED or
unavailable QUERY retain the session without another DOWN or reopen permission.
Only COMPLETE selects RELEASE, and only its acknowledged reply completes the
session. Lost CANCEL/RELEASE replies repeat the identical terminal operation.
Foreign PID and recursive advances refuse without transport calls.
The caller must retain actual shutdown/service admission across the whole
session; ownership of those guards, scheduler wiring, fresh CLOSE extraction,
and Main/Guest stop order integration are still pending. No production callback
is switched by linking this unit. No elapsed timeout is a completion proof.

`rc-physical-stop.c` retains a validated stop/restart intent, service guard and
normal-shutdown fence in one RC-process context. Beginning refuses another
active shutdown owner, requires a fresh private backend OFF/CLOSE receipt and
nonblocking entropy, and claims no firmware state until the session ARM step.
Preparation failure still receives balanced deferred cleanup. The PID1 wait
loop advances pending physical sessions at the existing100ms cadence. Guard
revalidation failure retains state; lost replies never release the guards.
Terminal consumption returns the copied intent exactly once, after guard and
signal cleanup. It does not run stock restart, attest a fresh reopen identity
or turn a completed receipt into an unlimited restart lease.
The actual stop/restart entry-point admission, active-IoT OFF initiation, AUX/
Guest ordering, deferred intent consumer and fresh safe-reopen validation remain
unbound. `physical_stop_rc_orchestration` therefore remains false.

The retained controller now advances the exact SDK AUX order before ARM:
APCLI, WDS3, WDS2, WDS1, WDS0, Guest. The prepared `net_wifi.c` adapter
uses existing `IFNAME_2G_*` constants and its existing private `wif_control`.
There is no Main slot. Each continuation attempts one slot; command or lookup
errors retain that slot and guards. ENODEV/ENXIO from an absent optional
interface completes only that administrative slot, without claiming driver
retirement. After all slots, the private backend CLOSE is read afresh; ARM
identity comes from that read, rather than the pre-AUX snapshot. Missing fresh
CLOSE retains the operation without issuing Main DOWN. Actual peer/worker
retirement remains required by the subsequent physical Main driver receipt.
This does not initiate OFF for an ACTIVE IoT owner or enable stock entrypoints.

`rc-quiesce.h` and the private backend now provide preparation of an ACTIVE IoT
owner for physical-stop integration. Admission first observes the actual ACTIVE
owner's configuration/network state, then copies its desired request into a
private same-process context before initiating existing normal OFF. OFF uses
its original CLOSE/progress/release and network-isolation path, without replay.
The desired request survives normal OFF clearing the runner's original request.
No SSID/password is added to output, mailbox records or telemetry by this API.
Advance retains the original OFF identity and admission; only a fresh released
CLOSE completes preparation. Already OFF has no inferred desired ON state.
The physical controller does not yet call this preparation: its future caller
must retain the desired request until post-radio-restart identity validation and
resume are implemented. Do not clear that context at physical RELEASE or reuse
the old adapter's CLOSE as an OPEN permission for a replacement epoch.
