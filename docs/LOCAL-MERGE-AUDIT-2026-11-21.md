# Local merge preservation audit — 2026-11-21

The existing Linux checkout is on `main`. Merge commit
`c50480744f4f91caec15e82db0cf0253343f5125` includes the service WebUI branch.
Live GitHub refs checked on this date: main
`70964a3dab872f83478bccce3e7c37a4e4ec176c`, service WebUI
`b581469258780d65429c6e3d29b3c950072175c3`. Both are ancestors of the local
checkpoint `3912448a8b5d142681939c0fb144d4431ee19286`. Of the 1131 commits ahead
of remote main before the Mi Mini documentation commit, 1122 were already
reachable through the remote service branch. No history was rewritten.

## Preserved untracked content

The private inventory records individual paths, sizes and SHA-256 for all
48,845 nonignored untracked files present before inventory creation. Hashes
identify content; they do not validate assertions in historical evidence.

| Classification | Files | Bytes | Disposition |
| --- | ---: | ---: | --- |
| Scratch of uncertain or unfinished use | 48,505 | 1,229,252,257 | Preserve locally; review active use before deletion |
| Historical environment records | 3 | 15,039 | Preserve locally; historical claims may be stale |
| Other helpers, binaries, selector and phase preparation | 8 | 462,090 | Preserve; source review required; do not stage generated binaries |
| Historical evidence awaiting source/claim review | 317 | 1,702,250 | Preserve; do not promote recorded host/CI observations to device acceptance |
| Private workspace inventories | 2 | 269,991 | Keep outside publication |
| IoT candidate documents and patches | 5 | 26,701 | Preserve; reconcile against current source before publication |
| Private owner materials | 4 | 18,558,182 | Keep outside publication |
| Deferred Mi Mini source helper | 1 | 2,898 | Preserve; no Mi Mini development resumed |

No originals were deleted or moved. The inventory itself is local audit output,
not an additional copy of the inventoried data. These counts exclude ignored
files and tracked modifications; they are not a complete disk-usage census.

## Candidate reconciliation

Read-only `git apply --reverse --check` succeeds for
`WR1200JS-NATIVE-EXCLUSION-CANDIDATE.patch` and
`WR1200JS-ON-CAPTURE-REFUSAL-CANDIDATE.patch`: their complete patch changes are
present in the current source. Preserve these historical patches without
applying them again. Both forward and reverse checks fail for
`WR1200JS-MAILBOX-ACTIVE-SHUTDOWN-CANDIDATE.patch`; its context has diverged.
The current backend defines `wr_iot_rc_backend_applied_route`, but that symbol
alone does not prove the entire patch is implemented. Compare its remaining
hunks before deciding disposition. No patch was applied by this audit.

The dated close/reopen plan contains historical next steps subsequently
implemented at least in part; preserve it as historical input pending a full
call-site reconciliation. The image-gates document's Modern pause statement
is corrected to the owner's 2026-11-20 settings/apply resumption.

## Verification and remaining work

Repository/profile validation, its negative fixtures, and whitespace checking
of the committed delta from the live service-branch SHA pass locally. These
checks establish neither full firmware compilation nor image/device acceptance.
Mi Mini priority corrections are committed separately in `3912448a`.

Remaining tracked changes include deferred Mi Mini configuration/source,
historical evidence additions, status corrections and a failure-monitor parser
change whose real triggering CI log remains to be established. Preserve each
until its claims and dependency scope are reviewed. Public evidence must be
reviewed for private material before selective staging. Phase 1A extraction
remains a separate proposed stage; no bulk source move was performed.
