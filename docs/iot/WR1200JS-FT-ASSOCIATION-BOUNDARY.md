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
