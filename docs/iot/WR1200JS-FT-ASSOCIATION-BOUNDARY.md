# Active FT association boundary — 2026-11-19

Pinned SDK c25283e; optional1418 actual ap_cfg/ap_wpa/cmm_wpa macros have
DOT11R_FT_SUPPORT=true. This source review identifies an unclosed path; it does
not prove that a physical FT client triggered it or that every FT TU is active.

common/ft.c:FT_FtAction (line1008) is a separate MLME callback, outside the
three existing native auth/assoc wrappers. It derives apidx from frame Addr1.
For terminating FT_ACTION_BT_REQ it looks up Addr2 by MAC alone, optionally
inserts a station through MacTableInsertEntry, calls FT_AuthReqHandler, and on
success changes MdIeInfo/AuthState/Sst. Existing insertion arbitration covers
only allocation; a preexisting peer can reach native mutation without that call.
FT_AuthReqHandler derives its BSS from the entry, so a MAC-only lookup returning
another BSS is not corrected by the earlier frame apidx classification.

The confirmation branch takes MacTab.Content[Elem->Wcid] directly before
FT_AuthConfirmHandler; it needs explicit entry/BSS/generation provenance review.
Its current index check uses > BssidNum. Wrapping only a receiver-BSS predicate
cannot establish correctness of a borrowed WCID from another BSS.

Required next implementation: inspect actual FT callback dispatch and TU flags;
validate complete action header length before parsing; match requested BSS and
resolved peer; admit the entire native mutation under the same ra2 association
arbiter before the first mutable operation; advance association generation at
the correct new FT association boundary, preserving native crypto/timer behavior.
Hold no spinlock across native operations. Include FT daemon key-response and
other callers of FT_AuthReqHandler/ConfirmHandler in the coverage inventory.
Do not claim complete GTK-versus-association exclusion until this active path is
bound and target/host checked. Do not disable FT globally to close the report.

## Prepared outer boundary

common/action.c:93 registers FT_FtAction for FT_CATEGORY_BSS_TRANSITION.
Both FT_AuthReqHandler and FT_AuthConfirmHandler are also called from the
already wrapped ap_auth.c callbacks. The separate action callback therefore
requires its own admission. ra2-ft-mutation-composition.py prepares its outer
wrapper using the same exact native wrapper generator; production SITES is
unchanged. check-ra2-ft-mutation-composition.py verifies byte-for-byte native
body preservation, duplicate refusal and generated wrapper execution with a
native early-return actor, in target-feature and native pass-through modes.
ASan/UBSan host checks pass. This wrapper is not producer-installed: complete
action payload length, selected-entry BSS/provenance and generation advancement
must still be bound before activation. The check does not execute FT crypto.

## Action payload length defect and prepared bounds

The actual packed FT_ACTION in include/dot11r_ft.h has14 bytes before Oct.
FT_FtAction twice passes FtActLen-sizeof(PFT_ACTION) to FT_ReqActionParse;
PFT_ACTION is a pointer, so this subtracts4 on MIPS instead of14, overstating
the remaining IE bytes by10. Before using the result, validate outer MsgLen
against buffer capacity, the complete MAC/action headers and UINT16 range.
ft-action-bounds.h prepares bounded subtraction without narrowing or overflow;
check-ft-action-bounds.py extracts the actual vendor layout and tests all
outer lengths0–256, truncation, empty remainder, capacity overflow, ULONG_MAX
and UINT16 boundaries under ASan/UBSan. Header decoding uses latin-1 because
vendor comments contain non-UTF8 bytes; the C declaration is unchanged.
The helper is uninstalled. FT_ReqActionParse itself reads eid_ptr->Len in its
loop condition before checking that two IE-header bytes remain; outer bounds
alone do not correct that parser. Full IE validation and FT ownership are still
required before activating the complete prepared FT path.

## Prepared bounded IE framing primitive

ft-ie-span.h checks two header bytes before reading length, subtracts header
space before comparing the body length, and advances only by a validated span.
It supports outer IEs and nested FT subelements. check-ft-ie-span.c exhausts
all256 length-byte values for remaining sizes0–257 using exact-size ASan
allocations, plus concatenated/empty/truncated lists and null arguments.
The helper does not validate MDIE's3-byte body, FTIE fixed/nonces/subelement
semantics or OUI minimum lengths. It is not installed in the native parser;
FT_FillFtIeInfo's nested loop and its destination field capacities still need
validation before complete action admission is enabled.

## Prepared nested FTIE copy bounds

FT_FillFtIeInfo reads2+16+32+32 fixed bytes before optional subelements. Its
nested loop reads the subelement header with only RemainLen>0, and GTK copies
Len bytes without comparing the destination capacity. ft-subelement-bounds.h
prepares full-list framing plus R0/R1/GTK destination bounds, taking the fixed
header offset and capacities from the eventual caller rather than assuming
target structure sizes. It rejects zero-length subelements because the native
parser otherwise stops before validating the remaining list. Host tests exhaust
all256 lengths for R0/R1/GTK/unknown IDs, exact allocations and one-byte
truncations under ASan/UBSan. The test's32-byte GTK capacity is an injected test
parameter, not a claim about the SDK destination. Production binding must use
sizeof(actual GtkSubIE), offsetof(FT_FTIE,Option), and existing vendor IDs.
These helpers are still uninstalled; complete FT action/native parser execution
and target verification remain required.

## Prepared complete request-IE admission

ft-request-ie-admission.h composes span/MDIE/FTIE nested bounds and native OUI
read minimums. It derives GtkSubIE and RSN_IE capacity from caller vendor types,
FTIE fixed bytes from offsetof, and rejects RSN output lengths exceeding UCHAR.
The host fixture exhausts256 IDs ×256 body lengths with exact allocations and
one-byte truncation, plus a64-byte GTK nested element and overflow refusal.
ASan/UBSan passes. This fixture uses explicit boundary layouts, not full vendor
headers; target type compatibility and whole native-parser execution remain
unverified. The header is not producer-installed. Empty lists pass framing but
are not authentication approval; native required-IE checks must still reject
missing mandatory data. The minimum5-byte RSN/WPA policy is specifically for
the native parser's unconditional OUI reads; it is not a new RSN protocol claim.

## Prepared native parser bounds composition

ft-parser-bounds-composition.py now prepares concrete common/ft.c changes:
validate complete action lengths/IE framing before allocation, pass actual
IE remainder instead of sizeof(pointer), validate the whole list before native
field output, iterate with a remaining-byte counter and bound RIC view to the
actual input remainder. Changed anchors and duplicate installation refuse.
The producer still does not install this composition.

check-ft-native-parser.py compiles/executes the actual composed parser body
with explicit MDIE/FTIE fill actors and boundary layouts, not the complete SDK
fill routines. ASan/UBSan checks exact-size buffers0–257, full-list malformed
refusal before MDIE output, native RIC length/copy and RSN OUI copy. The native
RIC switch intentionally falls through to descriptor copying; this inherited
warning alone is suppressed. Complete native fill-function execution, actual
vendor header compilation, callback BSS/provenance/generation arbitration and
forwarded-action semantics must still be verified before candidate activation.

## Actual vendor fill routines and type declarations exercised

check-ft-vendor-fill-parser.py extracts the real FT_CAP_AND_POLICY, FT_MDIE,
FT_MIC_CTR_FIELD, FT_FTIE, FT_OPTION_FIELD and FT_*_INFO declarations from SDK
headers, and executes unchanged FT_FillMdIeInfo/FT_FillFtIeInfo with the composed
parser under ASan/UBSan. Byte-order/MMIO-independent SDK macros are explicit
boundary definitions. It verifies MDIE3 bytes, FTIE Option offset82 and GTK
capacity64, all256 FTIE lengths, actual64-byte nested GTK copy and overflow
refusal, plus MDID copying. Host PASS supersedes the prior fill-actor-only
coverage for these cases. Full FT callback authentication/crypto, all optional
header combinations, target linking and physical runtime remain unverified.

## Forwarding scope correction before activation

The first prepared bounds composer applied request-IE validation before the FT
Action switch, which could reject native forwarded response payloads containing
status bytes. It now applies outer complete-header admission globally but checks
request IEs only in terminating BT_REQ/BT_CONFIRM branches, before MAC lookup
or WCID borrowing. Native forwarding calls remain byte-identical. The new
check-ft-parser-composition.py verifies this ordering, both parser lengths and
duplicate refusal. Native vendor-fill parser tests still pass. Full action
execution and target validation remain pending; the composer stays uninstalled.

## Optional MIPS translation-unit probe prepared

