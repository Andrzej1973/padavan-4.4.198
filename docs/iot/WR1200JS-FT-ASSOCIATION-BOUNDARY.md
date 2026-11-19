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
