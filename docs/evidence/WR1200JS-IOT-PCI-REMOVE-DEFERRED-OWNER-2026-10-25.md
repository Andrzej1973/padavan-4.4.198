# PCI remove and deferred IoT owner — 2026-10-25

Source and host-model audit of isolated MT76x3 v12 and v33. No production driver,
firmware image or router was changed.

## Confirmed removal hazard

- `os/linux/pci_main_dev.c:rt_pci_remove` calls `RtmpPhyNetDevExit(pAd, net_dev)` without checking its BOOLEAN result. It then calls `RtmpRaDevCtrlExit(pAd)` and `RtmpOSNetDevFree(net_dev)`.
- `os/linux/rt_main_dev.c:RtmpPhyNetDevExit` can return `FALSE` when `RT28xx_MBSS_Remove` fails, before final main netdev detach.
- `common/rtmp_init.c:RtmpRaDevCtrlExit` calls `RTMPFreeAdapter`. Thus a deferred close/reset owner retaining an adapter pointer could use freed memory if remove proceeds after a failed child teardown.
- In v33, `RtmpPhyNetDevExit` calls AP-client, WDS and monitor removal through `VOID` wrappers. Each wrapper discards its ioctl result; only MBSS removal returns a checked status. This means the parent can report success even when one of the other three families retains a netdev.
- `ap/ap_apcli.c:ApCli_Remove` and `ap/ap_wds.c:WDS_Remove` skip an interface when `wr_iot_netdev_mark_removing` fails, then return `VOID`. `sniffer/sniffer_radiotap.c:Monitor_Remove` returns early on the same failure, also as `VOID`. On the success path each detaches/frees the netdev without proving that its checked `ndo_stop` completed or that its registry entry and callback ownership are quiescent.
- The `RTMPFreeAdapter` call at `os/linux/pci_main_dev.c:389` is a separate probe-error path. A remove-only gate must not silently change this path; probe unwind needs its own proof for partially initialized children.
- A `dev_hold` protects a netdev reference but does not by itself prevent the separate `RTMPFreeAdapter` call. The existing `wr_child_teardown_may_free_adapter` host helper accepts a broad `all_paths_quiescent` assertion; no current production caller proves or enforces it.

## Added release invariant

The host-only `tools/iot/adapter-release-gate.h` now requires all child-family
teardown done, radio retiring and physically DOWN, no busy operation/OS TX/
pending reset, no in-flight registration or deferred owners, all registry
slots released, and separate callback plus physical quiescence evidence.
`check-adapter-release-gate.c` passes strict C11 compilation and exercises
each refusal and the fully released case.

This is a release predicate, not a recovery scheduler or a safe PCI-remove
implementation. Because `rt_pci_remove` returns `void`, merely returning
early on child teardown failure would leak a partly detached PCI device and
would not solve the lifetime contract. Production integration needs a single
retirement owner that fences new callbacks, joins or terminates deferred
work, completes checked child and main teardown, proves RF/DMA quiescence,
and only then frees the adapter. Pending reset must reach a verified terminal
state before that release gate can pass. Do not bind deferred work or package
v12 before this sequence is demonstrated in the target build and fault tests.

## Next binding order established by the v33 audit

1. Make AP-client, WDS and monitor removal return checked results through the
   ioctl dispatcher and `RtmpPhyNetDevExit`. A skipped `mark_removing` must be a
   visible failure, not a silent successful removal.
2. For each family, join its close/recovery owner before detaching/freeing the
   netdev. Verify the exact registry record and callback quiescence; a successful
   `ndo_stop` return alone is insufficient because Linux unregister/close does
   not propagate that driver's failure as a release proof.
3. Give MBSS and the main netdev the same release proof, then bind one adapter
   retirement owner to PCI remove. It must fence new work, drain callbacks and
   DMA, and evaluate `wr_iot_adapter_release_ready` before `RTMPFreeAdapter`.
4. Audit the separate probe-error unwind with partial initialization. Only
   after these paths pass target compilation and fault injection may the
   isolated candidate be considered for a firmware image.

Source anchors in the pinned v33 tree: `os/linux/rt_main_dev.c:866-907`,
`os/linux/pci_main_dev.c:389,408-450`, `ap/ap_apcli.c:3470-3495`,
`ap/ap_wds.c:1346-1369`, `sniffer/sniffer_radiotap.c:480-500`, and
`ap/ap_mbss.c:207-253`. This audit changes the next integration step; it does
not implement these checked removal paths.

## Isolated WDS result propagation candidate

`tools/iot/prepare-wds-remove-result-candidate.py` generated
`.iot-local-check/wds-remove-v35-20261025` from v33 without editing the
production driver. In this candidate, `WDS_Remove` returns failure when any
WDS `mark_removing` fails; the ioctl dispatcher, `RT28xx_WDS_Remove` and
`RtmpPhyNetDevExit` propagate that result. Python syntax and a five-file
source-chain assertion passed. The first generation failed on CRLF in the
vendor wrapper; the generator now preserves source line endings, and the
partial v34 directory was removed after its path was verified.

