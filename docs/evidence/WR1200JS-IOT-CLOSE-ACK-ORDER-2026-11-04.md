# Checked close ACK ordering audit

Fresh full source generation through all peer82, MBSS, ROM-ready and owned-OFF
layers succeeded. Installed owned-OFF ASan/UBSan, allocator/release/lifetime/
destructor suites and combined installed MBSS worker/submit/stop-join passed.
Initial audit lookup used the old public close name after the executor had
renamed it; source checks had already passed. Corrected lookup was replayed
against fresh generation, not treated as a driver failure or reused stale tree.
Current common/rtmp_init_inf.c SHA256:
c3994ebc9c9cee0271634f0a98970427ffe7350034d61dde60f8ee8d9e5f8f77.
Inside static wr_iot_checked_close_body, body-relative lines show:
144 APShutdown; 168 RtmpNetTaskExit; 197 mgmt exit; 213 RTMPDisableRxTx;
217 DISABLE_TX_RX; 218 interrupt disable; 239 checked radio OFF; 283 MCU exit.
The software-only AP helper has ZERO calls from this checked body. Thus OFF
cannot yet rely on its ACK path; full module compilation is not proof of a
workable shutdown sequence. Do not bind ordinary callbacks or install it.
The candidate already retains MacTabLock; APShutdown still retires WDS lock
and other AP resources, so moving its call
or RX join alone risks active RX users. RX1 accepts MCU events during HALT,
but shared schedule block/join and early global interrupt disable still remove
that route. Next split AP command/producer stop from destructive resource
cleanup, preserve MCU RX1 until owned ACK, then join RX/DMA/IRQ before freeing.
Respect existing stage receipts and retain uncertainty on partial side effects.
No quick reorder, gate bypass, sequence clear or reopen is authorized by this
source audit. Normal and feature configurations require separate validation.
Phase-specific generated tree 1440444792 bytes removed; earlier replay tree
also auto-removed. This frees WSL filesystem scratch, not a claim that Windows
VHD/C: allocation shrank. Inputs and owner materials preserved; no router use.
CI 742/743 and ABI 658 remain queued at latest observation; no duplicate runs.
