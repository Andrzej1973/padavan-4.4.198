# No-response MCU transport boundary — source evidence

The retained MT7603 SDK candidate (`aux-remove-close-v39`) sends EDCA (`0x27`)
and slot-time (`0x28`) with `need_wait = FALSE`, no response buffer and no
callback.  This is visible in `mcu/andes_mt.c` in `CmdEdcaParameterSet()` and
`CmdSlotTimeSet()`.

`AndesSendCmdMsg()` puts such a message on `MCUCtrl.txq` and returns after
`AndesDequeueAndKickOutCmdMsgs()` has attempted the PCI kickout.  Because
`need_wait` is false, it assigns sequence zero; it does not wait on
`ack_done`, inspect `wr_iot_response_done`, or inspect a firmware result.

The PCI TX completion callback in `mcu/andes_core.c` moves a no-wait message
from `kickq` to `tx_doneq`, and the bottom half frees it.  That event releases
the host-side command buffer after transport completion.  It has no response
queue entry, callback, result field, or command-specific state proving that
the MCU consumed or applied EDCA/slot-time.

Therefore neither a successful `AndesSendCmdMsg()` return nor `tx_done` is a
firmware execution receipt for these commands.  A later implementation may
only clear the retained EDCA/slot intents using a documented command response
or another command-specific, ordered and validated execution proof.  It must
not relabel DMA/TX completion as ACK.

This is source evidence only.  It does not establish target compilation,
final-image contents, radio behavior, or device runtime.  No router operation
occurred.