This is one checked-result link, not a safe remove path. It does not join a
failed `ndo_stop`, prove callback/registry quiescence, repair the AP-client or
monitor `VOID` paths, or stop `rt_pci_remove` from freeing the adapter after
`RtmpPhyNetDevExit` fails. No target compiler or router validation was run.

## Isolated AP-client and monitor result propagation candidate

`tools/iot/prepare-aux-remove-result-candidate.py` generated
`.iot-local-check/aux-remove-v36-20261025` from v35. AP-client and monitor
now return failure on refused `mark_removing`; both ioctl dispatchers, their
OS wrappers and `RtmpPhyNetDevExit` pass that failure upward. The two
generators passed Python syntax checks. A source-chain assertion confirmed
both branches; a full-tree byte comparison found exactly the nine intended
files changed between v35 and v36.

This still does not make PCI remove safe: the PCI caller ignores the parent
result and frees the adapter, and detached children are not proved to have
completed checked close or callback/registry retirement. No MIPS compile,
firmware image, CI or router test was performed. Do not merge either
isolated result-propagation candidate into the production driver alone.

## Isolated post-detach close-phase gate

Inspection of `include/wr-iot-netdev-registration.inc` in v36 confirmed
`wr_iot_netdev_mark_removing` is admission only: it accepts an `OWNED` record
and does not prove that unregister's `ndo_stop` consumed the vendor reference.
The v37 candidate (`tools/iot/prepare-aux-close-phase-gate-candidate.py`) now
checks `published`, `removing`, `WR_REF_IDLE` and no in-flight registration
under the adapter transition lock after `RtmpOSNetDevDetach` but before
`rtmp_wdev_idx_unreg` and `RtmpOSNetDevFree` in WDS, AP-client and monitor.
When close remains incomplete it returns failure and retains the netdev
pointer instead of freeing it. The check must occur after detach because
unregister invokes `ndo_stop`; checking `OWNED` before detach would refuse
normal active interfaces.

Python syntax, exact five-file byte-diff inventory and source ordering checks
passed. This is still not release proof: the netdev may already be
unregistered, callback/worker quiescence is unproven, registry release is
unbound, and PCI remove still ignores the propagated failure. The worker and
adapter-retirement owner must be completed before target packaging. No MIPS
compile, image, CI or router action occurred.

**Correction after inspecting the OS helper:** v37 is unsuitable even as a
retry base. `RtmpOSNetDevDetach` calls `unregister_netdevice` and then
`vfree(pNetDevOps)`. A failure detected after that point retains a netdev
without its normal callback table. Do not package or build on v37's ordering.

The v38 isolated candidate moves the check before unregister: while holding
RTNL it calls `RtmpOSNetDevClose` (`dev_close`), verifies the record is idle,
and only then calls `RtmpOSNetDevDetach` and free. On incomplete close it
releases RTNL and leaves the interface registered for recovery. Python
syntax, exact four-file byte-diff inventory, and ordering assertions for all
three families passed. This is still a source candidate, not runtime proof:
the checked close/retry owner, lock-order audit, callback and vendor-worker
quiescence, registry release, and PCI adapter fence are still missing. No
MIPS compile, firmware image, CI or router test was performed.

## v38 retry limitation from Linux close semantics

The pinned Padavan source at
`vipshmily/padavan-4.4@c25283e915a2a00a763774dd255b14aff997285e`
has the same close path: `net/core/dev.c` calls `ndo_stop` only for an
interface with `IFF_UP`, discards its return value, then clears `IFF_UP`.
A later `dev_close` on that same down netdev does not call `ndo_stop` again.
Pinned source: <https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/net/core/dev.c>
(`__dev_close_many` and `dev_close`). The checked-in IMQ patch and
`apply-imq-vendor.py` touch includes and transmit handling in this file,
not these close functions. A final generated build-tree comparison remains
necessary before a target integration claim.

Consequently, v38 is **not a retry mechanism**. On failed checked close it
keeps the netdev registered, but the kernel can mark it down, so retrying
`dev_close` cannot advance the retained AUX_CLOSE ticket. A real owner must
call the same-ticket WDS continuation directly, with a pinned netdev and
adapter release fence, then join that work and prove registry/callback
quiescence before unregister/free. AP-client and monitor need corresponding
continuations. Do not package v38 as-is or describe it as self-recovering.

The host-only deferred-owner contract now selects a direct WDS continuation
for an exact in-flight ticket: stage 1 means retry checked DOWN; stage 4 means
finish after previously verified DOWN without repeating it. Wrong serial,
wrong family, retained-but-not-running owner and invalid stage select no action.
Only WDS may claim this owner until AP-client/monitor continuations exist. Its strict
C11 fixture passed under MinGW GCC (`-std=c11 -Wall -Wextra -Werror`). This
defines worker routing but schedules no kernel work and adds no adapter-free
fence; the candidate remains outside production.

