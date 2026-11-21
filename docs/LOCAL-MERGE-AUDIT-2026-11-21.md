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

## Monitor patch provenance resolved

The missing-file matcher is supported by real optional900/run42466029821.
Its original failed step could not open tools/check-libyaml-download.py.
Monitor42466114320 correctly bound that source run and step, but its surviving
console excerpt omitted the causal Python line. Upload logs identify
artifact13611414280; the current artifacts API returns none, so the ZIP itself
was unavailable for comparison. This limitation is recorded explicitly in
`docs/evidence/WR1200JS-OPTIONAL900-MONITOR-MISSING-CHECKER-2026-11-21.json`.

The fixture now uses the real run/path. The patched Nim compile, empty fixture
and full offline executable suite pass; a temporary committed-version parser
fails exactly the new missing-file assertion. That negative-control build
needed explicit -d:ssl outside its normal config.nims directory. All temporary
compiler/cache/fixture output was removed. This resolves the earlier reason
for leaving the parser patch uncommitted. No recurring automation was resumed.

## Original-content preservation recheck

At checkpoint f454e87a the entire initial48845-file nonignored untracked
inventory was re-read and hashed. Missing original paths:0. Sixteen initial
files are now tracked. Exactly five baseline files changed: the three reviewed
FT cache/storage evidence records and the two historical IoT plan documents.
All five current files match their committed HEAD bytes exactly; their changes
are the recorded audit metadata and historical/current-priority clarifications.
Every other baseline file retains its initial SHA256. No originals were moved
or removed. This check includes the initial scratch files, not only docs.
New audit reports are additional metadata and are outside the initial baseline.

The remaining untracked content is preserved locally. Raw owner materials,
workspace histories/inventories, generated selector/binaries and standalone
helpers are excluded from publication by the dispositions above. Remaining
historical evidence has per-record mechanical triage, but its claims are not
fully revalidated. Source drift and uncertain/private records must retain that
status; no generic PASS or device-acceptance conclusion may be inferred from
their preservation. The detailed inventories remain local rather than exposing
private paths in GitHub.

## Retention decisions for remaining evidence

After selective preservation,307 original evidence files remain local. The
private per-file disposition records each exact path, size, SHA256, purpose,
tracked textual references, current-source hash matches/drift, publication
readiness and retention reason. Exact content comparison against candidate
tracked files found no tracked duplicates. All originals remain at their
existing paths; no archive, relocation or deletion is needed to retain them.

| Retention category | Files | Decision |
| --- | ---: | --- |
| Historical source/host/CI evidence with unvalidated claims | 285 | Retain locally; use only after checking source revision and original result |
| Private workspace inventory | 1 | Keep outside publication |
| Historical static build inventory | 1 | Retain locally; generator is preserved separately |
| Historical cleanup receipts | 14 | Keep as history; never infer new deletion permission |
| Provenance-sensitive observation | 1 | Keep private; no new device authority |
| Untrusted historical diagnostic logs | 4 | Retain original context; review before reuse/publication |
| Historical source hash manifest | 1 | Retain as identity metadata, not test proof |

This disposition completes the safe keep/exclude decision for these records;
it does not certify their historical claims. Uncertainty is a reason to preserve
them separately, as permitted by the owner's repository-completion task.
The separate dependency snapshot, taken before the last two source-audit records
were committed, counted309 remaining records and104 with tracked textual
references. References are evidence of documentation use, not semantic test
coverage. No original is redundant merely because its hash or test result is old.

## Final preservation and ancestry recheck — 2026-11-21

At published main `2fcc4f3fd45430a5135f348482a8da3d3ffc3ce1`, historical
origin/main70964a3d, local service tipc9e1e892 and remote service tipb5814692
are all ancestors. Mergec5048074 retains its two recorded parents. Local main
and origin/main agree; Git connectivity check passes; no staged/modified
tracked files or unmerged entries were present at this observation. Only the
existing main checkout is registered; no new checkout was created.

All48845 original inventory paths still exist. The baseline included3477
symlinks without content hashes; all3477 are still symlinks. Their original
link-target text was not inventoried, so unchanged target text cannot be proven
from that baseline. The earlier broad hash statement must be read with this
limit. For regular files, six differ from baseline: the five reviewed records
listed above plus the Phase1A preservation note. All six match committed HEAD
bytes. Twenty-three original paths are now tracked. Every other hashed regular
file matches its baseline digest. The private detailed receipt remains local.

Standard1440 passed for6e715891. Its successor2fcc4f3f corrects optional1439
FT composition. Its push triggered ABI961/run44902041131, but firmware push
paths do not include these isolated FT helper paths. After checking existing
runs, standard1441/run44902143769 was manually dispatched on main and its API
head SHA independently confirmed2fcc4f3f. Both runs were active at observation;
no success is inferred. Required optional iot/peer82 awaits standard success.
The next publication will combine related results/fixes in one push as directed
by the owner; no intermediate push was made for this receipt.

## Merge completion verified — 2026-11-21

The controlled merge/preservation goal is complete. Mergec50480744f4f91caec15e82db0cf0253343f5125
retains parents1645182535ece301d2cdb8f0a0f0ba8811432b2b and
c9e1e892f2c6048de709fdf12259ebdd0198a2c4. Historical remote main70964a3d
and local service tipc9e1e892 are ancestors of verified main29566c76.
Current connectivity/ancestry/whitespace checks pass; no unmerged entries,
tracked modifications or extra registered worktrees. Main matched origin/main.

Standard1450/run44915367873 and ABI966/run44915353811 succeeded for
29566c76d1dd46c8fa09671004f5f02993aebd00. Optional1451/run44916964158 also
succeeded. Its source receipt independently confirms that SHA; ZIP digests/CRC
and all ten FT object hashes match. Five prepared TUs pass normal/hard-retry
compilation and consumer/provider symbol checks. Receipt:
docs/evidence/WR1200JS-OPTIONAL1451-FT-TARGET-PASS-2026-11-21.json.
This is not installed FT integration, four final release images or physical
acceptance. Those remain separate project requirements, not merge claims.

All original48845 inventoried paths were retained; original hashed regular
files either match baseline or reviewed committed changes.3477 baseline
symlinks had no recorded target text, so target equality is unproven. Private
owner/history inventories, unfinished scratch and307 classified historical
evidence records remain local, intentionally untracked. No source archives,
owner data or unique evidence deleted. Preservation decisions and limits:
docs/LOCAL-MERGE-AUDIT-2026-11-21.md and private per-file disposition.

Nilabsent comparison is documented in docs/NILABSENT-ARCHITECTURE-ANALYSIS.md.
Bounded Phase1 catalog/audit extraction preserves the stable CLI and board
admission; broader path moves require a separate Phase1A dependency review.
See docs/REPOSITORY-PHASE1A-START-2026-11-08.md. No3.4 kernel transplant,
Docker build replacement or bulk move. WR1200JS4.4.198 stays primary; IoT,
Hybrid Modern, Band Steering, Zapret2, settings and four-variant requirements
remain. Retired v39-v42 standalone workflow paths were removed by owner request;
live donor dependencies and legacy control retained. Further work stays on main.

Cleanup: verification ZIPs read in memory, temporary object/fixture trees
removed automatically. Historical/unfinished scratch retained by explicit
classification; no new archive or backup. Publish this final evidence-only
package once; it does not change tested source/build inputs.