check-ft-bounds-target-tu.py locates the actual single ft.o Kbuild command,
unwraps only approved system ccache, checks exact compiler/source identity,
and compiles a temporary transformed ft.c with copied bounds headers. It
requires effective AP/FT/MT7603/MT_MAC/PCI macros and ELF32 LE MIPS output,
records source/prepared/object hashes, then verifies original source unchanged.
It neither replaces ft.o nor relinks/installs the driver. The peer82 optional
pipeline now requests this separate probe after the original module build.
Local checks cover Python/shell syntax and CLI only; first actual target result
is pending. Native FT association arbitration is still uninstalled/unverified.

## Combined temporary FT TU probe

The temporary target probe now composes the balanced outer FT mutation wrapper
on the bounded parser and includes the existing Linux mutation admission header
under the MT7603/MT_MAC/PCI guard. It therefore checks callback/arbiter type
compatibility in addition to parser types, without replacing the built module.
Combined source composition preserves the bounded native body and has exactly
one enter/leave seam; local source/CLI syntax checks pass. BSS/provenance and
original queued-association identity remain runtime integration requirements,
so a successful future TU build will not authorize installation by itself.

## Prepared allocation/index refusal before handler execution

The action composition now adds if(!pEntry)goto out after the native optional
MacTableInsertEntry, before request parsing/FT_AuthReqHandler. Allocation or
existing insertion-admission refusal must not become a null-entry handler call.
The confirmation branch's func_tb_idx > BssidNum test becomes >= BssidNum;
BssidNum is a count and index==count is outside the configured BSS range.
Source-order regression checks and vendor-fill parser tests pass. These checks
are still in the uninstalled FT composition; no full action or target/runtime
acceptance is claimed by the source assertions.

## Exact-buffer native parser regression — 2026-11-19

The real vendor-fill host harness now checks every truncated length before a
complete MDIE (3-byte body) and FTIE (82-byte fixed body), with exact heap
allocations. It also checks zero body lengths and declared length255 with only
the two-byte header available. Refusal must leave the complete FT_INFO zeroed,
not partially populated. Existing valid MDIE/FTIE and GTK64 cases still pass;
ASan/UBSan report no boundary violations. The five FT Python host checks pass.

The supplied Nim run is separate evidence: its intentionally unchecked branch
accepted oversized input, so its negative-control assertion failed and returned
status1. That does not execute or validate the vendor C parser.

Standard1421/1422/1423 and their ABI checks completed successfully. Optional1424
(run44548591244) was dispatched for exact published revision ead99729 and was
observed in progress. It predates the allocation/index refusal and expanded
exact-buffer tests. No temporary FT TU result, installed FT fix, whole callback
association ownership, or router runtime acceptance is inferred from these host
results. The producer still leaves this FT composition uninstalled.

## Optional1424 temporary FT TU independently read — 2026-11-19

GitHub API confirms all four jobs of run44548591244 completed successfully,
including isolated merged IoT compilation. Artifact14543192706 belongs to
exact ead99729cabb692c5ecdec7e7f3216318489157e; downloaded48652581-byte archive
SHA25674e485ac7e600b11599af68ef0cdb4265a47dbb721c760ab55c176cb24afdd47
matches API digest; all ZIP members pass CRC. Read ft-bounds-target-tu.json:
status passed, all AP/FT/MT7603/MT_MAC/PCI macros true, object105284 bytes,
module_installed false, runtime_verified false. Exact report retained in
`docs/evidence/WR1200JS-OPTIONAL1424-FT-TU-2026-11-19.json`.
Owned downloaded archive removed after verification; no full extraction.
This covers the temporary composed TU at ead99729, not later allocation/index
changes or current eda5fff. No producer installation or device acceptance.

Next remains FT association-generation/BSS provenance: wr_assoc_capture and
wr_assoc_event_current protect WPA_STATE_MACHINE only. Native FT_FtAction
request resolves Addr2 by MAC alone; confirmation borrows Elem->Wcid. Outer
receiver classification does not validate the selected peer's BSS or original
queued generation. Keep prepared composers uninstalled until producer/event
identity, peer lifetime and association advancement are bound and tested.
No duplicate CI, driver edits, router actions, commit or push during acceptance.


## Prepared RRB lookup bound to active destination BSS — 2026-11-19

At owner request, ft-parser-bounds-composition.py now changes FT_RrbHandler:
derive apidx from the Ethernet destination (the same destination used for the
synthetic MLME receiver), scan under MacTabLock, accept only IS_ENTRY_CLIENT,
SST_ASSOC, exact MAC, slot WCID, func_tb_idx and embedded wdev for that BSS.
No match returns before allocation/frame construction/REPORT_MGMT_FRAME_TO_MLME;
RESERVED_WCID fallback is removed. Minimum complete packet headers and declared
RRB action remainder are checked before field reads. No peer pointer is used
after the lock; the selected WCID remains a snapshot, not a generation lease.
This stricter rule intentionally refuses a target with no associated client.

Existing source composition test executes the generated pre-allocation C
selection with ASan/UBSan: earlier same-MAC wrong BSS/inactive slot skipped;
wrong state/wdev/BSS/WCID/MAC, absent client, invalid destination and truncated
lengths refused. Source ordering verifies refusal precedes MLME enqueue.
Real vendor-fill parser regression also PASS. This is host selection coverage,
not full native RRB/frame/MLME execution, target compilation or device proof.
Original supplied slot_lookup_check.nim rerun unchanged: legacy PASS=false,
strict PASS=true, stale-generation PASS=true; process exits0 because the
helper prints booleans without failure exit logic. It does not execute C.

Composer remains uninstalled; original queued generation/lifetime binding and
FT action selected-entry BSS checks remain open before activation. Previous
optional1424 TU report predates this change and does not cover it. No router
changes, heavy local builds, commit or push in this change.


## RRB full callback host regression and native FT state correction — 2026-11-19

Expanded the existing FT composition check to compile and execute the entire
composed FT_RrbHandler body with explicit allocation/framing/MLME queue actors,
under ASan/UBSan. It observes queue suppression before allocation for wrong BSS,
inactive/non-client and mismatched wdev; valid WCID delivery, allocation failure,
exact heap input truncations and exact output capacity/one-byte excess refusal.
The original MAC-only callback fails the same expected-WCID assertion. Actors
are boundary replacements, not execution of the native MLME queue or RF path.
MlmeAllocateMemory in both SDK rt_drv.h/rt_linux.h allocates MGMT_DMA_BUFFER_SIZE;
composer now checks that output capacity before MakeOutgoingFrame.

Corrected the earlier SST_ASSOC-only predicate: successful native FT_FtAction
request explicitly sets Sst=SST_AUTH before confirmation. Valid active client
states are now SST_AUTH or SST_ASSOC with exact MAC/BSS/wdev/WCID; the fixture
executes both. SST_NOT_AUTH and non-client entries remain refused. Thus earlier
status text requiring an associated client only is superseded by this block.
This preserves the native request/confirmation state sequence at this boundary.

Host report: docs/evidence/WR1200JS-FT-RRB-CONTEXT-HOST-2026-11-19.json.
No producer installation/target compile/device acceptance for this local change.
Next: bind FT_FtAction's selected entry to receiver BSS and original queued
generation, with native peer lifetime arbitration, before any activation.

## Prepared FT native action BSS context checked — 2026-11-19

The uninstalled FT bounds composer now also scopes FT_FtAction request lookup
under MacTabLock to a live ENTRY_CLIENT with exact MAC, slot WCID, receiver
apidx and embedded wdev. Action StaMac must match frame Addr2 before lookup/
insertion. A failed insertion returns without handler execution. Native initial
SST_NOT_AUTH insertion is preserved; request success still sets SST_AUTH.
Confirmation requires a nonreserved matching WCID, live client, exact receiver
BSS/wdev/MAC/StaMac and SST_AUTH or SST_ASSOC before FT_AuthConfirmHandler.
Native forwarding branches remain unchanged. Negative apidx is now refused.

Existing composition regression executes the entire composed FT_FtAction with
explicit IE-parser, crypto/handler, allocation and forwarding actors. Same-MAC
other-BSS slot before correct slot, request -> SST_AUTH -> confirm, wrong WCID/
BSS/wdev/MAC/state, insertion failure/success, short outer headers, forwarding
and balanced frees PASS under ASan/UBSan. Original callback fails the same
BSS/state assertions. Independent real vendor-fill parser regression also PASS.
Native callback control flow is exercised, not actual crypto/MLME concurrency.
Report: docs/evidence/WR1200JS-FT-ACTION-CONTEXT-HOST-2026-11-19.json.

Compiler commands resolving local headers now pass -I<script_dir>, including
the original-callback regression build. No FT producer activation, target build
or device acceptance is claimed. WCID/generation capture before enqueue,
peer lease during native mutation and correct FT generation advancement remain
required. Current point-in-time BSS checks do not establish those properties.

