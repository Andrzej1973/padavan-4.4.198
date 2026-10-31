# WR1200JS isolated IoT v40 target compile — build #600

GitHub Actions run [#600](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40216625327)
completed successfully on branch `codex/wr1200js-service-webui`, HEAD
`a71e8abedf4c2a6c1fd5df2917002db990df84e2`, attempt 1. The run was dispatched
with the optional candidate checks enabled and `iot_candidate_variant=v40`.
Both `Build WR1200JS firmware` and `Compile isolated merged IoT MT7603
candidate` succeeded.

## Target artifact

The `iot-merged-driver-probe` artifact (GitHub artifact ID `12607858175`,
2,038,264-byte ZIP) contains `mt76x3_ap.ko` and its complete candidate build
log and metadata:

- Module size: 5,202,152 bytes.
- SHA-256: `f01a3272ac60769dd08a312fbe67622284fa590a533285335a749a300b75a4e5`.
- ELF: ELF32, little-endian, relocatable MIPS, O32, MIPS32r2.
- Source: pinned MediaTek tree revision
  `c25283e915a2a00a763774dd255b14aff997285e`; 58 candidate overlay paths were
  assembled against the prepared tree before compilation.
- Target compile log ends with `LD [M] .../mt76x3_ap.ko` followed by successful
  `make` exit.

For comparison, build #595's earlier isolated `mt76x3_ap.ko` was 5,200,856
bytes with SHA-256
`2be70edfa1dd9eaa9402560000111f89657d456134072e91cc4b6d5e874a2039`. The v40
module is 1,296 bytes larger. This is an uncompressed module-file comparison,
not an estimate of firmware image growth.

## Warning and evidence boundaries

The candidate build log reports one non-fatal kernel `modpost` warning:
`Found 1 section mismatch(es)`. The log does not identify the specific symbol;
its source and whether it predates v40 are therefore unresolved. This warning
did not fail the module link. Investigate it with detailed section-mismatch
diagnostics before production integration if it is attributable to the overlay.
The isolated v39 build #595 log also reports one section mismatch at the
155-module `MODPOST` step. This establishes that the warning count was present
before v40, but does not identify either symbol or prove both warnings have the
same cause.

The artifact's source manifest keeps `target_compiled=false` as source-package
metadata; the separate successful target build log, MIPS ELF header and module
artifact are the compile evidence. The workflow compiles this probe after the
ordinary firmware image is built, so this candidate is **not included in the
#600 firmware image**. No production driver, final ROMFS, router or runtime
behavior was validated by this candidate step. In particular, the MCU command
result plus PDMA readback does not prove RF silence, callback quiescence, safe
main-interface close, safe PCI removal, IoT isolation, or live third-BSS
operation.

## Next gates

1. Explain the `modpost` section mismatch without assuming it belongs to v40.
2. Bind checked main stop to an adapter-pinned recovery owner; the current
   `MainVirtualIF_close` still releases its module pin without physical-close
   proof.
3. Bind child/root teardown, callback quiescence, worker stop/join and the
   adapter-release gate into PCI remove, including persistent failure behavior
   for its `void` callback.
4. Re-run the isolated target compile after any source integration. Only after
   those lifecycle gates pass should candidate image packaging and final-ROMFS
   checks begin; device acceptance remains a separately authorized stage.

No router settings, firmware or runtime services were changed.

## Main-interface source reachability, follow-up

The generated v40 source still routes `MainVirtualIF_close` through
`RTMPInfClose` and legacy `VIRTUAL_IF_DOWN`, then releases the module pin
(`os/linux/rt_main_dev.c:112-143`). In the shared dispatcher,
`CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN` decrements `VirtualIfCnt` and calls the
legacy `rt28xx_close` on the last reference without a checked result
(`common/cmm_cfg.c:1150-1160`). The checked `wr_iot_virtual_down_checked`
helper has WDS call sites in this overlay but is not bound to main close.

The separate local `prepare-main-open-owner-candidate.py` does not close that
gap. It reserves a main-open ticket and record, then calls
`wr_iot_radio_finish_unverified` after virtual UP. That function deliberately
leaves the transition in `UNVERIFIED` with `main_ready=0`; `WR_RADIO_BSS_OPEN`
requires `READY` and `main_ready=1` (`tools/iot/radio-transition.h`). No
main-radio readback/verification owner is bound in the generated v40 source.
The generator also reports that legacy family count writers and main close
bypass its owner. Therefore the main-open overlay cannot be packaged as a
complete IoT activation path.

Next implementation must serialize every vendor count writer with the shared
registry and transition lock, bind checked main stop and retained recovery,
and produce a reviewed radio-ready observation before admitting IoT BSS open.
That observation must remain atomic with the ticket and epoch checks; a
successful software UP alone is insufficient. PCI release still requires the
separate physical and callback quiescence gates above.

## Local main-readiness owner gate

The local, unbound `tools/iot/virtual-open-claim.h` now provides
`wr_iot_main_radio_verify_owned`. After a bounded observation performed outside
the adapter lock, its caller must hold the shared transition lock while it
checks the live VERIFY ticket, published owned MAIN record, complete vendor
reference count and current radio epoch. A missing owner or stale observation
retires the ticket without publishing `READY`; the secondary BSS remains
inadmissible. The result does not establish physical RF readiness on its own.

The corresponding `check-virtual-open-claim.c` host fixture passed with MinGW
GCC `-std=c11 -Wall -Wextra -Werror`. It covered a valid owner and rejection
for count mismatch, wrong family, unpublished/removing main record, failed
observation, and main-down during VERIFY. This is host model evidence only.
Binding the actual MT7603 observer after `ndo_open`, instrumenting every
vendor count writer and proving adapter/netdev lifetime are still required
before this gate can be used by the source candidate or the firmware image.

## Main beacon register observer correction (local, after #600)

Source review found a concrete error in the local `mt7603-main-observe.h`:
it rejected `ARB_BCNQCR0` bit 2 as if that were IoT BSS 2's queue-start bit.
The pinned driver's `ap/ap_mbss.c` starts and stops a secondary queue using
`1U << (BssId + 15)`; BSS 2 therefore uses bit 17. Its main queue uses bit 0
in `hw_ctrl/cmm_asic_mt.c`. The observer now requires bit 0 and rejects bit
17. The host fixture first failed against the old predicate, then passed with
both bit-17 rejection and bit-2 non-rejection cases under MinGW GCC
`-std=c11 -Wall -Wextra -Werror`. This is only local host evidence. Existing
generated candidate directories retain their earlier copied header until
regenerated, and no target compile or firmware image includes this correction.

The pinned kernel `net/core/dev.c` sets `__LINK_STATE_START` before calling
`ndo_open` and clears it before `ndo_stop`; this makes `netif_running(main)`
possible during main open. It does not prove that the driver's main beacon
request and hardware queue have settled at that point. Verify the observer's
placement and source lifetime before binding a VERIFY ticket or enabling IoT.

The same kernel ordering exposed a second local observer defect: the staged
`MBSS_VirtualIF_Open` calls this observer *inside the IoT netdev's `ndo_open`*.
At that moment `netif_running(iot)` is already true even though IoT's beacon
request and queue have not been enabled. Requiring `!netif_running(iot)` made
the staged IoT admission fail every time. The observer no longer uses that
bit as a pre-open test; the caller's BSS_OPEN ticket and registry reservation
establish admission, while `bBcnSntReq` and queue bit 17 test whether this
BSS has begun beaconing. The focused host fixture failed before this change
and passed afterward with the IoT netdev START bit set. This remains a local
predicate correction, not target-build or runtime acceptance evidence.

The optional isolated candidate CI step now requires the staged observer
header to match the local source and runs `check-capacity.py` with
`--check-main-observer`. The next candidate build must compile the observer
under its recorded MIPS Kbuild flags and report `status=compiled`; #600 had
`main_observer_probe=null` and does not gain this evidence retroactively.
Locally, PyYAML parsed the workflow as one job, `git diff --check` passed,
and the focused MinGW host fixture passed. No new target build was run.

## Guest then IoT open ordering (local follow-up)

The staged `MBSS_VirtualIF_Open` retires every successful BSS_OPEN with
`wr_iot_radio_finish_unverified`. `wr_iot_radio_begin` permits the next
BSS_OPEN only from `READY` with `main_ready=1`. Thus opening guest first
leaves `UNVERIFIED` and blocks the next IoT open even if the guest netdev
returned success. The staged raw wrapper also ignores the return from
`CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE`, so its zero return cannot close this gap.

A local, still unbound post-open MT7603 configuration observer now checks
the selected guest/IoT netdev identity, requested beacon state, main queue
bit 0 and the selected BSS queue bit (`BssId + 15`) under `BcnRingLock`.
The host fixture covers guest and IoT success plus missing queue/request,
wrong device, invalid BSS index and reset during read; it passed with strict
MinGW C11 warnings. The target observer probe now compiles both pre-open
and post-open entry points when the optional candidate gate next runs;
Python syntax and `git diff --check` passed locally. This observer does not
prove emitted RF frames. Binding it requires checked CR_ENABLE result,
retained module/reference ownership on partial failure, and same-ticket
radio/registry revalidation before publishing READY. No source candidate,
firmware image, or router now uses this post-open observer.

## Checked CR_ENABLE outcome in the local assembler

The local `prepare-radio-queue-candidate.py` now replaces the raw MBSS
`CR_ENABLE` fire-and-forget call with a checked return. A failure after
`VIRTUAL_IF_UP_CLAIM` returns the existing uncertain-open code `-2` before
HNAT registration or netdev queue start. The staged admission wrapper retains
the module pin and registration, retires the ticket without publishing READY,
and returns failure
from `ndo_open`; a future recovery owner must still finish the vendor count
and hardware teardown because the kernel will not call `ndo_stop` after a
failed open. The source replacement requires exactly one pinned anchor, so
source drift fails assembly rather than silently restoring unchecked behavior.
Python syntax, anchor cardinality against the prior v40 generated source, and
`git diff --check` passed locally. No regenerated target candidate or MIPS
compile has run for this assembler edit. Successful CR_ENABLE plus post-open
readback still needs same-ticket/registry verification before READY can be
published; guest-first then IoT remains blocked until that is bound.

The replacement now lives in one `mbss_cr_enable.py` helper used by the
assembler and a focused generated-C host fixture. The fixture extracts the
prior v40 raw wrapper, applies that helper, compiles it with MinGW GCC
`-std=c11 -Wall -Wextra -Werror`, and injects success, MBSS_OPEN failure,
virtual-UP failure with successful/failed abort, and CR_ENABLE failure.
All five paths passed. Specifically, failed CR_ENABLE retained one module
reference and one claimed vendor count while skipping queue publication.
The fixture cannot prove target compilation, recovery after failed `ndo_open`
or radio behavior.

The optional isolated candidate workflow now runs that focused host fixture
against its assembled `ap_mbss_inf.c` before the MIPS module build. For a
previous unguarded v40 source the fixture applies the shared transform; for
an assembled guarded source it compiles that exact raw function. Local checks
passed for the old-source transform and for the guard recognition path;
PyYAML parsed the workflow and `git diff --check` passed. This is a future
CI gate, not evidence that a new candidate run has completed.

## Local v40f post-open receipt, after #600

`prepare-mt7603-checked-off-candidate.py` now copies the current MT7603
observer and open-claim helper, checks `CR_ENABLE`, and generates the MBSS
post-open receipt while retaining the v39 claimed raw-open signature and all
three ticket-retirement wakeups. It produced the separate local
`.iot-local-check/mt7603-radio-off-v40f-20261025` tree. The generated wrapper
passed `check-mbss-post-open.c` with strict MinGW C11 warnings: guest then IoT,
failed readback, count mismatch and reset during receipt. The generated raw
open also passed `check_mbss_cr_enable.py`; five-family call coverage and eight
remove-result pairs passed. The optional v40 CI path now compiles and runs the
post-open fixture before its target module build. YAML parsed as one job and
`git diff --check` passed.

No local MIPS compiler or pinned Linux build tree is present in this Windows
workspace; the available #600 artifact predates v40f. Therefore no target
compile, module/image packaging or device behavior is established for v40f.
The next target evidence must come from the optional isolated CI module job
using these exact source bytes. Close/recovery and PCI-release ownership remain
separate blockers before installing any driver in a production image.

The v40 host gate was corrected to search the generated candidate's include
directory before local `tools/iot` headers. The focused test was rerun with
that ordering and passed against the v40f wrapper, its copied transition and
registry headers, and its copied open-claim helper. This prevents a host pass
that accidentally compiles the local helper while the candidate retains an
older copy. The local workspace still has no target toolchain, so this is
stronger source/host evidence rather than a MIPS build result.

The v40 assembler now pins the exact reviewed v39 MBSS admission fragment
before replacing it. This prevents a future v39 edit from being silently
discarded by the generated post-open wrapper. A fresh isolated v40g assembly
passed this pin and the guest-to-IoT fixture using its generated headers.

## Distinct MBSS partial-open outcomes (local v40h)

Source review confirmed that failed `MBSS_ABORT_OPEN` follows a failed
`VIRTUAL_IF_UP_CLAIM`, so its vendor count remains uncertain. In contrast,
`CR_ENABLE` runs only after the claimed virtual-UP returned success and
incremented `VirtualIfCnt`. The earlier raw result `-2` conflated those
states. The guarded CR_ENABLE path now returns `-3`; the admission wrapper
retains an OWNED record and module pin with radio FAULT for that acquired
count, while `-2` retains UNCERTAIN_OPEN. Neither failed `ndo_open` receives
an automatic `ndo_stop` callback. The separate adapter-pinned recovery owner
is still required before production use.

Fresh isolated v40h assembly passed its pinned v39-fragment check. Strict
MinGW C11 tests against v40h's generated headers covered both distinct
partial-open outcomes as well as guest-to-IoT, readback, count and reset
cases. The extracted generated raw wrapper passed the CR_ENABLE fixture.
No target compile, firmware image or router runtime is implied.

The recovery path cannot be borrowed from the existing WDS host model:
`aux-close-recovery-owner.h` explicitly accepts only WDS close stages 1/4.
The v40 MBSS netdev still has `netDevHook.stop = MBSS_VirtualIF_Close`, whose
legacy body discards CR_DISABLE, MBSS_CLOSE and virtual-DOWN results. The
separate `wr_iot_mbss_begin_close`/`wr_iot_mbss_close_checked` candidate is
not called by that netdev hook. After a failed `ndo_open`, Linux does not call
the hook at all. Thus OWNED on `-3` makes the acquired count identifiable,
but does not itself free it. A dedicated MBSS recovery owner must hold the
netdev and adapter lifetime, claim/continue the checked BSS_CLOSE ticket,
join before PCI adapter free, and retain the module pin on incomplete close.
The `-2` uncertain-count path additionally needs vendor-state reconciliation
before a decrement may be attempted. Neither owner is bound yet.

## MBSS checked-close admission count gate (local v40i)

The isolated `wr_iot_mbss_begin_close` previously chose a last/non-last
radio ticket from `VirtualIfCnt` without proving that every counted vendor
reference had an owned, published registry record. That was unsafe for the
new acquired `-3` recovery path and for ordinary MBSS close. It now requires
an MBSS-family owned record and `wr_iot_registry_count_matches` under the
same transition lock before taking the stop ticket. The v40 assembler pins
the reviewed v39 close fragment and copies this corrected candidate. A fresh
v40i assembly and strict C11 close fixture against its copied headers passed;
the fixture first refuses a missing main owner, then admits the matching
two-reference state, and retains prior failure/retry cases. The optional v40
CI path now runs this close-admission fixture before the module compile.

This guard is only valid after every vendor count writer shares the lock and
registry ownership contract. Legacy bypasses and the lack of an adapter-pinned
MBSS recovery worker still prevent production binding. No MIPS/image/device
claim follows from this host test.

## Unclaimed virtual-UP writer removed from isolated v40j — 2026-10-26

The generated v40i source has five active virtual-UP call sites: main, MBSS,
WDS, AP-client and monitor. Each calls `VIRTUAL_IF_UP_CLAIM`; the old
`VIRTUAL_IF_UP` wrapper has no caller. In `common/cmm_cfg.c`, however, a
request with no owner fields could still enter the legacy UP branch,
increment `VirtualIfCnt` without the transition lock and, on first-open
failure, decrement it without the lock. This contradicted the new checked
close count/registry admission rule.

The v40 assembler now rejects any active use of the unclaimed wrapper and
replaces the legacy UP branch with `NDIS_STATUS_FAILURE`. The claimed main,
BSS and auxiliary count writes retain the common transition lock. Fresh
isolated v40j assembly passed; source search found only the unused wrapper
definition. Candidate-header MBSS close and post-open strict C11 fixtures,
the raw CR_ENABLE fixture, Python syntax and `git diff --check` passed.

This does not complete the count invariant: main, MBSS, AP-client and monitor
legacy stop paths still call void `VIRTUAL_IF_DOWN`, while WDS has a distinct
checked-down path. The legacy dispatcher decrements without the transition
lock and discards the physical-close result. Next bind all stop paths to
checked owner-aware DOWN, then the MBSS recovery owner and PCI release fence.
v40j has no manifest, MIPS compile, image or device proof.

## Legacy virtual-DOWN caller audit — 2026-10-26

The v40j source has four active calls to void `VIRTUAL_IF_DOWN`:

| Caller | Preceding operation | Missing ownership/result proof |
| --- | --- | --- |
| `os/linux/rt_main_dev.c:138` | `RTMPInfClose`, queue/carrier/HNAT changes | Main stop request/continuation is not bound; physical close result is discarded. |
| `ap/ap_mbss_inf.c:214` | CR_DISABLE, queue stop, MBSS_CLOSE, HNAT | The separate checked MBSS close exists but the netdev stop hook still calls this legacy body. |
| `ap/ap_apcli_inf.c:173` | APC_CLOSE, HNAT | Its ioctl returns failure when `ApCli_Close` returns FALSE, but the caller discards it; `ApCli_Close` can disconnect or alter state before returning. |
| `os/linux/rt_profile.c:1502` | SNIFF_CLOSE, HNAT | Its ioctl returns failure when `Monitor_Close` returns FALSE, but the caller discards it; `Monitor_Close` changes BSS mode and RX filter before success. |

WDS is distinct: `ap/ap_wds_inf.c` calls `wr_iot_virtual_down_checked`
under a retained AUX_CLOSE ticket and records the count stage. The legacy
dispatcher in `common/cmm_cfg.c` still decrements `VirtualIfCnt` without the
common transition lock and calls a void physical close on the last count.
Thus locking that decrement alone would not establish the needed owner,
stage or result contract.

Binding order: (1) give main and MBSS stop paths retained owners and use their
existing checked-close candidates; (2) for AP-client and monitor, record the
exact family-close outcome and reconcile uncertain side effects before
checked virtual DOWN; (3) retire the four legacy callers and only then reject
unclaimed DOWN in the dispatcher; (4) join every retained owner before PCI
adapter release. Failed `ndo_stop` cannot rely on a later kernel retry.
This source audit does not change the driver or prove target/runtime behavior.
The v40 assembler now requires exactly these four legacy DOWN call sites and
rejects any added or changed caller. Fresh isolated v40k assembly and Python
syntax checks passed. This is a regression inventory, not permission to bind
the legacy DOWN path to production.

## Atomic MBSS checked-close retirement — local v40l, 2026-10-26

Source inspection found that `wr_iot_mbss_close_checked` consumed its
registry reference after checked virtual DOWN but never retired the radio
ticket. A subsequent close or reset would remain blocked by the old busy
operation despite a released module pin. The helper now retires the exact
ticket and consumes the matching reference under the same adapter lock.
An idempotent repeat recognizes the matching IDLE record, close stage 4 and
retired serial without releasing a second pin. If ticket retirement fails,
the CLOSING record, original ticket and pin remain for the retained owner.

Strict MinGW C11 tests passed both the local helper and fresh isolated v40l
generated headers. The fixture covers normal retry, idempotence, slot reuse
and injected ticket-retirement failure after checked DOWN. Fresh v40l
assembly also passed the exact four-caller legacy DOWN inventory gate.
This helper remains unbound to `ndo_stop`; it has no worker, MIPS compile,
image or device evidence. The physical close and callback release gates
remain open.

## Virtual-interface coverage gate updated for acquired failure — 2026-10-26

The v40l pre-CI check initially failed with `MBSS uncertain-open owner
handoff missing`: its previous rule expected one uncertain-open call and
three ticket wakeups. The newer acquired post-UP `-3` branch adds a distinct
fallback uncertain handoff and a fourth wakeup. Updated the checker to
require both branches, the acquired OWNED publication, radio failure receipt,
retained pin and exact wakeup count. It preserves the original v39 rule when
that branch is absent. The checker passed against both pinned v39 and fresh
v40l generated source; Python syntax and whitespace checks passed. This is
source coverage only, not MIPS or device evidence.

## MBSS retained recovery contract — local host gate, 2026-10-26

Added `tools/iot/mbss-close-recovery-owner.h` as a host-only ownership
contract. It separates an acquired vendor reference after failed `ndo_open`
(`CR_ENABLE` failure) from an in-progress checked close, and from an
uncertain count or family-close result. An acquired record may begin a new
checked BSS close only after the complete registry/vendor count matches;
an in-progress close may continue only with its original serial and stage.
Uncertain cases request reconciliation and have no automatic DOWN/replay
action. Every queued owner requires an already held netdev reference and an
adapter release fence. It releases those only after an exact checked close,
ticket retirement and a joined worker.

`check-mbss-close-recovery-owner.c` passed strict MinGW C11 compilation and
execution for missing pins, mismatched count/serial, acquired-open close,
completed checked close, join gating and uncertain non-replay. The optional
v40 CI path now runs this host fixture before target compilation; YAML parses
as one job. This is still a model: no kernel `work_struct`, `dev_hold`, PCI
release binding, MIPS compilation or router runtime proof was added.

## Selective source publication and current CI — 2026-10-26

Committed the v40 assembler, ownership and checked-close helpers, host
fixtures, coverage correction and optional CI gates as `eefbf12` on
`codex/wr1200js-service-webui`, then pushed that commit to PR #2. This
selective commit excluded unrelated dirty files, local candidate outputs and
router state. The remote branch matched parent `ba118ea` before push. PR
synchronization started ordinary firmware run `40257333149` and Band
Steering ABI run `40257333066`; both were queued/running at this check.
The ordinary build does not select the optional v40 overlay. Do not credit
this commit with a new isolated MIPS compile until that candidate run
finishes. No duplicate manual build was dispatched while the ordinary run
remained queued.

## CI continuation on `eefbf12` — 2026-10-26

The ordinary firmware run [#603](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40257333149)
completed successfully, including the WR1200JS build and ZIP jobs. The
Band Steering ABI run `40257333066` also completed successfully. Neither
run selected the isolated v40 candidate. After checking there was no
equivalent dispatch for this HEAD, one manual run
[`40260205702`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40260205702)
was started with `boards=wr1200js`, `run_candidate_checks=true` and
`iot_candidate_variant=v40`. Its WR1200JS job was still in progress at the
first check. Inspect its isolated candidate step and diagnostic artifact
before claiming target compilation; no router runtime result follows from CI.

## Isolated v40 target result — run `40260205702`

The manual run completed successfully on `eefbf12`. Its `Compile isolated
merged IoT MT7603 candidate` step succeeded, and the downloaded
`iot-merged-driver-probe` artifact contains a 5,206,540-byte
`mt76x3_ap.ko` with ELF32 little-endian MIPS32r2/o32 header and SHA-256
`cfaa715ebc3fabff6acd1ad55bf4603aedb674d201b3e3fd1fd0a38749363c51`.
The 58-path source manifest includes `wr-iot-mbss-close-checked.inc`;
`merged-capacity.json` reports a compiled main observer. The build log ends
with the module link and one section-mismatch warning, without a reported
compile error. The manifest's `target_compiled: false` is a **pre-build
source manifest** copied before `make`, so it must not be mistaken for a
post-build result. The successful CI step, resulting module and ELF header
are the target-compile evidence. `production_installed: false` remains true:
this isolated module is not the firmware module and has not run on WR1200JS.

The local workflow now writes a separate `target-compile-result.json` only
after the MIPS module, ELF header and unchanged kernel configuration are
checked. It records the variant, repository revision, module size/hash and
explicit false production/runtime fields, leaving the pre-build source
manifest unchanged. Parsed the one-job YAML and executed the extracted
post-build Python block against the downloaded v40 artifact: it reproduced
the 5,206,540-byte module and the SHA-256 above. This workflow edit is local
and has not yet been exercised by GitHub Actions.
Local `readelf -sW` of that module also found
`wr_iot_mbss_begin_close`, `wr_iot_mbss_close_checked` and
`wr_iot_virtual_down_checked`. The workflow now records the symbol table and
requires these three symbols for v40, guarding against compiling the wrong
candidate. Symbol presence does **not** prove that `MBSS_VirtualIF_Close`
calls the checked function: the generated v40 source still invokes legacy
`VIRTUAL_IF_DOWN` and returns success without using the checked result.
That binding requires a retained recovery worker and PCI release fence.
The new symbol gate was checked locally against the downloaded module only;
its CI result remains pending.

## MBSS close record identity across unlocked calls — local follow-up

The checked close helper previously re-read `r->last_token` after an unlocked
vendor DOWN, so a same-device, same-generation token replacement could pass
its record check and then retire the old ticket before consuming the new
reference. The helper now captures the token under the initial transition
lock and requires that exact token at each later stage. It also preflights
the reference's consume conditions before ticket retirement, then consumes
using the captured generation/token under the same lock. The strict C11
fixture passes an injected nonzero token replacement after DOWN and verifies
that the old ticket stays busy, the original module pin stays retained and
the record is not consumed. This is local source/host evidence only; it has
not been target-compiled or bound to `ndo_stop`.

## MBSS post-DOWN vendor count — local follow-up

The checked close path also lacked a post-DOWN count check. A stray legacy
writer could change `VirtualIfCnt` during the unlocked vendor call, after
the admission check, yet the close helper would retire the ticket and consume
the MBSS record. It now counts the other stable OWNED registry records under
the transition lock and requires the post-DOWN vendor count to equal that
number before retirement. Any uncertain/closing other record refuses this
completion. The C11 fixture models a successful decrement and an injected
extra count writer; the latter keeps the MBSS record, module pin and ticket
for reconciliation. Both local-helper and freshly generated v40n-header
fixtures passed. This follow-up is local and has not been MIPS-compiled.

## v40 target compile on `3041f7f` — 2026-10-26

The follow-up was committed and pushed as `3041f7fb09362b563cdf5185889d6d74964de259`.
The single optional v40 GitHub Actions run `40265901025` completed successfully
on that revision. Its `iot-merged-driver-probe` artifact contains the new
post-build `target-compile-result.json`, which records `target_compiled: true`,
`production_installed: false`, and `runtime_verified: false`. The isolated
MIPS module is 5,207,716 bytes and has SHA-256
`13ac9ac57450324e3763e24e8fe75fc3a479889db33aacd8f42f4705e774383f`;
the downloaded module hash matches the report. The artifact symbol table
contains `wr_iot_mbss_begin_close`, `wr_iot_mbss_close_checked`, and
`wr_iot_virtual_down_checked`. The earlier pending target-compile and symbol
gates passed for this revision. This does not establish production driver
binding, firmware image inclusion, or router behavior.

## v40 provenance gate target compile on `f708bcb` — 2026-10-26

Ordinary firmware run `40268551446` and ABI run `40268551314` passed on
`f708bcb5fc549ed72f36a29842d0f2f057632393`. The single optional v40
run `40330460110` also passed. Its downloaded `iot-merged-driver-probe`
artifact (`artifacts-609-v40/`) reports `target_compiled: true`,
`production_installed: false`, `runtime_verified: false`. The isolated
MIPS32 little-endian `mt76x3_ap.ko` is 5,207,896 bytes with SHA-256
`4088c6f3d2e5eeacddba2708eaee5c81159530558dba61518ca20ec0b13ece52`;
the downloaded file hash matches. The artifact's source manifest hashes for
`include/interface-reference.h` and
`include/wr-iot-netdev-registration.inc` match the freshly generated v40p
files, proving the provenance gate was in the compiled candidate. The CI
workflow also ran the strict host fixtures against those generated headers.
The run does not bind checked `ndo_stop`, install this module in the firmware,
or test the router.
