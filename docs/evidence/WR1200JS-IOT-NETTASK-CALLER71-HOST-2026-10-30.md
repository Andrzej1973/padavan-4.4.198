# Network task init caller71 and composition review

Extended prepare-nettask-init-failure-check.py with optional --caller-source.
It extracts the actual RtmpNetTaskInit status branch and err2-to-return tail
from common/rtmp_init_inf.c. Only orphan err1/err0 labels are removed; the
fallthrough operations remain. Every enabled OS_ABL task allocation failure
now traverses this caller tail. Host assertions require partial init cleanup,
idempotent network Exit, then exactly one hif_sys_exit. Base and extended
strict GCC variants passed. This is a selected caller slice, not whole driver
initialization, IRQ synchronization or resource lifetime proof.

rt28xx_open source review: FALSE init goes to err, issues WR_PEER_OPEN_FAIL,
then IRQ_RELEASE and returns -1; MBSS/WDS/APCLI/Monitor creation below the
successful init branch is skipped. Failure of unrelated init stages, all
asynchronous callbacks and outer ownership acceptance still need broader
verification. No on-device operation occurred.

Full candidate70 host attempt1 stopped at an obsolete APShutdown verifier
anchor expecting the old void NetTaskExit call. Updated the anchor to the
call expression and changed shared host stub to return successful status.
The injected failure check retains its explicit override. The 12 targeted
APShutdown/legacy-close/shared-close/release-gate variants passed afterward.
The rejected65 fixture anchor was kept compatible, without accepting draft65.

The suite now detects scheduling helpers and includes base/extended tasklet
checks, OS_ABL allocation failures with caller tail, and injected close exit
failure. A full replay was started separately; consult its actual result,
not this preparation note, before claiming success. Prepared chain still
ends64 until replay and coherent fresh preparation are accepted.

## Completed replay

full70-host-attempt3-20261030/result.json records passed=true, full_suite=true,
72 variants, target_compiled=false and runtime_verified=false. This invocation
loaded the suite before the additional injected-exit test was registered;
that test passed separately in full70-exit-injected71-20261030/result.json
(1 variant). Thus72+1 host results exist, not a single73-variant report.
Fresh whole-chain preparation70 was started with all four67–70 transforms;
its live handle/result must be checked before treating preparation as done.
