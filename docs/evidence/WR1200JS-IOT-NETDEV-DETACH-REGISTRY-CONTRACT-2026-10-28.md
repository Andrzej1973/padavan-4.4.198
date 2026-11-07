# IoT netdev detach registry contract — 2026-10-28

Added `wr_iot_registry_release_after_detach` to the isolated registry
contract. It requires the exact device/generation, published removal intent,
an idle checked-close reference, an untouched removal stage, and three
caller-proven facts: unregister completed, callbacks quiescent, and vendor
index unregistered. Only then does it record kernel/vendor completion and
clear the registry slot. A repeated call cannot release the same generation.

The strict host test compiled with Windows GCC using C11, `-Wall -Wextra
-Werror`, and passed. It rejects an owned reference, each missing proof,
wrong generation and a repeated release, then accepts one fully proven
transaction. `git diff --check` passed on the two source/test files.

Further source inspection found that `IDLE` alone can be insufficient for a
record with an acquired open: the auxiliary close wrappers in v24c still
discard the `VIRTUAL_IF_DOWN` result. The contract now additionally refuses
release when `last_token` exists, the open was not proven unmutated and
the family-specific checked-close terminal state is absent. Main and MBSS
reach stage 4 after successful reference consumption. The older isolated WDS
checked-close candidate reaches stage 2 on success; its stage 4 retains an
unfinished owner after failed radio completion. The host test accepts WDS
stage 2 and rejects WDS stage 4. AP-client and monitor acquired-open records
remain ineligible until their checked-close result is established. These
states alone do not make the legacy v24c auxiliary wrappers safe.

Follow-up comparison of v24c and the older isolated `aux-remove-close-v39`
found that v24c WDS `ndo_stop` still calls unchecked `VIRTUAL_IF_DOWN`, then
decrements the module pin and returns success unconditionally. The v39 WDS
path reserves an `AUX_CLOSE` ticket and checks DOWN, but its retry and
completion functions explicitly require a future retained recovery owner.
They are not wired to a live worker. Copying that wrapper into v24c would
therefore strand the pin/ticket on failure. The release contract is modeled
for the reviewed WDS stage-2 success, but no WDS production release binding
is justified yet. AP-client and monitor terminal stages remain unproven and
are rejected by the new host test. Main/MBSS stage 4 remains accepted.

The post-unregister contract is now split into two steps. When unregister
returns, `wr_iot_registry_after_unregister` records stage 1 against the exact
device/generation even if checked close is still `CLOSING`. A later owner can
call `wr_iot_registry_finish_after_unregister` only after `IDLE`, the
family-specific checked-close terminal state, callback quiescence and vendor
unregistration are independently proved. Failed proofs leave stage 1 and
the original identity intact, so a caller must continue instead of repeating
unregister. The host fixture covers pending close, wrong generation, missing
proofs, retry and one-shot release. No production owner invokes these helpers.

The combined `release_after_detach` entry point now records stage 1 as soon
as unregister completion is proved, before checking close or later proofs.
If close/callback/vendor completion is missing, the record remains at stage
1. A later invocation may finish that same generation with no second
unregister. The host fixture verifies this combined-path recovery as well.

The exact pinned Padavan source in the local bare Git snapshot at
`c25283e915a2a00a763774dd255b14aff997285e` was inspected. Blob
`221c420741a32e6c8fcc177d93a07200e041569f` (`net/core/dev.c`) shows
`unregister_netdevice_queue` adding the device to the todo list and
`netdev_run_todo` setting `NETREG_UNREGISTERED`, waiting for all netdev
references and completing unregister events. Blob
`d52b633164c917ed4c1f775091d87be75cee1f1f` (`net/core/rtnetlink.c`)
shows `rtnl_unlock` calling `netdev_run_todo`. The repository IMQ patch's
`net/core/dev.c` hunks do not modify these functions; no overlay patch to
`rtnetlink.c` was found. This supports a kernel unregister completion proof
after `RtmpOSNetDevProtect(0)` for the pinned base plus inspected overlay.
It does not prove a successful vendor checked close or all driver callbacks.

This helper is not yet called by the four vendor child remove loops. Those
loops also require a retry/finalization rule if a post-unregister proof
fails; simply returning and calling unregister again is unsafe. A final
assembled kernel source/image comparison and target MIPS compile have not
been performed, nor has a router test.

Exact v24c MBSS binding point: `ap/ap_mbss.c:239-243` calls
`RtmpOSNetDevProtect(1)`, `RtmpOSNetDevDetach`, then
`RtmpOSNetDevProtect(0)` before `rtmp_wdev_idx_unreg` and netdev free.
The pinned kernel's `rtnl_unlock` runs `netdev_run_todo`; stage 1 can be
recorded only after that protect-off call returns. A failure in any later
proof must not reenter the loop at `wdev_bcn_buf_deinit` or `Detach` because
beacon storage and kernel unregister have already changed state. The present
loop has no stage-1 continuation branch and always proceeds to free. The
next production candidate therefore needs a per-netdev resume path and
ownership of the still-live netdev; merely inserting the stage-1 call after
protect-off would not make it safe. AP-client, WDS and monitor have analogous
detach/free sequences and unverified checked-close outcomes.