## AP-client and monitor are not WDS-close equivalents

In pinned v38, `ApCli_VirtualIF_Close` calls `CMD_RTPRIV_IOCTL_APC_CLOSE`
before virtual DOWN. `ApCli_Close` stops the queue, can enqueue and handle
MLME disconnects, changes connection state and may free family resources.
`Monitor_VirtualIF_Close` calls `CMD_RTPRIV_IOCTL_SNIFF_CLOSE` before virtual
DOWN; `Monitor_Close` changes BSS type and the ASIC RX filter. Both wrappers
discard the family-close ioctl result and then call unchecked
`VIRTUAL_IF_DOWN`. Their failure after a partly applied family close cannot
be treated as WDS stage 1. A safe implementation needs a checked family-close
result, a separate stage for uncertain side effects, and a continuation that
does not repeat a proven or uncertain family close blindly.

The host WDS owner now explicitly refuses AP-client and monitor at queue
admission; strict C11 fixture covers both refusals. This prevents accidental
reuse of WDS-only recovery routing while their family-specific teardown is
still unresolved. No target driver or router change was made.

A separate host-only `tools/iot/aux-family-close.h` contract now records the
AP-client/monitor family ioctl and virtual DOWN as distinct stages tied to
one device/generation/ticket. A failed family ioctl enters UNCERTAIN and
cannot be replayed or advanced to DOWN. A confirmed family close allows
DOWN; only a proved unmutated DOWN failure permits its direct retry, and a
verified DOWN permits finalization. The C11 fixture passed for both families,
wrong-ticket refusal and WDS exclusion under `-Wall -Wextra -Werror`.
This does not call the vendor driver or resolve side effects of a failed
family ioctl; it establishes the failure policy for a later checked wrapper.

## MBSS unregister/free boundary rechecked — 2026-10-26

The freshly generated v40n `ap/ap_mbss.c:239-245` calls
`RtmpOSNetDevDetach(wdev->if_dev)` under RTNL and then immediately invokes
`rtmp_wdev_idx_unreg`, `RtmpOSNetDevFree` and clears `if_dev`. The OS helper
`os/linux/rt_linux.c:1619-1630` calls `unregister_netdevice` and does not
return an `ndo_stop` completion result. The current
`ap/ap_mbss_inf.c:194-219` `MBSS_VirtualIF_Close` still returns success
after legacy void `VIRTUAL_IF_DOWN`; the separately compiled checked close
has no call site. Therefore binding checked close to `ndo_stop` alone would
not be safe: an ignored incomplete close could still reach the immediate
free. The MBSS remove path must join/reconcile its retained owner and verify
the exact registry/driver state before freeing the netdev; PCI remove must
wait for all such owners and refuse adapter release until its release gate
passes. A worker that requires RTNL while remove holds RTNL would deadlock,
so its scheduling/join boundary must be designed with that ordering. This is
source evidence, not a completed implementation or runtime verification.

## MBSS remove ordering after v40 target compile — 2026-10-26

The successful isolated v40 run `40265901025` does not close this lifetime
gap. In the generated source, `wr_iot_mbss_begin_remove` admits a published
record only in `WR_REF_IDLE` and advances its retirement stage before beacon
buffer deinitialization. It does not itself call checked close or prove that
the retained owner has completed. `MBSS_Remove` then calls
`RtmpOSNetDevDetach` and frees the netdev. The OS detach helper unregisters
the interface and frees its `netdev_ops`, so a failed close discovered after
detach cannot safely be retried through `ndo_stop` or a retained netdev.

The next binding must establish a completed exact-ticket close and join any
deferred owner **before** the unregister/free boundary, while preserving a
registered netdev on incomplete close. Worker join must occur outside RTNL
if that worker can need RTNL; a later RTNL-protected pre-unregister check must
revalidate registry identity and close completion. The same ownership must
fence PCI adapter release. These are source-derived ordering requirements,
not a claim that the worker, fence, or production binding already exists.

## Local MBSS removal provenance gate — 2026-10-26

An idle registry phase alone did not distinguish a proven unmutated open
failure from an acquired reference whose close had not been verified. The
local interface record now carries `open_unmutated`, set only by the reviewed
pre-acquisition failure paths and reset on the next reserve. MBSS begin-remove
refuses an idle record with a previous token unless that proof is present or
the checked close reached stage 4. The v40 generator applies the same exact
edits to its pinned v39 header and registration helper. Local strict C11
reference and registration fixtures passed, including a fixture compiled
against the freshly generated v40p headers. Python syntax, MT7603 checked
stop and five-family caller coverage passed. This closes one admission gap
only; it does not join a retained owner, prove beacon callback quiescence,
bind checked `ndo_stop`, target-compile the new candidate or make removal
safe for production.
