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