Added host-only `mbss-remove-resume.h` to select the next MBSS teardown
operation from the exact registry and beacon-retirement stages. It selects
beacon work only before beacon completion, unregister only before registry
stage 1, and then bookkeeping/vendor/release without returning to destructive
earlier stages. Vendor and release steps wait for `IDLE` plus the MBSS
checked-close terminal state. `check-mbss-remove-resume.c` compiled with
strict C11 GCC and passed, including a close still pending after unregister.
This selector is not copied into or called by v24c; it does not hold a netdev
reference or establish callback quiescence.
The selector additionally rejects a non-MBSS family or stale generation and
will not choose beacon teardown or unregister while the reference is closing
or reserved. A strict host fixture verified these refusal cases. It remains
a host contract, not evidence of a target-driver binding.

Pinned-kernel lifetime correction: `netdev_run_todo` calls
`netdev_wait_allrefs` during `rtnl_unlock`. A persistent `dev_hold` across
`RtmpOSNetDevProtect(0)` can deadlock unregister. The continuation must own
the allocation through the driver's lifecycle and defer `RtmpOSNetDevFree`
until proofs finish, while dropping any temporary kernel netdev reference
before protect-off. No such production owner is bound.

The pinned source also confirms the allocation can remain available after
unregister completion if the driver has not called `free_netdev`: in
`net/core/dev.c`, `free_netdev` requires `NETREG_UNREGISTERED`, changes it to
`NETREG_RELEASED`, then drops the device reference; `net/core/net-sysfs.c`
frees the allocation in `netdev_release` when the final device kobject
reference is gone. The candidate's `RtmpOSNetDevFree` delegates to
`free_netdev`. Thus the deferred path can postpone that call after
protect-off, provided it owns the driver lifecycle and has prevented other
free paths; a kernel `dev_hold` must still be dropped before protect-off.
This is source evidence for the lifetime mechanism, not proof that the
current candidate has wired the owner or its callbacks correctly.

The host MBSS resume selector now requires a caller-proven callback
quiescence result before choosing vendor teardown or final release. Its
fixture rejects both steps when that proof is false and passes with it true.
The selector cannot itself establish the proof; production binding remains
dependent on an actual callback/worker drain.

Candidate callback-proof audit: `wr_iot_wait_tx_idle` observes only
`wr_iot_transition.active_tx` and explicitly documents that it does not
drain DMA or hardware queues. `wr_iot_wait_registration_idle` observes only
registration in flight. The PCI path joins `wr_iot_main_recovery_work` and
its delayed reaper, but the MBSS remove loop has no corresponding per-BSS
worker/callback receipt. Those existing waits therefore cannot be passed as
the selector's `callbacks_quiescent` proof. Kernel `netdev_run_todo` drains
netdev references and RCU callbacks for unregister; it does not by itself
prove that all vendor beacon/DMA users have stopped. Production binding must
identify and join those vendor producers under the same removal fence.

Composition follow-up: v24c lacked the reviewed beacon/TIM producer gate.
The preparer matched LF-only anchors while v24c's `ap/ap_connect.c` uses
CRLF. It now accepts exactly one matching anchor in either line-ending form
without normalizing the whole file. A new isolated v25b candidate was
generated from v24c at
`.iot-local-check/mt7603-pci-recovery-drain-v25b-beacon-20261028`.
Its manifest lists seven modified/added files and reports
`producer_gate_bound=true`, `target_compiled=false`, and
`production_installed=false`. The strict host beacon-gate fixture and Python
syntax check passed. A first failed attempt left a partial v25 scratch
directory; deletion was rejected by the environment's policy. Use only the
successful v25b candidate, never the partial v25 directory. This is source
composition, not target compilation or full callback/DMA proof.
The v25b source check finds one wrapped `APUpdateBeaconFrame` and one
wrapped `APMakeBssTimFrame`; each admits a producer before the inner
function and ends it after return. MBSS close/abort revoke and drain, and
MBSS remove checks the gate before beacon-buffer deinit. The kernel-adapter
host fixture also passed (`atomic refusal`, revoke, producer drain, remove
gate). This covers packet-pointer preparation but does not by itself retire
late DMA completion or TxS reports; the v25b manifest still has no target
compile or PCI release proof.

## v25b extracted DMA and TxS evidence

