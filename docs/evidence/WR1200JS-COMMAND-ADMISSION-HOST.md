# PCI command worker admission — 2026-11-06

The isolated command-admission layer adds one control reference per dequeued
command before dispatch, under the helper's existing transition lock. Bootstrap
reservation therefore refuses an already admitted worker; a worker that runs
after reservation skips the dispatch body. Other chips retain their existing
dispatch path. The original queue cleanup/free path runs even when denied.
Denied normal commands are discarded, not replayed; subsequent normal startup
integration must audit required configuration commands before enabling IoT.

MLME's deferred reset drain is moved outside dispatch admission, after reference
release, and runs for a periodic command even if reset_pending denied dispatch.
NIC_NOT_EXIST and HALT gates remain in force. Reset uses its existing RTNL,
peer executor and radio transition protocol; this change grants no reset or
firmware readiness proof. No short lock spans the command or reset body.

Fresh isolated generation passed:

- Generated command envelope with injected body/cleanup/admission: enabled and
  disabled feature guards, DMA_RESET_SUPPORT on/off, other-chip bypass, NIC and
  halt, admitted and denied dispatch, exactly-once cleanup, reset after release
  and reset suppression for NIC/halt: ASan/UBSan PASS.
- Existing control-wrapper and actual bootstrap transport/admission fixtures:
  PASS; complete generated-tree SHA256 inventory: PASS.
- After preserving NIC/halt reset guards, regenerated from input and reran
  command-envelope checks and inventory: PASS.

This is host/source evidence. Target compilation, image and device runtime
remain unverified. The peer82 CI recipe includes the new layer and fixture.
Fresh temporary candidates (~14MB each) and binaries auto-removed.

Additional remaining audit input: GPIOGetValue is used by WSC_HDR_BTN macro in
include/wsc.h, so searches limited to C call sites miss a real macro path.
Trace WSC timer admission before declaring GPIO excluded. EFUSE and chip/PSE
init ordering, ATE/QA and numeric remap accesses also remain outstanding.
