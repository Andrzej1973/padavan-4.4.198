# Isolated non-owning TxS PID prototype

Status: host allocator/parser experiment, not an IoT lifecycle implementation.
The production driver, MCU ACK protocol and existing candidate workflow are
unchanged. This experiment must not be installed on the router.

The prototype derives the existing checked allocator, callback ledger and
claimed-slot changes from four exact pinned vendor files. It excludes wire
PID255 from allocation and returns immediately for its reports before status
lookup, removal or callback accounting. The 256-entry array remains unchanged;
usable tracked capacity becomes255, including for Main/Guest traffic.

The source invariant is conditional: PID255 must never own metadata, every
wire producer must respect that exclusion, and no receive path may consume it.
The current experiment checks the actual generated allocator/parser only;
it does not audit or change every transmitter and reset path.

Run on the existing preserved exact vendor Git tar, without extracting a full
firmware tree:

```sh
python3 tools/iot/check-noowner-pid-prototype.py /path/to/padavan-4.4-c25283e-git-exact.tar --report /path/to/host-report.json
```

The ASan/UBSan fixture executes actual extracted functions for all256 allocator
cursors, 255-slot exhaustion, duplicate-report inertness, out-of-range PID
refusal, cancellation, ordinary callback completion and generation exhaustion.
The same fixture rejects the predecessor which can allocate255. Linux locks,
hardware and transport are injected, so this is not concurrency or device proof.
The [recorded result](evidence/WR1200JS-IOT-NOOWNER-PID-HOST-PROTOTYPE-2026-11-10.json)
includes source/output hashes and723730 bytes of removed temporary output.

Before a useful driver variant can exist:

1. Audit every wire-PID writer and reset/initialization path; logical policy
   selectors such as PID_DATA_NO_ACK are not reserved wire slots.
2. Route only intended ra2 beacons to the non-owning PID before allocation.
   Do not replace an already allocated PID and strand its owner.
3. Establish a cold-start transition or retire all old tracked non255 ra2
   reports. Ignoring255 does not make old reports with other PIDs safe.
4. Replace TxS-dependent beacon pacing with a justified DMA/queue lifecycle.
   Simply changing DMA_DONE to IDLE or clearing HostTxS is insufficient.
5. Prove RF/BCN/BMC/AC stop and teardown safety, preserve Main/Guest, then
   perform target compilation and separately authorized runtime tests.

The [pinned upstream comparison](evidence/WR1200JS-IOT-UPSTREAM-NOOWNER-PID-CANDIDATE-2026-11-10.json)
motivates the distinction between a non-owning status ID and disabling status
generation. It is not a firmware specification for the vendor driver. No full
late-TxS, safe reopen or complete-IoT claim follows from this experiment.
