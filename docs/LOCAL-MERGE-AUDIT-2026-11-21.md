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
Follow-up traced its logic to commit `1b13d68f`: the backend arm function and
normal shutdown readiness body remain present. Its declaration was published
in control-channel.h instead of rc-backend.h. Commit `a396c4ce` generalized the
control-server dispatch/continuation checks through `wr_iot_terminal_ready`,
whose runtime branch retains the same backend route. Thus this patch is
historical input, not a patch to apply again. No patch was applied by this audit.

The current `check-mailbox-active-normal-shutdown.py` passes all five host
modes with exit 0: ordinary ACTIVE publication, unavailable consumer, queued
signal, both together, and identity drift. It executes prepared host composition
with modeled external actors; it does not establish final image or hardware
shutdown acceptance. Its temporary build tree is managed by TemporaryDirectory.

The dated close/reopen plan contains historical next steps subsequently
implemented at least in part; preserve it as historical input pending a full
call-site reconciliation. Both plans now explicitly identify their historical
scope. The image-gates document's Modern pause statement
is corrected to the owner's 2026-11-20 settings/apply resumption.

## Verification and remaining work

Seven historical evidence records referenced by the changed lifecycle and
Mi Mini status documents were reviewed and selectively preserved with those
documents. They describe source/host findings and explicitly disclaim runtime
acceptance. Their original dates, hashes and proposed next actions remain
historical; preservation is not a new execution of the recorded checks or
resumption of Mi Mini work. Two host records were also compared against current
source hashes; any changed source requires fresh checks before using their old
PASS results for current acceptance. Private owner/workspace material remains
outside this package.

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

## Published checkpoint and focused follow-up

The eight initially unclassified nonignored files were read/classified:
`ie_length_check.nim` is a standalone boundary model with an intentional negative
control that makes its default suite exit 1; it is not driver acceptance.
`slot_lookup_check.nim` models stale/MAC-only lookup and prints an expected
negative control, but does not make its exit code a reliable test verdict.
Keep both local pending a deliberate helper package. `tools/replace_text.nim`
is a generic file-editing utility, unrelated to firmware behavior; retain locally
with its generated binary until a separate review justifies inclusion.
`tools/iot/ft_pending_identity_check` is generated output; its source is already
tracked, so do not stage the binary. `selected-boards.json` is generated selector
output, not an authoritative board catalog. The Phase 1A preparation note and
`tools/repository/inventory-build-calls.py` are a deferred static-inventory
proposal, not extraction implementation or a complete dependency graph.
No helper or generated output was removed or executed by this classification.

Remote main was verified at `03f5170407203e0317958fa1835920f992841dbf` after
the authorized fast-forward push. Its service checks run 44898285567 and
Zapret2 run 44898285594 completed successfully. Firmware standard1438/run
44898285630 and ABI run 44898285575 were still running at this observation;
no success is claimed for those jobs or any final image.

The inherited Mi Mini push trigger also started diagnostic run 44898285641.
This contradicted the deferred stage. It was cancelled using the installed
Windows GitHub CLI; GitHub independently confirmed `cancelled`. Follow-up
commit `6aee08b9f4446f60e7e323617c2755fe8d64ad8c` gates the job until the owner
resumes Mi Mini after WR1200JS acceptance. Its run 44898344777 is `skipped`.
Only the gate was staged; the pre-existing local resource-checker step remains
unstaged with its deferred helper/source changes. Staged YAML parsed and the
gate expression was checked before publication.

The modified MCU E2 static evidence was partially checked against the existing
pinned vendor header: header SHA256, firmware image SHA256 and computed payload
end match. Its 20 blocks contain 1443 decoded instructions, but full reproduction
requires the optional `pypcode` dependency absent from the current Python.
Keep this change local pending reproduction; both runtime and firmware ACK
contract flags remain false. Raw hashes do not validate the disassembly.

Follow-up resolved the reproduction dependency without a persistent install:
the official PyPI pypcode4.1.0 Linux cp312 wheel was downloaded into memory,
checked against its published SHA256 and extracted into TemporaryDirectory.
The committed inspector reproduced the complete evidence JSON exactly:20
blocks and1443 decoded instructions. No differing top-level fields. Temporary
dependency extraction was removed; no local wheel archive was retained.
The static report can now be preserved with
`docs/evidence/WR1200JS-MCU-E2-STATIC-REPRODUCTION-2026-11-21.json`.
This supersedes only the reproduction deferral above, not ACK/ROM/runtime limits.

Mechanical review of312 remaining local evidence files found145 with hashes
that differ from current source,27 mentioning local filesystem paths, no
matches for the narrow credential patterns checked and no true runtime/device
acceptance flags. These checks are triage only: they do not clear private data
or prove historical results. Keep the detailed per-record review local and
continue selective source/claim review before publication.

## Preserved deferred Mi Mini source package

The existing dirty Mi Mini LPRD selector, platform-resource guard, matching
manifest, resource-check helper and workflow step were reviewed as one
preservation package. No new board implementation was added by this audit.
All bundle file/patch SHA256 values match the manifest; the helper parses as
Python and the workflow parses as YAML. The Mi Mini board remains disabled
and its job retains the unconditional false gate published in6aee08b9.
No Mi Mini compilation, fixture execution, device access or board admission
was performed during this preservation review. The earlier source/host claims
remain historical. Resume implementation only after the WR1200JS four-variant
acceptance requirement is satisfied and the stage is resumed by the owner.