## Existing-peer FT generation/lease primitive prepared locally — 2026-11-19

New uninstalled ft-peer-generation.h captures a value stamp under caller-owned
MacTabLock: nonzero generation, exact WCID/MAC/BSS/wdev and AUTH/ASSOC state.
Later validation uses that captured generation, never rebinds it to a reused
slot. Synchronous scope uses existing wr_assoc_event_users plus peer-table
transaction; reset is excluded until balanced release. Foreign/double leave is
refused. If identity/users drift during the scope, owner is poisoned and the
uncertain reference retained instead of releasing another peer's ownership.
Caller must separately hold adapter/wdev lifetime and association-vs-key/control
admission; helpers acquire no locks and execute no native operations. The stamped
existing-peer FT candidate now advances and republishes generation after native
FT auth succeeds while the lease is held, then releases at callback exit. The
pending first-peer scope still needs transfer through the callback; ordinary RX
remains uncovered.

New check-ft-peer-generation.c runs the actual primitive and existing table
owner under ASan/UBSan. Existing full FT callback regression also runs it.
Immutable-generation, wrong context/state, competing/reset scope, foreign/double
leave and uncertain release cases PASS; report FT-PEER-GENERATION-HOST JSON.
Temporary MIPS TU probe now includes/copies this header to typecheck against
actual candidate fields on its NEXT revision. No such target result exists yet.
These files remain local/uncommitted for the next coherent generation package.

Still required: pending first-peer ticket and lease transfer through the callback;
ordinary RX identity and first-peer behavior; complete callback-exit arbitration;
IAPP daemon response identity/completion; target compilation of the composed
paired TUs and lifecycle; and full adapter/wdev/control-owner integration.
Do not replace native enqueue with an unverified custom queue implementation.
No producer installation or physical proof. Current ABI958, standard1428 and
prior2ff optional1427 freshly in_progress; no restarts/duplicates this turn.

## Explicit FT producer snapshot enqueue prepared locally — 2026-11-19

ft-enqueue-generation-composition.py creates a separately named native
MlmeEnqueueForRecv variant from the actual association-stamped SDK candidate.
It accepts const wr_ft_peer_stamp explicitly and copies original generation,
WCID and MAC into native queue metadata instead of calling wr_assoc_capture.
Ordinary receive enqueue/callers remain byte-identical. Receiver BSS/MAC/WCID
and complete outer action header checked before native classification/queue.
Native queue allocation, metadata, dispatch and feature guards are preserved.
The extracted explicit prototype compiles against the complete function.

check-ft-enqueue-generation.py executes the entire cloned native function with
host queue/classifier actors under ASan/UBSan, in default/EAP/SNR variants.
Replacing the live slot generation immediately before queue locking still
queues the original stamp; later current-generation validation rejects it.
Fresh capture queues new generation; wrong context, occupied/full queue and
exact-allocation short frames refuse. Duplicate composer application refuses.
Durable FT-EXPLICIT-ENQUEUE-HOST report records checks and source hashes.

This is uninstalled preparation, not an alternative custom queue or completed
FT identity binding. RRB producer still must capture/pass its original value;
consumer must restore/validate it before native mutation and retain the peer
lease. Plain RX FT/new-peer semantics, including generation advancement on those routes, remain open.
No target compilation of this new enqueue variant yet; temporary FT TU header
probe alone does not cover common/mlme.c. Keep this work local for the coherent
producer/consumer package. Existing published CI handles unchanged this turn.

## RRB snapshot capture and stamped FT consumer prepared locally — 2026-11-19

New bind_ft stage in ft-enqueue-generation-composition.py captures a value
stamp inside the existing RRB lookup lock and passes that exact value to the
explicit native enqueue variant instead of REPORT_MGMT_FRAME_TO_MLME. It does
not recapture a new generation after allocation. A prototype is explicitly
shared with the FT TU. Native output buffer is still freed after enqueue.

For stamped events, FT_FtAction restores immutable generation/WCID/MAC plus
receiver BSS and acquires the existing-peer scope before switch/lookup/insertion
or native handlers. The out path releases the scope without holding a lock
across native work. A stale stamp cannot insert a replacement station first.
Zero-stamp ordinary RX remains native and explicitly not covered by this step.
Outer association-vs-key/control admission remains a separate prerequisite.

check-ft-generation-binding.py reuses full callback fixtures, executes the
complete composed producer/consumer with explicit queue/crypto/parser actors,
and passes ASan/UBSan in default/SNR configurations. Producer allocation-time
slot replacement still passes original generation; stale consumer refuses;
live request/confirm balance event-users/table transactions. Real native explicit
enqueue is separately exercised by check-ft-enqueue-generation.py. This is not
one fully linked native MLME/FT/crypto end-to-end test. Report:
docs/evidence/WR1200JS-FT-GENERATION-BINDING-HOST-2026-11-19.json.

Uncommitted coherent generation work remains producer-uninstalled. Temporary
FT probe currently typechecks primitive only; it does not yet compile the new
common/mlme.c explicit enqueue or bound FT producer/consumer. Next extend exact
MIPS temporary probes to both TUs, cover ordinary RX/new-peer capture semantics,
review pending/ordinary-RX generation transitions and daemon key-response writers before enable.
Current published103707fb remains unchanged; no new CI dispatch this turn.

## Prepared paired FT/MLME target verification — 2026-11-19

check-ft-bounds-target-tu.py now prepares BOTH common/ft.c and common/mlme.c
using their respective original Kbuild commands and pinned compiler identity.
The temporary FT TU includes bounds, producer/stamped consumer binding and
outer association arbitration; temporary MLME TU contains the explicit-stamp
native receive-enqueue variant. Both require active AP/FT/MT7603/MT_MAC/PCI
macros and ELF32 little-endian MIPS output. readelf must show FT's undefined
GLOBAL wr_ft_mlme_enqueue_for_recv and MLME's defined GLOBAL provider. This is
symbol/type evidence only, not a final module link or installed producer.
Native source hashes are checked unchanged; objects remain temporary. Report
retains original FT fields and adds per-TU command/source/object receipts.
Local source preparation, CLI/Python syntax, full callback/peer primitive,
explicit native queue and producer/consumer host regressions PASS. Actual paired
MIPS result still pending; no such coverage inferred from older FT-only probes.

Optional1427/run44563426937 for exact2ff341d8 completed SUCCESS. Actual artifact
14552535822 archive SHA256a467f62a494e48138a2d783798f0ab504aa4e165d80e53b581f355d4dbadf0dd
and ZIP CRC independently verified; ft-bounds-target-tu.json says passed,
module_installed false, runtime_verified false. Durable OPTIONAL1427 FT TU
report saved; owned ZIP removed. This proves prior RRB-context FT TU only.
Standard1428/run44564759097 all four jobs SUCCESS. Exact103707fb optional
run44567353810 dispatched once with true/iot/peer82 after absence check; this
predates current local generation work. ABI958 last observed in_progress.

Still required before FT producer activation: ordinary RX/new-peer identity,
pending/ordinary-RX FT generation transition, daemon-response writers and full
association/control/lifetime integration review. Preserve actual crypto and
firmware behavior; do not enable this prepared path from host evidence alone.

## FT daemon completion dependency audited — 2026-11-19

Pinned source audit FT-DAEMON-REQUEST-COMPLETION-AUDIT records file hashes and
exact references. FT request emits station S1KHID and BSSID R1KHID. Conditional
R1KH_HARD_RETRY path in FT_AuthReqRsnValidation waits30ms on peer ack_r1kh;
FT_KDP_KeyResponseToUs subsequently resets peer cache-miss counters and completes
that ack after MAC-only lookup. Response pNonce is assigned but not compared
inside this function. Exact image macro activity has not yet been established.

Integration consequence: the peer scope must not reject the matching daemon
completion merely because wr_assoc_event_users is already1 for the waiting
native handler. This would create repeated timeouts. A response needs request
identity/BSS/generation correlation and a completion-specific admission contract
compatible with the waiting handler's lease; no spinlock across the wait.
Do not use current MAC/generation recapture as proof of original request identity.
Ordinary RX/new-peer stamping, generation transition on those routes, and daemon completion must
be designed together before producer installation. Existing host action actors
do not exercise this conditional native wait/response concurrency.

Exact8fb standard1430 and ABI959 SUCCESS; all four standard jobs inspected.
Optional1431/run44576631105 for exact8fb, true/iot/peer82 completed SUCCESS;
its paired FT/MLME target report was independently checked and is recorded
below. This proves temporary translation-unit and symbol compatibility only;
no result establishes installation or FT runtime.


