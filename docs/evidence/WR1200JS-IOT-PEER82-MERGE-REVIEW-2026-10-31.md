# Scheduler82 merge review — 2026-10-31

Scope: fresh source reconstruction and scratch three-way merge, not target
compilation, production installation or device acceptance.

## Verified inputs and CI

The local c25283e Git archive SHA256 was recomputed and matches
`sources.lock.json`:
`d209008e97e3a50b6b02054578546df17c5e90f87116a793b739f94e18bf5008`.
Fresh recovery preparation and full overlay succeeded. The following peer
chain completed 74 stages and produced 585 files; every final file hash
matches its generated peer-chain receipt. Scheduler source audit and strict
MinGW host fixture passed. This does not establish target concurrency safety.

[ABI run 41209565829](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/41209565829)
completed successfully on c0db7489549ef9809637c4d55aba8f1e93dd9527.
Its successor step covers v25b fixtures and MIPS objects, not whole scheduler82
Kbuild. Keep those scopes distinct.

## Actual overlay inventory

After normalizing line endings for comparison, scheduler82 changes 62 original
files and adds 70 files; no base files disappear. The existing assembler's
directory whitelist would ignore four modified paths:

- `ate/mt_mac/mt_ate.c`
- `easy_setup/mt7603_chip_ops.c`
- `easy_setup/mt7603_chip_ops_api.c`
- `mgmt/mgmt_entrytb.c`

Do not merely raise the old overlay-count limit. The complete inventory and
prepared-source interactions must be handled explicitly.

## Prepared driver overlap

An independent scratch tree was prepared with the existing driver-side Band
Steering helpers (idle, grant, WPS guards, channel stats, main BSS, OFF ACK,
uninitialized OFF and quiet status log), then all five RSSI helpers in normal
order. This is driver-source preparation only, not the full firmware pipeline.

Six modified files overlap with scheduler82. Three merge cleanly as text:
`ap/ap.c`, `ap/ap_cfg.c`, `hw_ctrl/cmm_asic_mt.c`. Three each have one conflict:
`common/rtmp_init.c`, `include/rtmp.h`, `mgmt/mgmt_entrytb.c`.
The first combines pre-publication RSSI initialization and IoT initialization;
the header combines independent declarations. Neither permits deleting a side.

## Semantic deletion-path conflict

The management-table merge needs a dedicated integration, not concatenation.
RSSI preparation replaces the original deletion function with
`wr_rssi_delete_entry(...identity, attempt)`. Scheduler82 instead introduces
`wr_iot_mac_delete_entry_body(...resume identity, table serial)` and the
`wr-iot-peer-normal-delete.inc` synchronous execution lease.

The trial merge incorrectly turns the IoT body into a stub calling the RSSI
function, while moving the actual body under the RSSI signature. This loses
the resume/table parameters from that body's scope. Moreover, RSSI calls from
`ap/ap.c` would enter that raw body without acquiring the IoT deletion lease.
Resolving the queue-retirement conflict text alone cannot fix either issue.

Required next integration: retain one raw deletion body with both contexts,
route ordinary/WDS/reset and RSSI callers through the same execution-admission
path, and forward optional RSSI identity/attempt only within that admitted
operation. Preserve exact WDS resume identity and reset table serial. Verify
busy/refused calls cannot reach the body, context is forwarded intact, failed
deletions release only their synchronous lease, and RSSI clearing evidence is
emitted only after actual entry clearing. Then compile the complete merged
driver under the actual target feature configuration.

No production source, router state, flash, reboot or service state was changed.

## Local integration implemented and tested

`assemble-peer-prepared-candidate.py` now validates the entire peer receipt,
all 74 generator hashes and the full base receipt before merging. It applies
all 132 changed/new paths, checks the six overlaps and pins both sides of
each reviewed conflict. Unexpected conflicts fail before output creation.
It preserves prepared-only files (including steering changes outside the IoT
overlay), then verifies every output byte against the planned result.

The integrated raw deletion body accepts both WDS/reset and optional RSSI
context. The ordinary wrapper retains its seven-argument ABI; the RSSI wrapper
uses the same admitted execution helper. The actual merged include passed
`check-peer-rssi-delete.c` with GCC C11 -O2 -Wall -Wextra -Werror, covering
busy/reentrant refusal, failed-body lease release, invalid inputs, normal WDS
context forwarding and exact reset serial admission. Vendor deletion is
injected; callback/DMA retirement and actual clearing remain outside that test.
The retained body still captures matched RSSI identity and appends clearing
evidence only after SET_ENTRY_NONE. Scheduler structural audit also passed on
the merged tree. Negative tests rejected modified peer hashes, modified
generator hashes and an unexpected header conflict before output creation.

Local workflow edits add peer82 selection, isolated Kbuild wiring and Linux
host/MIPS fixture checks. YAML, Python and candidate shell syntax passed;
those edits have not run in CI and must not be described as target proof.

## Remaining portability prerequisite before publication

The Linux peer preparation needs further EOL work before publishing these
workflow edits. A second concrete legacy pin was identified: the initial WDS
input is reviewed as CRLF SHA256
`9a20173fc99a049abd3ffa53e36ccd8c811acd45bfe104089f068babcf4ed958`,
whereas its exact LF equivalent is
`617391f6a2e02130c9e302edf4564f7f6bd640281b093ad448c8f52bcda0ef89`.
Unlike the now-fixed v25b pin, this is in the full peer chain. Audit all
platform-dependent generated bytes/legacy pins before enabling that chain in
Linux CI; do not weaken hash validation or claim the Windows replay proves
Linux generation. Current remote remains c0db748; integration edits are local.

## Portability prerequisite addressed locally

The 74 peer stages already write source text with explicit LF. The older
recovery dependencies instead used platform-default write_text, producing
CRLF on the reviewed Windows replay and LF on Linux. Those source/fixture
writers now explicitly preserve their reviewed CRLF output. No source pin was
removed, bypassed or broadened for the WDS case. Existing explicitly LF or
binary writers are unchanged. JSON/log metadata remains outside driver pins.

Fresh preparation after this change produced 71 candidate files identical in
bytes to the earlier replay. Its full overlay has 540 files, also byte-identical
to the prior full overlay. All 74 downstream generator hashes are unchanged;
therefore that identical input retains the existing 585-file peer receipt.
The new static regression checks explicit text-output policy through 140
generator dependencies and rejects an implicit or newline=None source writer.
LF/CRLF/corruption v25b regression still passes; Python/YAML and both changed
Bash bodies parse successfully. Linux execution remains for CI to establish.

This resolves the identified local publication prerequisite. Publish the
coherent source merge, host fixture, deterministic writers and workflow
wiring together. The standard ABI run exercises Linux generation and the
merged fixture/MIPS object. Whole-driver Kbuild still requires the separate
run_candidate_checks=true, candidate_scope=iot, iot_candidate_variant=peer82
selection after confirming no duplicate active firmware run on that commit.
