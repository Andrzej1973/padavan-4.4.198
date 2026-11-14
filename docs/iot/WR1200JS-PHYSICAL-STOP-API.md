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
