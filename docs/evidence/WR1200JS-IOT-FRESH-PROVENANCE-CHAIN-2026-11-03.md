# Fresh recovery generation with close provenance

Repository revision: 80b1080. Executed:

`python3 tools/iot/prepare-current-recovery-chain.py <pinned-mt76x3> <new-output>`

Input was the preserved pinned mt76x3 tree under
`/tmp/wr-peer82-triage/pinned/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3`.
No historical reviewed_open comparison argument was supplied.

Process exited 0. preparation.json records returncode 0 for each preparation
step. The generated later/corrected/include/interface-reference.h contains
both close_uncertain_reason and close_verified_stage. This establishes fresh
queue/later source generation with current provenance assets rather than
reusing an old generated queue. It does not establish full peer assembly,
current-wrapper host execution, target compilation or device runtime.

Temporary phase directory was inventoried (74,956,746 bytes) and removed
after the process completed and the receipt/header were checked. No generated
candidate or binary retained. Original pinned input remains for unfinished work.

## Full fresh peer replay

At revision a13c2c1, repeated current recovery generation from the same pinned
input, then prepare-full-driver-overlay.py using later/corrected and
later/v24c-composition.json, followed by prepare-peer-retirement-chain.py.
Session 80907 exited 0 and reported final candidate
peer/radio-on-retirement-admission. This confirms the entire fresh source
chain, including the corrected WDS input pin, without substituting an old
generated recovery overlay. It is still source-generation evidence only.

The launching script inventoried 1,133,658,867 bytes in its phase directory
and deleted that directory after successful completion. No new source build
trees or binaries were retained.
