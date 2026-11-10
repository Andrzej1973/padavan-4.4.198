# Isolated non-owning TxS PID prototype

Status: host allocator/parser and long-TXD branch experiment, not an IoT lifecycle implementation.
The production driver, MCU ACK protocol and existing candidate workflow are
unchanged. This experiment must not be installed on the router.

The prototype derives the existing checked allocator, callback ledger and
claimed-slot changes from four exact pinned vendor files. It excludes wire
PID255 from allocation and returns immediately for its reports before status
lookup, removal or callback accounting. The 256-entry array remains unchanged;
usable tracked capacity becomes255, including for Main/Guest traffic.
The experimental long packet-type TXD branch selects255 only for exact
MT7603/HIF_MT/BssidNum3/BSS2 beacon/BCN-queue/WCID0/logical-PID0/Priv2. It
returns PID255 with generation0, without allocating or claiming a software slot.
The current tracked-submit guard rejects this zero generation: no new
non-owning submission mode is implemented or enabled.

The source invariant is conditional: PID255 must never own metadata, every
wire producer must respect that exclusion, and no receive path may consume it.
The current experiment checks the actual generated allocator/parser and one
selected long-TXD branch; it does not audit every transmitter/reset path or
execute the whole TMAC formatter.

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
includes source/output hashes,3072 TXD-branch scope/pool cases and the
removed temporary byte count.

Before a useful driver variant can exist:

1. Audit every wire-PID writer and reset/initialization path; logical policy
   selectors such as PID_DATA_NO_ACK are not reserved wire slots.
2. Review and target-compile the staged long-TXD route in its full formatter
   and cold-only lifecycle. The tested branch selects the non-owning PID
   before allocation; it does not replace an allocated PID or satisfy lower
   submit admission.
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

## Pacing boundary review — 2026-11-10

The current candidate already holds an exclusive ra2 producer pin across its
checked zero-DMA-cell observation and revalidation. That protects host-buffer
reuse; replacing it with the scalar DMA_DONE state would weaken the proof.
A future non-owning mode needs a separate, generation-bound BCN+BMC queue
preparation receipt consumed by one submission. It must not call this RF-IDLE.

The MT vendor AsicWaitMacTxRxIdle function simply returns TRUE. It supplies no
hardware observation and cannot fulfill a strong quiescence contract. The
upstream scoped beacon iterator is useful queue-control evidence, but its
whole tasklet also includes global CAB flush/recovery and cannot be copied as
a Main/Guest-preserving implementation. See the
[pacing review](evidence/WR1200JS-IOT-NONOWNER-PACING-BOUNDARY-2026-11-10.json).

The [wire-PID inventory](evidence/WR1200JS-IOT-WIRE-PID-WRITERS-AUDIT-2026-11-10.json)
covers textual references in450 pinned C/H files. It identifies four allocator
call sites, zero writes and PID2 short templates; it does not exclude arbitrary
raw-word writers or aliases. Those limits remain before activation.

## Executable old-report transition counterexample

The actual parser fixture also models a previously tracked ra2 beacon report
completing its non255 PID, then a Main beacon obtaining that same PID with a
new software generation. An injected old report consumes Main's new metadata.
This is a conditional host counterexample, not a claim that firmware emits
duplicates on the device. The new invariant protects reports carrying255; it
does not repair arbitrary historic non255 reports.

A zeroed software table, a fresh adapter object or a software reset is therefore
not enough to authorize the new mode. Historical tracked-report retirement
and mode activation remain explicitly unproved/unimplemented in the prototype.