On 2026-10-28, the existing extractors were applied to the successful
isolated v25b source. Both generated C fixtures compiled with
`gcc -std=c11 -Wall -Wextra -Werror` and ran. The beacon DMA fixture passed
owner, unknown-owner, ring-mismatch and lock-release checks. The TxS
ledger/parser fixture produced a **negative witness**: after a completed
reservation's PID was reused for another BSS, a modeled duplicate old TxS
report invoked the new BSS handler and retired its slot. The fixture reads
the candidate's actual `AddTxSStatus`, `RemoveTxSStatus`, claim completion,
outstanding query and parser functions. Its modeled duplicate is not proof
that WR1200JS hardware emits duplicates.

`TXS_CLAIMED` prevents reuse while the parser owns a slot, but completion
sets the slot to `TXS_UNUSED`. The report is dispatched by its 8-bit PID;
the software `ReservationGeneration` is absent from the report. The old
report and the new report are indistinguishable at that parser boundary.
Neither the producer gate nor the DMA snapshot closes this gap. The
selective-BSS-retirement and late-report flags must remain false. Before
production binding, verify an exact hardware-returned report identity or
prove a barrier that drains beacon DMA, hardware TxS, received report
batches and callbacks without disturbing main/guest BSS. A timeout or a
software-only generation cannot substitute for either proof. The detailed
options and source map are in `WR1200JS-IOT-TXS-RETIREMENT-OPTIONS-2026-10-24.md`.

Follow-up source check: `ap/ap_nps.c` sets `NSeq=TRUE` for the TIM/beacon
path. The candidate's `mac/mt_mac.c::write_tmac_info` zeroes the descriptor
and writes no `txd_3.sn` or `txd_3.sn_vld`; its printed SN is diagnostic
only. `tx_rx/txs.c::BcnTxSHandler` records `txs_d4->sn` only under `DBG`,
after `ParseTxSPacket` has already claimed a slot by PID and selected its
BSS callback. That history cannot reject a stale report before it is
misattributed. A sequence-based solution therefore needs a proven
submission-side expected value and a comparison *before* slot claim; the
existing `TXS_SN` history does not provide either. The isolated v25b copy
does not contain the full RX file, so this follow-up is bounded to those
present candidate functions and the separate pinned RX source audit above.

The host MBSS removal selector was tightened accordingly: after kernel
unregister, vendor teardown and final release now require both callback
quiescence and a distinct `reports_drained` proof. Its strict C11 fixture
rejects each step with `reports_drained=0` and permits it with a hypothetical
proved value. The current driver has no mechanism supplying that value.
`WrBeaconTxSOutstanding == 0` cannot be used for it. This change prevents
the host contract from treating software ledger emptiness as a hardware
barrier; it does not complete a production close or justify flashing.

The registry finalizer previously remained an alternate release path after
the selector was tightened. It now takes `reports_drained` as a separate
caller proof for an MBSS that acquired an open reference, both in direct
`release_after_detach` and resumed `finish_after_unregister`. False retains
stage 1 and the exact device/generation; true permits completion when all
other checks pass. A WDS removal does not require this MBSS-specific proof.
Both host fixtures compile and pass under strict C11/GCC. The raw registry
release primitive is still lower level and must not be wired directly to
production MBSS teardown. No actual hardware/RX drain has been established.

Local target-compile availability check on 2026-10-28: this Windows session
has no `mipsel-linux-gnu-gcc`, `mips-linux-gnu-gcc`, Docker or Podman command.
`wsl.exe` exists, but `wsl.exe --status` returned exit code 50 without a
usable distribution/status. The existing band-steering package compiler
script expects an already built Linux source tree and cross compiler; it is
not a driver source compiler. Thus v25b has not received a local MIPS driver
compile. A CI target compile must use a pinned source/toolchain and report
its exact candidate hashes; it still would not prove runtime TxS behavior.

The v25b manifest names only its seven changed/added files. A new source
checker compared the entire v24c 69-file manifest with the actual parent,
verified every declared v25b delta hash, and checked that the complete v25b
tree has exactly the expected 71 files with no unrecorded changes. It passed
locally. This is full local content verification, not a GitHub-reproducible
build: the v24c parent and several earlier composition scripts are still
untracked local inputs. They must be deliberately packaged and reviewed
before a pinned CI target compile can consume this exact candidate.

Git-index provenance check: the v22→v23b→v24c→v25b chain uses
`prepare-main-recovery-rtnl-candidate.py`,
`prepare-main-recovery-reaper-candidate.py`,
`prepare-pci-recovery-drain-candidate.py` and
`prepare-beacon-producer-candidate.py`. In the current worktree only the
last preparer is tracked; the first three and `pci-recovery-drain.inc` exist
locally but are untracked. The complete v25b tree is 71 files, about 2.98 MB
uncompressed. Copying that tree into Git now would add a separate unfinished
driver snapshot, while the earlier chain still needs provenance review.
The next CI package must either deliberately include the exact candidate
with its upstream license/revision and full hash manifest, or make every
preparation dependency available from tracked files and regenerate it from
the pinned source. No CI or firmware job currently consumes v25b.
