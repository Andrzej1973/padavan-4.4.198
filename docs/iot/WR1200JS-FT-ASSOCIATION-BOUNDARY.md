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
