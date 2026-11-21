# Initialized-adapter pre-destructor release60b

`prepare-peer-adapter-release.py` pins candidate59 controller source and inserts
`wr_iot_adapter_release_begin` before the first destructor in RtmpRaDevCtrlExit.
Candidate: `.iot-local-check/peer-adapter-release60b-20261030`.

The helper requires the terminal PCI RELEASE_CLAIMED receipt, child completion,
retiring/down radio without active work/TX/reset, software close completion,
required command/WSC worker join bits, empty registry and zero registration/
deferred owners. WSC join is required only when WSC_INCLUDED is enabled; these
bits are not evidence that every kernel timer/direct callback has joined.

After observing the terminal receipt under the transition lock, the helper
checks peer table/close/open/delete/transaction state under MacTabLock. No locks
are nested and no wait occurs. Once idle, it permanently sets the existing
table-owner poison bit as an admission fence; this bit must never be reset on
a failed release or retry. The two-lock sequence relies on RELEASE_CLAIMED being
terminal; establishing that terminal receipt from actual retirement is a
separate required binding, not something this helper infers.

Four selected strict GCC host variants passed in
`peer-adapter-release60b-targeted/result.json`:

- Actual pre-destructor helper, with and without WSC: missing terminal receipt,
  missing worker join, active delete/transaction/table owner, deferred owner,
  published reference and a writer injected between snapshots all refuse.
  Accepted claim closes ordinary table admission and cannot be repeated.
- Actual controller body and native/OS_ABL caller seams: mocked early gate
  refusal prevents every modeled destructor/free/unmap; prior result propagation
  checks remain. Actual free is mocked; actual gate is tested separately above.

The lexical audit observes result propagation and pre-destructor claim order,
but still marks release unaccepted. Current PCI remove does NOT yet produce
the terminal receipt through all required stages, so initialized release in
this candidate refuses instead of fabricating quiescence. Direct cold-probe
free paths are not covered by this initialized controller gate. Neither this
necessary refusal nor passing host tests proves complete unload/recovery.

Next: bind actual retirement receipt through work joins, child/root callback
quiescence and physical observation; establish cold-probe cleanup ownership;
verify all callback/DMA and target ABI requirements. No target/firmware build,
router changes, dispatch, commit or push. Step60 is in the preparer chain,
not freshly replayed in full; latest completed full replay remains58.