## Optional1431 completed; RRB admission semantics remain open — 2026-11-19

Run44576631105 (#1431) completed success for exact8fb2bbe6. Its downloaded
`iot-merged-driver-probe` artifact and `ft-bounds-target-tu.json` were
independently checked; exact report, object hashes, paired symbol receipts and
artifact digest are in `docs/evidence/WR1200JS-OPTIONAL1431-FT-TU-2026-11-19.json`.
This closes the pending paired-TU compile observation for prepared FT/MLME
sources only. It does not close final module integration, installation, or
runtime acceptance.

Pinned `common/ft.c:FT_RrbHandler` uses `MacTableLookup` on the station MAC;
when absent it assigns `RESERVED_WCID` and still reports the action to MLME.
The terminating `FT_ACTION_BT_REQ` branch in `FT_FtAction` can then insert a
station entry before native request handling. The prepared binding instead
requires a captured active peer stamp, and its explicit MLME enqueue rejects a
zero stamp. Therefore an absent peer is dropped before that later native insert
can occur. This matches the explicit requirement to return without enqueue when
no active contextual peer exists, but leaves a native FT RRB path behavior
change whose applicability to legitimate deployments needs an explicit host
scenario and product acceptance before installation.

The prepared explicit enqueue is only bound from `FT_RrbHandler`. Ordinary
management RX categorized as FT action still uses the unmodified zero-stamp
path, and its `FT_FtAction` consumer remains native. Thus the paired target
result does not establish coverage for ordinary RX identity or complete FT
association-generation provenance. Keep both routes, fresh-peer insertion
semantics, generation transition on those routes, and daemon completion in the remaining
integration review. No source driver or router was changed by this audit.

## First-peer FT request ticket claim model — 2026-11-19

Owner selected a pending BSS+MAC identity ledger to preserve native
`FT_ACTION_BT_REQ` first-peer insertion without allowing an unrelated queued
event or same-MAC foreign-BSS station to authorize it. The standalone ledger
now models one-shot claim under the caller's `MacTabLock`: a second claimant or
same-key reservation is refused while the ticket is claimed; a failed native
insert may unclaim it; successful insertion must retire the exact BSS+MAC
before releasing the claimed and queued references, making sibling events
stale. Other BSS tickets for that MAC remain independent.

The C fixture passes under ASan/UBSan and Nim model passes the same claim,
retry, retirement, stale-token, capacity and overflow cases. These are model
checks only. No SDK source, MLME queue lifecycle or target insertion path is
yet wired to the ledger, and there is no target compile or runtime result.
Next integration must initialize adapter storage once, reserve/release tickets
on all queue ingress/failure/drain paths, carry ticket values through dequeue,
and claim plus insert atomically for the expected BSS. Keep native
first-peer behavior; never fall back to a global MAC-only lookup.

The pinned `MacTableInsertEntry` takes `MacTabLock` internally (line 422),
chooses a free WCID, and assigns `wdev`, BSS index, and MAC while holding it;
the normal unlock is at line 768. Therefore a caller-side claim followed by
unlock and this native insert leaves a race window. A safe candidate needs a
private insertion hook/refactor that checks and claims the ticket inside that
same table critical section while preserving the existing initialization and
hash/list bookkeeping. `RTMPInitAdapter` initializes `MacTab` and its lock at
1498-1501; ledger storage must be initialized there exactly once before queue
ingress. These are pinned-source observations, not an implementation.

## Prepared pending-ticket native insertion composer — 2026-11-19

`ft-pending-insert-composition.py` now prepares adapter ledger storage and
initializes it at fresh `RTMPAllocAdapterBlock` allocation, before publishing
the adapter. It never resets the ledger on reopen. This corrects the earlier
initialization proposal above: MAC-table reinitialization is not a fresh
adapter-allocation boundary.

The composer clones the generation-prepared native insertion, retaining vendor
initialization and private startup/table owner gates. Under the native
`MacTabLock`, it checks the exact ticket BSS/MAC, wdev and func_idx, rejects any
nonempty matching target-context entry, claims the ticket, then runs the native
insertion bookkeeping. A foreign-BSS duplicate is not adopted. Success retires
all same-key queued siblings; failed allocation unclaims for retry. Every
ordinary successful native insertion also retires same-key pending tickets.
The new wrapper holds the existing table transaction through the unlocked
TX-burst tail. The caller retains ownership of the queued ticket reference.

`check-ft-pending-insert.py` checks pinned source anchors/order and executes the
generated admission, finish, failure and transaction-wrapper fragments under
ASan/UBSan with explicit allocation actors. It covers target-context duplicate,
foreign-BSS same MAC, stale sibling, retry/full capacity, reset exclusion,
lock/reference-independent transaction balance and duplicate composition.
The original native insertion is byte-identical except the successful pending
ticket retirement hook; private startup gate placement is separately checked.
Nim ledger and existing FT generation/parser regressions pass. Receipt:
`docs/evidence/WR1200JS-FT-PENDING-INSERT-HOST-2026-11-19.json`.

This composer is not invoked by the producer or FT callback. The entire native
insertion function and target TU have not been compiled for this change.
Queue ticket ownership/release, first-peer consumer wiring, atomic inserted-peer
generation/lifetime handoff, FT_AUTH generation transition and IAPP completion
remain open. Keep all prepared FT producers uninstalled.

## Prepared pending FT queue transport — 2026-11-19

Added `ft-pending-enqueue-composition.py` and `ft-pending-queue.h`: an explicit
pending-ticket clone of native MlmeEnqueueForRecv moves one existing reference
under Queue->Lock. Failure retains the producer ticket. The clone admits only
terminating BT_REQ with exact BSS/MAC/StaMac/TargetApAddr and RESERVED_WCID;
ordinary native enqueue remains byte-identical. A live queue-ticket slot cannot
be overwritten. Consumer take moves the reference to an empty local owner for
later current-validation and release under MacTabLock; no refcount increments,
table locks or identity recapture occur during queue publication/take.

Host execution of the entire cloned native enqueue passes ASan/UBSan in default,
EAP and SNR variants. Updated existing Nim helper passes linear ownership/stale
release cases. Pending insertion and existing-peer native enqueue regressions
pass. Receipt: docs/evidence/WR1200JS-FT-PENDING-ENQUEUE-HOST-2026-11-19.json.
Pinned RTMP_MLME_HANDLER expands to RtmpMLMEUp; direct MlmeHandler invocation is
in MlmeThread. Synchronous caller dispatch is not established for this SDK.

Still uninstalled: queue metadata init/reuse, ingress reservation and producer
wiring, consumer first-peer insertion/lease, normal/stale/restart/destroy release
and task shutdown quiescence. Next close those lifecycle sites and atomic
new-peer scope handoff, then FT_AUTH generation and IAPP completion. No target
compile or router changes; Modern stays paused. Full project goal remains open.


Pinned wakeup follow-up: `include/os/rt_linux_cmm.h:252` maps RtmpMLMEUp to
RtmpOsMlmeUp for the OS abstraction route. `os/linux/rt_linux.c:2082-2099`
implements kthread wake_up or task semaphore post, with no synchronous handler
call. Hashes are in the pending-enqueue host receipt. This removes the earlier
unproven synchronous-dispatch concern for this route; task shutdown/quiescence
and effective macro selection still require their own source/target checks.

## FT pending queue dispatch and drain prepared — 2026-11-19

Extended the uninstalled queue composer to initialize sidecar fields for every
native queue slot, reject ticket enqueue after the primary MLME queue closes,
validate stale tickets before state-machine dispatch, and release the ticket
under MacTabLock after the handler returns. Halt closes the pending ingress,
then drains detached slot tickets after RtmpOSTaskKill and before queue destroy.
PCI restart closes ingress after exclusive bRunning acquisition, drains queued
references, and reopens after the native reset sequence. Drain detaches under
Queue->Lock and releases after dropping that lock, so no Queue->Lock/MacTabLock
nesting is introduced. FT BT_REQ is ACTION_STATE_MACHINE traffic and the clone
admits it only to the primary queue; EAP queue sidecar slots are still initialized.

`check-ft-pending-enqueue.py` executes the complete enqueue clone under
ASan/UBSan in default/EAP/SNR variants and asserts handler, restart, halt, init,
close, drain and reopen ordering against pinned source. The C, Nim, insertion,
existing-peer enqueue and parser regressions pass (exit 0). Evidence:
`docs/evidence/WR1200JS-FT-PENDING-ENQUEUE-HOST-2026-11-19.json`.

Pinned shutdown audit found an unresolved native failure path: in the non-kthread
route, `RtmpOSTaskKill` waits for taskComplete only if task signalling succeeds;
`MlmeHalt` logs a failed kill but continues to destroy queues. The prepared
composer does not repair the void teardown call chain and remains uninstalled.
Also open: ingress reservation/caller release, consumer-to-insertion binding,
new-peer generation/lifetime handoff, FT_AUTH advancement and matching IAPP
completion. No target compile or runtime result.

## Prepared first-peer identity and lease — 2026-11-19

The selected policy preserves native first-peer FT BT_REQ insertion through a
bounded pending BSS+MAC ledger. It authorizes insertion for the exact claimed
identity, so a same-MAC peer on another BSS is not adopted and a live active
peer is not a prerequisite for legitimate first association.

The candidate insertion composer now reserves the chosen free WCID while
`MacTabLock` is held, binds the claim to BSS+MAC, and publishes the entry's
association generation and visible generation before unlocking. The candidate
lease helper then holds the peer event-user and peer-table transaction while
synchronous `FT_AuthReqHandler` may mutate the still-unauthenticated entry.
Successful AUTH advances and republishes the association generation while
updating the held lease, so queue snapshots from before the transition go stale.
Failed authentication leaves the new entry unauthenticated. Close refusal,
generation exhaustion, and drift retention are covered by host fixtures;
uncertain identity retains ownership and poisons table reset ownership.

`check-ft-pending-insert.py` and the ASan/UBSan lease fixture pass against pinned
c25283e. The prepared composer is still uninstalled; this does not execute the
whole vendor function or prove target compilation. `FT_FtAction` ownership and
all callback exits, ordinary RX first-peer flow, IAPP response correlation,
native delete/reassociation arbitration, and full staged target TUs remain open.
Do not install a producer until those are composed and verified. No image or
device acceptance is claimed.

## Fixed-size IAPP response token audit — 2026-11-19

The pinned automatic KEY_REQ path zeroes and fills `FT_KDP_EVT_KEY_ELM`, then
copies its full size into the kernel event. The daemon copies that payload into
the security block. At the R0KH, `FT_KDP_KeyRequestToUs` updates the same struct
in place, then emits the full struct as KEY_RSP_AUTO; the daemon copies the
returned payload into the ACK and then into the response OID. The seven reserved
bytes (`FT_KDP_EVT_KEY_ELM.RSV[3]` and `KeyInfo.RSV[4]`) are not written by the
pinned automatic path. The unrelated manual ioctl path zeroes `KeyInfo.RSV`.

This supplies a candidate fixed-size per-request token carrier without changing
the structure size. A local request ledger would retain the token's BSS, MAC,
WCID and association generation, and the response must validate both token and
live context before touching the PMK-R1 cache or completing `ack_r1kh`. The
current handler still ignores InitVec and admits by MAC only. The exact
round-trip is source-audited only for pinned c25283e; other R0KH builds are not
verified and must fail closed when the token is absent or changed. No code uses
these bytes yet. Receipt:
`docs/evidence/WR1200JS-FT-IAPP-RESERVED-TOKEN-AUDIT-2026-11-19.json`.

This audit also found that `ack_r1kh` is waited on and completed under
`R1KH_HARD_RETRY`, but the pinned insertion path never calls
`RTMP_OS_INIT_COMPLETION` for it. The prepared insertion composer now initializes
that completion immediately after each entry reset, guarded by the same feature
macro. It remains uninstalled; target compilation with the macro enabled is
required to verify the conditional path.

Next: integrate the modeled token ledger with automatic request creation,
response validation and timeout/association retirement; add a response-specific
peer lease that can coexist with the waiting AUTH handler. Then target-compile
`ap_ftkd.c` with the existing four FT TUs. Do not install
the prepared ingress until callback, response, deletion and teardown ownership
are composed and verified.

The standalone token ledger model is now implemented in
`tools/iot/ft-iapp-response-token.h`; its ASan/UBSan fixture passes exact token,
MAC/R1KHID, BSS/WCID/generation, timeout race, same-association request
supersession, association retirement and capacity checks. This does not exercise
a response lease or actual driver/cache
mutation. Receipt:
`docs/evidence/WR1200JS-FT-IAPP-RESPONSE-TOKEN-HOST-2026-11-19.json`.

## Native FT cache lifecycle admission gap — 2026-11-20

`inspect-ft-cache-lifecycle.py` reproduces the pinned source audit. Both APStop
and APStopBssOnly reach adapter-wide FT_Release, so a BSS-local lease cannot
alone protect cache lifetime. FT_R1KH_KEEP gates init/release on FT_RadioOff;
Set_RadioOn_Proc changes that flag after the synchronous radio call. Effective
radio callback ordering and feature selection still need verification.

Cache destroy clears Ready before locking and frees the lock after unlocking.
Maintenance checks Ready before locking, then performs station lookup and MLME
enqueue under the cache lock. Neither the Ready predicate nor owned cache
snapshots prove that the lock itself is still live. Before installing prepared
cache APIs, compose adapter-wide admission across every reader/writer and
init/destroy; close ingress and drain holders before freeing the lock. Review
reverse lock order before adding MacTabLock-to-cache nesting. Do not hold a
spinlock while waiting for drain. This is source evidence only; no producer,
target, final image or device acceptance is established. Receipt:
`docs/evidence/WR1200JS-FT-CACHE-LIFECYCLE-AUDIT-2026-11-20.json`.

## Prepared FT cache lifetime admission — 2026-11-20

`ft-cache-lifetime.h` reuses peer-table-owner transactions/exclusive serials.
Cold/start/live/drain/destroy phases prevent publication before native init,
close ingress before holders return, and refuse destroy until holders reach
zero. Native init/free and drain wait execute outside the adapter lifetime lock;
uncertain results retain exclusion. Linear noncopyable scopes bind each caller
to its cache instance and initialization serial. ASan/UBSan fixture covers 0–8
holders, close-first refusal, wrong-owner and duplicate release, exclusive
init/destroy, reopening, serial/counter overflow and partial failure retention.

This helper is uninstalled and does not establish native AP caller propagation,
adapter allocation retention or effective lock selection. Next bind all cache
APIs and maintenance to a single adapter lifetime lock that outlives cache lock,
and propagate close/drain refusal through both APStop and APStopBssOnly before
native destroy. Keep response identity/peer ownership separate but composed.
Receipt: `docs/evidence/WR1200JS-FT-CACHE-LIFETIME-HOST-2026-11-20.json`.

## Prepared cache API lifetime wrappers — 2026-11-20

`ft-cache-api-lifetime-composition.py` wraps the prepared snapshot/store/delete
APIs with linear cache leases. A dedicated adapter lifetime lock is taken only
for admission/release and dropped before cache locking or allocation/free;
MacTabLock may already be held by a caller. This avoids adding recursive
MacTabLock acquisition to the prepared detached IAPP response path.

The host fixture executes generated functions with the pinned cache entry type,
asserts a lease exists on every native cache lock acquisition, closes ingress
inside allocation, and verifies destroy is refused until that store returns.
Cold/draining/post-destroy calls refuse, allocation failure releases its lease,
and repeated/missing-anchor composition refuses. ASan/UBSan passes; the existing
snapshot/atomic-store fixture and Nim pending identity regression also pass.

Not producer-installed. Dedicated lifetime lock/storage initialization and
adapter retention, maintenance, native init/release and AP teardown refusal
propagation remain unbound. No target compilation or physical acceptance is
claimed. Receipt:
`docs/evidence/WR1200JS-FT-CACHE-API-LIFETIME-HOST-2026-11-20.json`.

## Prepared native maintenance lifetime wrapper — 2026-11-20

The cache API composer now also prepares a wrapper around the byte-preserved
native FT_R1KHInfoMaintenance body. It admits a cache lease before the native
Ready check and releases after native return, including its early-return path.
The host fixture executes the pinned body with station lookup/MLME/event stubs:
live expiry removes/frees the entry, a close injected at lookup refuses destroy
until callback return, and cold/draining/post-destroy calls do not enter native.
ASan/UBSan and the pending-identity Nim regression pass.

This protects only the prepared cache lifetime boundary. Native station lookup,
queue context and lock ordering inside maintenance remain unchanged and require
independent arbitration work. Dedicated lock initialization, init/destroy and AP
teardown propagation are not yet bound. No production installation, target or
device validation. Receipt:
`docs/evidence/WR1200JS-FT-CACHE-MAINTENANCE-LIFETIME-HOST-2026-11-20.json`.

## Prepared fresh-adapter cache lock storage — 2026-11-20

`ft-cache-storage-composition.py` adds dedicated lifetime storage and lock
initialization only at the fresh RTMPAllocAdapterBlock predecessor, after the
resource lists and before OS_Cookie publication. It does not reinitialize on
UserCfgInit/BSS reopen. Direct spinlock initialization and OS_ABL allocation
are separate generated branches. OS_ABL failure leaves initialized false and
cache owner poisoned/closed. API and maintenance gates refuse before accessing
the lifetime lock if initialization failed.

Host fragment execution for both branches, source-placement/drift checks,
cache API/native maintenance ASan/UBSan and Nim pending checks pass. Whole
adapter allocation and effective target macros remain unverified. Final lock
release is deliberately unbound pending adapter callback quiescence and teardown
failure propagation; native cache init/release also remain unbound. Source
shows non-OS_ABL lock free is a no-op, while OS_ABL uses allocated lock content;
do not infer allocation lifetime from the non-OS_ABL branch alone. The prepared
package remains uninstalled. Receipt:
`docs/evidence/WR1200JS-FT-CACHE-STORAGE-HOST-2026-11-20.json`.

## Prepared checked native cache lifecycle — 2026-11-20

`ft-cache-native-lifecycle-composition.py` prepares checked entry points using
pinned native init/destroy clones. Init reserves exclusive lifetime ownership,
initializes outside lifetime lock and publishes only after Ready. The clone
checks OS_ABL cache-lock allocation failure rather than publishing Ready on
failure as native void init does. Failed allocation retains poisoned exclusive
ownership. Release closes ingress and refuses native destroy while holders
remain; retry after the last lease returns executes native entry free and lock
release outside the lifetime lock, then seals cold state.

The host fixture executes native list init/destroy with lock/allocation stubs
in direct and OS_ABL variants under ASan/UBSan. Held-lease refusal, release retry,
double init/release refusal, reopen and OS_ABL allocation failure pass. Legacy
FT_Init/Release and their original cache calls are not redirected: KDP/RIC and
FT_R1KH_KEEP semantics, AP stop refusal propagation and final adapter release
remain required before any production installation. This is not complete native
AP lifecycle or target verification. Receipt:
`docs/evidence/WR1200JS-FT-CACHE-NATIVE-LIFECYCLE-HOST-2026-11-20.json`.

## KDP whole-operation lifetime prerequisite — 2026-11-20

The reproducible `inspect-ft-kdp-lifecycle.py` source inventory classifies all
KDP control-block, initialization-flag and KdpLock accesses in ap_ftkd.c across
18 functions. Cache snapshot/store/delete and maintenance leases do not cover
those whole operations. Do not use cache drain as proof of KDP quiescence.

Native KDP init is void, may return on control-block allocation failure, and
ignores OS_ABL KdpLock allocation failure. Its initialized flag alone therefore
does not prove a valid allocated lock. Native KDP release frees and NULLs the
control block before evaluating TimerReport for cancellation in the broadcast
feature branch. That define is commented out in pinned ft_cmm.h; effective target
flags are not established here. Callback/task-queue quiescence remains required,
not merely moving a cancel call.

APStop and APStopBssOnly perform AP mutations before their late FT_Release call.
A late FALSE alone cannot preserve the AP lifecycle. Next bind whole-operation
KDP users and acquire release reservation before first AP side effects, then
propagate refusal through callers and compose KDP/RIC/cache retirement with
FT_R1KH_KEEP transitions. RIC init/release currently only log; this does not
establish lifetime of other RIC handlers. No producer or target change made.
Receipt: `docs/evidence/WR1200JS-FT-KDP-LIFECYCLE-AUDIT-2026-11-20.json`.

## KDP ioctl output contract before admission wrappers — 2026-11-20

Pinned ap/ap_cfg.c:4201/4206 calls void FT_KDP_DataEncrypt/DataDecrypt and then
copies DataLen bytes to userspace unconditionally at lines4211–4213. Therefore
an admission wrapper that simply returns on refusal does not propagate failure
to the caller. The checked lifecycle composition must include these ioctl
callers and an explicit failed-result/length contract; wrapping KDP functions
alone is insufficient. FT_KDP_EventGet also has an output pointer which needs a
well-defined refused result. Preserve native successful crypto behavior and
verify refusal produces no successful copied payload before installation.
This is source/caller-contract evidence; no crypto or target behavior claimed.

## Prepared checked KDP crypto/ioctl refusal — 2026-11-20

`ft-kdp-crypto-composition.py` prepares checked native encrypt/decrypt clones
and matching ioctl case edits. Refusal sets EAGAIN and zero output length;
cleanup after the nested switch exits the outer ioctl case before user copy.
The first host run caught an incorrect inner-switch-only break; the corrected
whole case now passes ASan/UBSan. Missing KDP state, allocation failure, empty
feature and zero/oversized crypto result refuse without copying output. Native
success flow and allocation balance pass with a substituted AES primitive.
An admitted crypto operation holds a lifetime lease; close cannot destroy until
it returns. CryptKey writer serialization, all KDP users/release, AP teardown,
cross-TU declarations and real target compilation remain open. No producer
installation or real crypto/device claim. Evidence:
`docs/evidence/WR1200JS-FT-KDP-CRYPTO-HOST-2026-11-20.json`.

## Prepared EventGet output ownership — 2026-11-20

`ft-kdp-event-output-composition.py` initializes EventGet output to NULL before
feature/init early returns. Its ioctl caller initializes the local pointer and
releases a detached event after either output branch, including a too-small
userspace buffer. Previously only the successful-size branch freed that event.
ASan/UBSan executes the actual prepared caller fragment for absent event,
short/exact/large capacity and copy failure, asserting exactly-once cleanup.
EventGet extraction is substituted in this fixture; native queue lifetime and
payload allocation/length provenance remain unverified. Composer uninstalled.
Receipt: `docs/evidence/WR1200JS-FT-KDP-EVENT-OUTPUT-HOST-2026-11-20.json`.

## Native EventGet macro execution — 2026-11-20

`check-ft-kdp-event-native.py` now executes the prepared native function with
pinned FT_KDP_EVT_LIST_SIZE_GET/REMOVE_HEAD macros and link_list.h. Queue,
socket and empty feature branches pass ASan/UBSan. A deterministic competing
dequeue between size-read unlock and remove returns NULL without adopting a
stale output. Socket/empty branches leave the list untouched. This closes the
prior native-function execution gap, not the separate KDP control-block/lock
lifetime or allocated-payload bounds requirements. Composer remains uninstalled.
Receipt: `docs/evidence/WR1200JS-FT-KDP-EVENT-NATIVE-HOST-2026-11-20.json`.

## Prepared EventGet lifetime admission — 2026-11-20

EventGet now has a prepared lifetime wrapper: initialize NULL output, admit a
cache/KDP lease before native state/lock access, then release after return.
Host queue/socket/empty variants assert every native KdpLock acquisition holds
a lease. Close injected between size and dequeue cannot acquire destroy until
the callback returns; cold/uninitialized/closed calls refuse. ASan/UBSan pass.
All KDP users and release still need this shared admission before installation;
detached allocation-length provenance and target verification remain open.
Receipt: `docs/evidence/WR1200JS-FT-KDP-EVENT-ADMISSION-HOST-2026-11-20.json`.

## Nested KDP admission contract — 2026-11-20

The lifecycle inspector now records lexical internal FT call edges in ap_ftkd.c,
including KeyRequestToUs -> EventInform and R0KH_InfoAdd -> InfoDel. Independent
entry leases on every nested public call can refuse after close even while the
outer operation legitimately owns its lifetime. Compose outer admission with
internal implementations under the same owned lease; never introduce an adapter
wide bypass flag that admits unrelated callers. Call edges are potential across
feature branches, not effective target/runtime reachability. Macro calls,
external callers and indirect callbacks remain separate coverage requirements.
Receipt: `docs/evidence/WR1200JS-FT-KDP-CALL-ADMISSION-AUDIT-2026-11-20.json`.

## Typed EventInform input preflight — 2026-11-20

Prepared producer composition now checks actual sizeof association/reassociation
payloads and the KEY_REQ element when PeerIP is zero, before allocation and
native typed reads. Source placement and duplicate refusal pass. This is source
composition only: complete vendor type compilation, native producer execution,
ACTION control-block capacity provenance and lifetime remain open. Receipt:
`docs/evidence/WR1200JS-FT-KDP-TYPED-GUARDS-2026-11-20.json`.

## Typed event preflight execution — 2026-11-20

The typed guard check now extracts the actual packed event/key-info declarations
and size constants, compiles them and executes generated preflight for all
lengths0–1024, NULL/present payload and PeerIP branches under ASan/UBSan.
Host sizes are8/14/167 bytes. This supersedes the prior source-only type check;
whole EventInform, supplied pointer capacity and target ABI remain unverified.
Receipt: `docs/evidence/WR1200JS-FT-KDP-TYPED-EXECUTION-2026-11-20.json`.

## Prepared whole-signal initialization — 2026-11-20

EventInform initialized only its local EvtHdr before allocating signal storage.
Prepared composition now zeroes the entire allocated signal after the NULL
check and before Sig/case fields. The fixture executes that generated fragment
with the actual packed RT_SIGNAL_STRUC, nonzero-filled allocations and all256
IDs, asserting every non-Sig byte is zero. ASan/UBSan and typed guard checks
pass. This is not whole producer, queue/socket or target execution. Source also
shows socket FrameLen includes event header whereas the legacy ioctl length
arithmetic omits it; daemon wire expectations require audit before changing it.
Receipt: `docs/evidence/WR1200JS-FT-KDP-SIGNAL-INIT-HOST-2026-11-20.json`.

## Unified prepared KDP source map — 2026-11-20

`ft-kdp-package-composition.py` composes full ap_ftkd.c/ap_cfg.c/ft.h source maps:
checked crypto implementations and matching declarations/callers, initialized
EventGet with lifetime admission and detached-event cleanup, producer span/typed
guards and whole-signal initialization. It refuses missing cache-storage
prerequisite and duplicate preparation. Pinned source is never overwritten.
`check-ft-kdp-package.py` verifies paired symbols and caller cleanup in the full
maps; crypto and native EventGet host fixtures also pass. This is not a full-TU
compile; the check supplies a synthetic cache-storage marker. Real predecessor
composition, other KDP users/release, nested admission and AP lifecycle must be
completed before target staging or installation. Original unused legacy crypto
prototypes remain for now; target caller coverage must confirm none remain.
Receipt: `docs/evidence/WR1200JS-FT-KDP-PACKAGE-COMPOSITION-2026-11-20.json`.

## Cache/KDP predecessor composition — 2026-11-20

`check-ft-kdp-cache-chain.py` composes actual pending/request storage and fresh
cache storage, native snapshot/caller conversions, atomic writers, cache API
and maintenance leases, then the unified KDP package. The prior package-only
synthetic initialized marker is replaced by the actual storage composer here.
Paired API declarations/callers and removal of raw cache lookups in converted
related TUs pass. The association peer-owner field schema remains a test
stand-in, explicitly not the full target predecessor. Checked native cache
lifecycle host regression also passes. KDP release/all users, native AP lifecycle
and effective target compilation remain open; no producer installation.
Receipt: `docs/evidence/WR1200JS-FT-KDP-CACHE-CHAIN-2026-11-20.json`.

## Checked crypto reference closure — 2026-11-20

Unified KDP composition now removes obsolete void encrypt/decrypt declarations
and scans all pinned native .c/.h files with prepared overlays for remaining
legacy identifiers, including function-pointer references. An injected external
caller is rejected; package and cache predecessor checks pass. This supersedes
the prior note retaining unused legacy prototypes. Lexical reference closure is
not target compile/link evidence, nor macro-generated identifier coverage.
Receipt: `docs/evidence/WR1200JS-FT-KDP-CRYPTO-REFERENCE-CLOSURE-2026-11-20.json`.

## Actual owner predecessor reproduced — 2026-11-20

Reproduced prepare-current-recovery-chain, full-driver overlay and complete
peer-retirement-chain in private scratch from pinned c25283e; all existing hash
gates passed without changes. Cache/KDP chain now supports --prepared-owner
and passed against actual radio-on-retirement-admission output, with no injected
peer-owner fields. This supersedes the owner-schema stand-in limitation for
this run. The scratch peer-chain.json records actual stage scripts and hashes.
No firmware build or production installation performed. KDP/AP lifetime
integration and full target TUs remain open.
Receipt: `docs/evidence/WR1200JS-FT-KDP-REAL-OWNER-CHAIN-2026-11-20.json`.

## Checked cache lifecycle in unified map — 2026-11-20

Added compose_map to the native lifecycle composer: it requires prepared cache
source/header/storage, adds checked initialization/release implementations to
common/ft.c and paired BOOLEAN prototypes to ft.h, and refuses duplicates.
The full cache/KDP map passes on the reproduced real owner predecessor.
Direct/OS_ABL native-lifecycle host fixtures pass. Legacy FT_Init/Release remain
unchanged; no activation or complete KDP retirement is claimed. Actual staged
APStop/APStopBssOnly already return BOOLEAN; future admission refusal should
extend that existing result chain before AP side effects, not add a parallel
void teardown route. Next bind whole KDP users/release and AP reservation.
Receipt: `docs/evidence/WR1200JS-FT-KDP-CHECKED-LIFECYCLE-MAP-2026-11-20.json`.

## Split checked cache release reservation — 2026-11-20

Checked release now exposes reserve and reserved-destroy entry points, keeping
the existing synchronous helper as reserve+execute. Reservation closes/drains
and claims the exact serial before native destruction. Wrong/stale tickets and
repeated reservation refuse; native free remains outside lifetime lock.
Direct/OS_ABL host tests and actual-owner composition pass. The entire AP
lifecycle must separately serialize reservation-to-destroy; linear tickets must
not be copied, concurrently executed or abandoned after side effects. This
external contract is not yet bound, so no AP caller is switched and no complete
concurrency/teardown claim is made. Receipt:
`docs/evidence/WR1200JS-FT-CACHE-RELEASE-RESERVATION-2026-11-20.json`.

## Reserved destroy execution claim — 2026-11-20

Reserved cache destroy now claims an explicit FREEING phase under lifetime lock
before dropping it for native destruction. A same-ticket second executor cannot
pass DESTROYING after that claim. The native lifecycle fixture injects a duplicate
release during free-lock execution and verifies refusal before a second native
free. Direct/OS_ABL ASan/UBSan, 0–8-holder helper tests and actual-owner map
composition pass. This supersedes reliance on external serialization for this
specific double-destroy interval; AP operation ownership and ticket propagation
still need binding. No producer installation or threaded/target claim.
Receipt: `docs/evidence/WR1200JS-FT-CACHE-DESTROY-CLAIM-2026-11-20.json`.

## Prepared KDP crypto key snapshot — 2026-11-20

Crypto clones now copy16 key bytes under KdpLock to an owned stack snapshot,
run synchronous AES outside the lock, and volatile-wipe the snapshot immediately
after AES. The package composes CryptKeySet publication under the same lock;
password hashing stays outside it. Host crypto stubs verify the AES pointer is
separate and an injected live-key change does not change the owned snapshot.
ASan/UBSan native/empty variants and real-owner source-map checks pass. Writer
whole-operation admission, actual writer/hash execution and target concurrency
remain open, so this is not installed or complete key lifecycle acceptance.
Receipt: `docs/evidence/WR1200JS-FT-KDP-KEY-SNAPSHOT-2026-11-20.json`.

## Prepared checked KDP key writer — 2026-11-20

CryptKeySet now has a prepared checked native clone and lifetime wrapper,
locked40-byte publication into the vendor100-byte key storage, and volatile
cleanup of local key material. Native hash/default selection remains; hashing
runs outside locks while holding the lease. The ioctl caller propagates FALSE
as EAGAIN and its header uses the checked BOOLEAN API. Host native/empty
ASan/UBSan fixtures inject close during hash, prove no destroy until lease
return, and verify publication/default selection with a deterministic hash
actor. Real hash and whole ioctl execution remain unverified. The actual-owner
cache/KDP composition passes; no production installation or target claim.
Receipt: `docs/evidence/WR1200JS-FT-KDP-KEY-WRITER-HOST-2026-11-20.json`.

## Checked writer reference closure — 2026-11-20

The unified package reference guard now includes legacy CryptKeySet as well
as encrypt/decrypt. Negative fixtures inject each old API as an external
function-pointer reference and require rejection. Checked writer declaration,
definition and ioctl caller are paired; package and native/empty writer host
regressions pass. Macro-generated reference and target link coverage remain
separate. No production installation. Receipt:
`docs/evidence/WR1200JS-FT-KDP-WRITER-REFERENCE-CLOSURE-2026-11-20.json`.

## Key-set ioctl branch execution — 2026-11-20

The writer fixture now executes the actual prepared RT_FT_KEY_SET inner-switch
branch, including caller NUL termination and checked FALSE -> EAGAIN status,
then caller buffer free. Native/empty ASan/UBSan checks verify balanced buffer
ownership across accepted/closed/missing-state cases. The outer ioctl dispatcher,
copy_from_user faults and real password hash remain unexecuted. No target or
production installation claim. Receipt:
`docs/evidence/WR1200JS-FT-KDP-KEY-IOCTL-HOST-2026-11-20.json`.

## Prepared key input cleanup — 2026-11-20

Key-set grouped ioctl cleanup now volatile-clears its owned length+1 buffer
before normal free and copy_from_user-failure free, scoped to RT_FT_KEY_SET.
The writer fixture executes the generated normal cleanup and checks every byte
is zero in accepted/refused native/empty scenarios. Copy-fault placement is
source-checked only. ASan/UBSan, package and actual-owner composition pass.
Receipt: `docs/evidence/WR1200JS-FT-KDP-KEY-INPUT-WIPE-2026-11-20.json`.

## Copy-fault cleanup execution — 2026-11-20

Writer fixture now extracts and executes actual prepared EFAULT cleanup for
lengths0–65 with dirty length+1 allocations, asserting all bytes zero immediately
before free, EFAULT retained and allocation balance. Native/empty ASan/UBSan
pass. This supersedes source-only copy-fault cleanup evidence; actual outer
ioctl/copy_from_user and hardware remain unverified. Receipt:
`docs/evidence/WR1200JS-FT-KDP-KEY-COPY-FAULT-HOST-2026-11-20.json`.

## Destroy completion requires execution claim — 2026-11-20

Tightened destroy_finish to accept FREEING only. A correct serial in reserved
DESTROYING state cannot publish cold before execution claim. Host tests now
explicitly refuse that premature completion, then claim/finish normally.
Helper and direct/OS_ABL native lifecycle ASan/UBSan regressions pass. Native
free success still requires the checked binding receipt; state alone is not
hardware/quiescence evidence. Receipt:
`docs/evidence/WR1200JS-FT-CACHE-FINISH-CLAIM-GATE-2026-11-20.json`.

## Durable AP reservation prerequisite — 2026-11-20

Actual reproduced APStop/APStopBssOnly disable interrupts before their fallible
MacTableReset/ResetWdev and late FT_Release. Reserving a local FT ticket at entry
would lose it on reset FALSE; retry cannot reacquire DESTROYING state. Bind
reservation to durable adapter-owned AP operation identity/resume state, retaining
exact BSS/operation/ticket and skipping completed phases. Rollback is permitted
only with proof no side effects occurred. FT_R1KH_KEEP retained-cache outcomes
must remain distinct. Inspect existing close executor as carrier before changing
AP calls. Reproducible audit checks both staged BOOLEAN functions; this is source
contract evidence, not execution or target acceptance. Receipt:
`docs/evidence/WR1200JS-FT-AP-RESERVATION-AUDIT-2026-11-20.json`.

## AP carrier coverage — 2026-11-20

Expanded staged AP audit to enumerate every direct C caller and hash the actual
close-executor header. That executor retains only lane/running/retained/serial;
it has no BSS identity or FT reservation. Config, radar, WSC and other direct
APStop paths bypass RTMPDrvClose, so putting the FT ticket only in close executor
would leave those paths unowned. Use a shared AP operation owner covering direct
and close-mediated calls, exact BSS identity, durable reservation and retry stage;
then bind close executor as one caller rather than assuming universal coverage.
The inventory is lexical and feature-inclusive, not effective target reachability.
Receipt: `docs/evidence/WR1200JS-FT-AP-CLOSE-CARRIER-AUDIT-2026-11-20.json`.

## Prepared durable AP stop record — 2026-11-20

Added ft-ap-stop-owner.h to retain exact caller operation/device generation/BSS
identity, cache reservation and checkpoint across yield/retry. Competing callers
and concurrent execution refuse; resume retains the original ticket and stage.
Host ASan/UBSan covers every checkpoint0–3 and each identity mismatch. The three
stages are abstract receipts, not native AP phase mapping. Caller operation
provenance, device pins, cache reservation validation, FT_R1KH_KEEP semantics
and native side-effect boundaries remain unbound; no production installation.
Receipt: `docs/evidence/WR1200JS-FT-AP-STOP-OWNER-HOST-2026-11-20.json`.

## AP/cache reservation helper composition — 2026-11-20

ft-ap-cache-reservation.h joins the actual prepared durable AP record and cache
reservation under one caller-held lifetime lock. Busy drain preserves AP identity
without inventing a ticket; retry after lease return stores the real cache serial.
Later AP retries reuse that serial only while exact cache reservation is current.
Foreign identity and FREEING state refuse. ASan/UBSan fixture passes; native AP
phase mapping, caller provenance, adapter storage and shared lock binding remain
unimplemented. No producer or target acceptance. Receipt:
`docs/evidence/WR1200JS-FT-AP-CACHE-RESERVATION-HOST-2026-11-20.json`.

## Prepared AP owner adapter storage — 2026-11-20

Cache storage composer now adds durable AP owner outside MacTab and zeros it
at fresh adapter allocation only, alongside cache lifetime initialization.
AP owner/reservation headers are staged in the same source map. Direct/OS_ABL
storage fragment and actual-owner chain composition pass. No AP entry or phase
uses this field yet: verified operation provenance, native side-effect mapping
and release arbitration remain open. No producer installation/target claim.
Receipt: `docs/evidence/WR1200JS-FT-AP-OWNER-STORAGE-2026-11-20.json`.

## AP checkpoint requires exact cache completion — 2026-11-20

AP/cache helper now advances the pre-cache checkpoint only when its stored
serial matches a completed cold/closed cache record with no active executor,
holders, poison or retention. Reserved/claimed state and wrong serial refuse;
completion advances once. ASan/UBSan and actual owner map checks pass. Native
AP checkpoint mapping and caller identity remain external/unbound. Receipt:
`docs/evidence/WR1200JS-FT-AP-CACHE-COMPLETION-HOST-2026-11-20.json`.

## Hash refusal before key publication — 2026-11-20

Pinned RtmpPasswordHash rejects password strlen>63, whereas native KDP writer
selects supplied key for KeyLen8–64 and ignored hash return. Checked writer now
checks both supplied/default hash calls, volatile-clears local material and
returns FALSE before publication on failure. Injected hash-failure fixture
asserts unchanged native key, balanced lease/input cleanup and ioctl EAGAIN;
native/empty ASan/UBSan and package composition pass. Actual hash execution and
length/NUL consistency still require verification. Producer remains uninstalled.
Receipt: `docs/evidence/WR1200JS-FT-KDP-HASH-REFUSAL-HOST-2026-11-20.json`.

## Native password derivation execution — 2026-11-20

Actual pinned F/RtmpPasswordHash now execute under ASan/UBSan with system
libcrypto supplying only HMAC-SHA1. Default/supplied/63-byte results match an
independent Python PBKDF2 oracle for all40 output bytes. A64-byte input refuses
and leaves output unchanged, confirming the writer return-check requirement.
Vendor HMAC/SHA, combined writer execution and target remain separate gaps.
Receipt: `docs/evidence/WR1200JS-FT-KDP-PASSWORD-HASH-HOST-2026-11-20.json`.

## Checked writer with native derivation — 2026-11-20

Combined fixture now executes generated checked writer and actual pinned
F/RtmpPasswordHash, with system HMAC-SHA1 only. Published40 bytes match Python
PBKDF2 for default/supplied/63-byte inputs; short input keeps native default
selection.64-byte refusal preserves all prior key storage and returns its
lease. ASan/UBSan passes. Vendor HMAC, native AP/KDP lifetime and target remain
separate gaps. Receipt:
`docs/evidence/WR1200JS-FT-KDP-WRITER-REAL-HASH-2026-11-20.json`.

## Supplied key length/NUL contract — 2026-11-20

Checked writer validates supplied-key8–64 byte inputs contain no embedded NUL
and terminate exactly at KeyLen before calling native strlen-based hash. The
caller must own readable length+1 storage, as the ioctl allocation does; this
is not inferred pointer capacity. Short/out-of-range native fallback policy is
unchanged. Combined real-hash fixture rejects malformed termination without key
mutation or lease acquisition; existing PBKDF2 cases and package checks pass.
Receipt: `docs/evidence/WR1200JS-FT-KDP-KEY-LENGTH-CONTRACT-2026-11-20.json`.
## Same-serial AP reset resume helper — 2026-11-20

`peer-table-owner.h` now supports reopening only an active retained reservation
with its exact serial; regular begin/transaction paths remain closed. The AP
stop helper composes this with the exact saved device/operation/generation/BSS
identity and reset serial. Hold/resume is limited to the TABLE checkpoint and
refuses while a WDS identity remains outstanding. C owner fixtures pass under
ASan/UBSan, including wrong identity/serial refusal and re-retention after
another failed attempt.
This is not native APStop integration and does not prove that driver callers
provide or retain the identity. The current prepared FT request-context
harness exited 0 against the c25283e candidate, as did parser/action,
reset-retirement and actual-owner KDP/cache-chain checks. Native AP lifecycle,
the current FT five-TU target compile, production installation, image and
runtime are still open. Continue generation/BSS provenance and caller-lifetime
binding before enabling prepared composers.
