## 2026-11-04 Sol: coherent isolated close-order integration verified on host

The local AP/data-lane work is now bound in the isolated peer82 close recipe.
New final manifest-checked layer performs early checked MAC RX stop, joins data
callbacks while MCU RX1/command-TX scheduling remains admitted, runs AP command
cleanup with destructive resource tails deferred, sends owned OFF, then joins
all network callbacks and releases IRQ before AP/channel/measurement resources.
Data gates preserve the current IRQ-save RTMP_INT_LOCK family, initialization
and release fences. Default LOAD_FW_ONE_TIME refuses before early mutation.
A terminal partial-cleanup stage6 prevents replay of irreversible tail frees;
CLOSE serial/epoch receipt prevents duplicate AP release. AP release claims
MCU message construction and nettask reinitialization fences, rather than
trusting zero-count snapshots; an initialization race retains all AP resources.
Ordinary callbacks remain unbound; configuration/router unchanged. ACK epoch,
late-report identity, MMIO/device completion and uncertain RECONCILE/reopen
still require evidence. Do not call this production or runtime accepted.

Fresh complete current source chain was generated. Its preserved final input
/tmp/wr-close-ack-order-input-a1f7d6d is 13898319 bytes plus manifest, retained
for unfinished target/debug work so the large generation need not be repeated.
All intermediate phase trees were removed. Temporary copies/fixtures removed;
phase-only bytecode cleanup also checked. WSL scratch reclamation does not
imply a smaller Windows VHD allocation. Keep owner references and old inputs.
Host ASan/UBSan passed actual installed close ordering/replay refusal, early-RX
and OFF MMIO fault fixtures in reload and one-time modes, AP feature guards,
data/MCU scheduling and poison, final AP admission and init race, owned OFF,
all four MCU sequence suites and combined MBSS submit/work/stop-join. Complete
installed inventory matched the updated manifest; duplicate install refused.
No local target compilation. Candidate target runs remain required.

Standard743/ABI658 succeeded on a1f7d6d. Required optional744/41868468440 was
dispatched once for that exact SHA and is building firmware; it does NOT cover
this newer close-order package. Prior optional742/41858780303 now confirmed
success; its compact reload reports are already committed. Publish this whole
coherent package once; verify new standard then queue its exact-SHA optional.


# AP resource split: local unfinished integration

HEAD a1f7d6d; no new commit/push. New local prepare-ap-resource-split.py and
check-ap-resource-split.py separate conditional FT/DMS, multicast and WDS lock
release from the existing AP software command path. Legacy TRUE wrappers keep
old behavior; candidate FALSE defers resource tails. The raw destructor helper
has NO caller or acceptance checks yet and is deliberately not wired into CI.
It must not be used until integrated single-execution, RX/IRQ retirement and
CLOSE receipt guards are implemented. No production source generated/installed.
Exact prepared source fixtures with feature guards enabled/disabled passed
ASan/UBSan; legacy wrappers and duplicate-transformation refusal checked.
Temporary prepared source/tests removed; no large local build or retained scratch.

Correction to prior audit: raw vendor APShutdown frees MacTabLock, but the
CURRENT candidate already retains it. Updated the uncommitted audit accordingly;
new preparer explicitly refuses a MacTabLock free and does not reintroduce it.
Current remaining resource tails include WdsTabLock and FT/DMS/multicast.
Next complete data-vs-MCU RX scheduling/joins and staged cleanup receipts before
binding this local split into a coherent close-order package. Do not push these
unbound pieces individually. CI 743/ABI 658 still queued; no duplicate dispatch.
No router access; owner references and unfinished inputs preserved.

## 2026-11-04 Sol: local data/MCU scheduler separation

Uncommitted coherent close-order package extended with nettask-lane-owner.h,
nettask-data-drain.inc, prepare-nettask-data-lane.py and extracted-code checker.
Prepared overlay keeps global scheduling lease for every call, adds data
lease for non-MCU calls, and retains MT7603 RX1/command-TX scheduling while
data gate is closed. Data-only exit copies actual guarded kill inventory,
excluding RX1/hcca; global exit blocks both owners and joins all callbacks.
Data join is NOT DMA retirement or AP-resource release permission. Explicit
join-in-progress fencing, two-owner init/open gates and sticky poison preserve
failure retention. No existing lower-layer generators or CI bindings changed.
ASan/UBSan on actual prepared scheduler/exits passed in-flight data admission
refusal, late callback rearm, MCU scheduling after data join, global join,
join collision, init fence and overflow poison rejection. OS/tasklet execution
and hardware remain mocked. Prepared against preserved source, not yet replayed
through full newest chain or target compiled. Temporary overlays/binaries removed.
AP resource split remains unbound/local. Next integrate early MAC RX stop,
data join, command/AP stop, owned OFF with MCU RX1 alive, then global RX/IRQ
retirement and single-execution AP release receipts. Retain partial-stage
ownership on every failure; do not use reordered calls alone as safety proof.
No commit/push until coherent integration verified. CI 743 still queued; no
duplicate builds, router access, source-input or owner-reference cleanup.
