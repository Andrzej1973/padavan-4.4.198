# Whole deletion57 — local source binding and host checks

## Superseded: candidate rejected by WDS recovery contract

The three checks below were too narrow to establish compatibility with the
existing WDS recovery caller. A later contract check reproduced an error:
after ordinary deletion returns a retained NOT_WRITTEN result, the table owner
is retained, but the existing WDS resume API supplies zero table serial. Its
retry is refused before the original body can validate its saved checkpoint.
`check-peer-delete-resume-contract.c` compiled with strict GCC and exited1 on
candidate57, printing `body calls=1`. This is a reproduced regression, not a
passing acceptance check. The mock models the original NOT_WRITTEN/resume
contract; it does not execute real hardware or the whole vendor deletion body.

Step57 has been removed from `prepare-peer-retirement-chain.py`. Its source,
candidate and test evidence remain preserved for review. The current chain
ends at56; latest completed full replay remains54. Do not publish/install57
as a compatible deletion implementation. Next design: a separate synchronous
deletion execution lease/count that blocks close/reset for the complete body
without replacing existing per-entry WDS retention/recovery ownership. Preserve
parent-reset serial handling and test this resume contract before acceptance.

The original report below is historical and its chain-membership statement is
superseded by this rejection.

Pinned preparer `prepare-peer-normal-delete.py` creates
`.iot-local-check/peer-normal-delete57-20261030` from candidate56. The original
private deletion function is renamed `wr_iot_mac_delete_entry_body` unchanged;
its callers now pass through `wr-iot-peer-normal-delete.inc`.

Ordinary deletion reserves an exclusive table serial under MacTabLock after
checking executor idleness. That serial spans the entire original body,
including unlocked TX-burst/protection/capability tails. The body receives the
serial so its existing table gate does not reject its own reservation.
Successful ordinary completion releases it; failed ordinary completion retains
it conservatively. Recovery from that retained failure is not implemented.

Deletion invoked by an owning table reset validates and forwards the parent's
exact serial without acquiring or releasing a second reservation. Invalid
adapter/address/WCID is rejected before reserving. Both close executors now
reject an unrelated active table owner before APShutdown, while permitting a
retry of their own stored close serial. Raw reset already checks ordinary table
admission and therefore refuses the deletion reservation.

Three strict GCC C11/O2/Wall/Wextra/Werror selected checks passed in
`.iot-local-check/peer-normal-delete57-targeted/result.json`:

- Wrapper with mocked original deletion body: ordinary release, active insert
  refusal, stale parent serial refusal, parent ownership preservation, invalid
  WCID and retained ordinary failure.
- Extracted actual close bodies/wrappers: unrelated active table owner refuses
  both paths before APShutdown; earlier partial-close and retry tests pass.
- Actual reset fragment: active table reservation preserves a pending request
  without executing raw reset; prior count/contention/retirement tests pass.

This is not execution of the full original deletion body, actual kernel locks,
callback/DMA joins, target compilation or on-device verification. Broader
extractors must be updated to follow the renamed private body before full
regression can be claimed. Step57 is in the chain; latest completed full replay
remains54. Follow-up: retained ordinary-delete recovery, all writer/callback
lifetime and adapter release. No router changes, firmware build, manual dispatch,
commit or push in this step.
