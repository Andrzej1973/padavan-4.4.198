# Owned synchronous configuration transport — 2026-11-06

The isolated layer routes the actual MAC/RF multiple-register write builders
through a task/ticket-owned allocator and sender while boot_active is true.
Their ordinary route remains AndesAllocCmdMsg/AndesSendCmdMsg. Message tags
capture all five ticket fields; the raw SDK allocator zeroes the message before
tags are assigned, so ordinary messages do not acquire a configuration tag.

Admission requires config state1/current task, the matching firmware/scheduler
receipts and frozen context, one message, no concurrent sender, the reviewed
SET command/extension, need_wait/need_rsp, response length32, no retransmission,
and the PCI kickout implementation. The core checked-command gate recognizes
only this tagged reviewed shape. Oversized/zero-count bootstrap builder input
refuses before multiplication/allocation. No new asynchronous command is admitted.

The checked result remains private to the message and is copied by existing
raw transport before queue transfer/free. The new sender never reads msg after
transport consumes it. After a successful checked response it waits up to5s for
message destruction/TX-done drain, then revalidates context after releasing its
sender lease. Timeout retains the outstanding message and marks uncertainty;
it never force-frees pending hardware work. Valid owned allocation failure,
rejected tagged messages and transport errors prevent silent phase completion.

Host evidence (ASan/UBSan):

- Actual owner, allocator/sender, SDK AndesInitCmdMsg, extracted core admission
  condition and actual MAC/RF builder bodies execute together. Hardware/ACK
  transport, locks, task references and waits are injected.
- Foreign task/ticket, duplicate constructor, allocation failure, unsupported
  command/direction/response flags, retransmit refusal, transport failure,
  consumed-message lifetime and ordinary routing: PASS.
- Delayed TX-done completion drains successfully; timeout retains the message,
  count and uncertainty until an injected later consumer completes: PASS.
- Earlier CI fixture sequence passed through all preceding fixtures. The new
  policy-test formatting warning was fixed, then regenerated transport/owner/
  parser/direct-RX tests passed. Complete SHA inventory and the closed outer
  init gate were checked. Temporary candidates (~14MB each) auto-removed.

The peer82 recipe stages this layer/test; target compilation is pending. Init
does not yet call config_begin/finish, and the outer bootstrap refusal remains.
Other required commands, no-response semantics, safe checked-ID budget/epochs,
abandoned-owner cleanup, full configuration readback, data promotion and repeat
lifecycle are still required. This is a real builder routing step, not complete
configuration, hardware DMA acceptance or device runtime verification.
