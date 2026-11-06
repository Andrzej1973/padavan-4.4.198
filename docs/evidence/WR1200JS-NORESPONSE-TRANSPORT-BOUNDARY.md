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

## Why a later checked command is not a sufficient fence

The same candidate's `AndesDequeueAndKickOutCmdMsgs()` drains all available
entries from the host `MCUCtrl.txq` in a loop.  `AndesMTPciKickOutCmdMsg()`
places each entry on the PCI control ring and advances its producer index;
the host-side FIFO therefore shows only submission order.  A no-response
entry carries sequence zero, while a checked entry has its own nonzero
sequence and waits for its own response.

Nothing in this host-side path states that firmware must finish a prior
no-response EDCA or slot command before it emits the later command's result.
Nor does the later result identify either prior command.  Consequently a
successful later extended-result response is not an ordered, command-specific
execution proof for the retained timing intent.  It must not retire the
EDCA/slot journal or open normal startup merely because both packets occupied
the same host control ring.

`AsicGetWmmParam()` can read the WMM MMIO fields for EDCA, but that helper alone
does not establish an ordering relation with the asynchronous firmware command
and has no counterpart for the complete slot-time tuple.  It is useful only if
a future change supplies and validates that missing command-specific ordering
contract.

The independently refreshed `nilabsent/padavan-ng` `master` source at
`c29b12da69b1593a6e8cf65cd43767fc99bb6386` (checked 2026-11-06) retains the
same MT7603 `CmdEdcaParameterSet()`/`CmdSlotTimeSet()` no-wait initializers and
the same channel/TX-power extended-result path.  It supplies no alternative
timing ACK or documented ordering fence; this comparison is corroboration,
not device evidence.

This is source evidence only.  It does not establish target compilation,
final-image contents, radio behavior, or device runtime.  No router operation
occurred.
