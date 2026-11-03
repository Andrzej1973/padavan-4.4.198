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
