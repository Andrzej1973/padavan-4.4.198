# Owned no-response register writes — 2026-11-06

The isolated layer routes actual CmdAccessRegWrite and CmdRFRegAccessWrite
through configuration ownership during bootstrap. Ordinary paths are retained.
Builder flags and command values are checked against the SDK before patching:
SET, no wait, no response, no callback/storage and zero response length. The
private sender admits only these reviewed shapes or the prior checked writes.

These messages remain unchecked. SDK dequeue assigns sequence 0 when need_wait
is false; this path does not claim an ACK or consume a checked response slot.
The existing bounded TX-done/message drain still applies. Delayed completion
can return submission success; timeout retains outstanding message/uncertainty.

Each admitted no-response write increments a retained unconfirmed-effects
counter before transport. It is not decremented on TX success or failure.
Counter overflow refuses before hardware. Config finish now refuses success
while this counter is nonzero, even if all TX messages completed. There is no
readback-clear API yet; inventing an ACK or resetting the counter is forbidden.
Future readback must prove the requested configuration before permitting finish.

Fresh generated ASan/UBSan tests execute actual SDK initialization, actual MAC
and RF no-response builders and actual owner/transport. They pass immediate
and delayed TX drain, timeout retention, unresolved-effects finish refusal,
overflow refusal, plus prior synchronous transport/owner/direct-RX checks.
Hardware, waits, tasks and transport are injected; this is source/host evidence.
Complete generated inventory matches the manifest; the outer bootstrap init
refusal remains present. Temporary candidate (~14MB) and executables auto-removed.

The peer82 recipe stages the layer and existing expanded fixtures. Target
compile and runtime are pending. Configuration-owner init binding, remaining
commands, readback, ACK budget/epochs, error cleanup, data promotion and repeated
lifecycle remain incomplete. No successful IoT activation is claimed.
