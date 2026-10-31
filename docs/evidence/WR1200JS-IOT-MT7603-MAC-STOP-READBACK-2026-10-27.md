# MT7603 checked stop: MAC TX/RX readback candidate — 2026-10-27

## Bounded TX dequeue wait in isolated checked close

The inherited `RTMPDrvClose` waits without a bound for each
`DeQueueRunning[i]` before AP shutdown and tasklet/IRQ/ring teardown. In the
isolated MT7603 checked-close generator, the corresponding checked path now
allows at most 1000 one-millisecond polls per ring. A timeout marks
`shutdown_stage=3` under the transition lock and returns failure before AP
shutdown, IRQ release or ring free; retry with the same ticket is rejected.
The legacy `VOID RTMPDrvClose` path is unchanged and remains an integration
blocker. The generated exact-function AP/PCI host fixture exercised a stuck
dequeue, terminal receipt, no resource release and no automatic retry; strict
GCC C11 `-Wall -Wextra -Werror -O2` passed. This does not prove actual timer
duration, producer retirement or target MIPS behavior. The adapter lifetime
owner must retain the device on this failure, and driver removal must not
ignore it.

The pinned MT76x3 source at
`c25283e915a2a00a763774dd255b14aff997285e` defines
`ASIC_MAC_RX=2`, `ASIC_MAC_TXRX=3`, `MT_ARB_SCR_TXDIS=BIT8` and
`MT_ARB_SCR_RXDIS=BIT9`. In `hw_ctrl/cmm_asic_mt.c`,
`AsicSetMacTxRx()` writes `ARB_SCR` and returns `TRUE` without reading it
back. The existing isolated `wr_iot_mt_radio_off_checked()` validated only
the RX-disable bit before draining TX/RX and sending the MCU radio-off
command. After the MCU command it checked PDMA but not the MAC TX-disable bit.

Updated `tools/iot/prepare-mt7603-checked-off-candidate.py`: at stage 3,
after the MCU command and before disabling PDMA, it requests MAC TX/RX off
and reads `ARB_SCR`. It refuses to advance unless both disable bits are seen
and the read is not all ones. This order retains TX until the MCU command has
completed; an uncertain MCU result still remains terminal for that attempt.
The stage-3 MAC operation may be retried without replaying the MCU command.

Updated the exact generated-body host fixture
`tools/iot/check-mt7603-checked-off.py` with the pinned constant values and
negative cases for a silently ineffective MAC write and invalid register
readback. The fixture compiled with `gcc -std=c11 -Wall -Wextra -Werror` and
passed. `python -m py_compile` and `git diff --check` passed.

This is still an isolated source candidate. The fixture does not model real
MMIO ordering, MCU/DMA interaction, in-flight PCI transactions, IRQ/work
retirement, target MIPS compilation or router behavior. MAC and PDMA
readback alone do not establish safe PCI/adapter resource release. Keep the
candidate out of the production driver until the complete terminal close
contract and target/device gates are satisfied.

## Source follow-up: DMA release boundary

In the preserved v39 MT7603 source, `hw_ctrl/cmm_asic_mt.c` function
`wr_iot_mt_poll_txrx_empty()` samples `MT_WPDMA_GLO_CFG` and waits for
`TX_DMA_BUSY` and `RX_DMA_BUSY` to remain clear. It does not inspect ring
descriptor ownership, DMA mapping lifetime, or completion of PCI transactions.
`AsicSetWPDMA()` writes the register and returns success without a write
readback; the isolated checked-stop candidate adds a later readback of enable
and busy bits, but this is still a register observation rather than proof of
in-flight transaction completion.

The inherited `common/rtmp_init_inf.c` close path logs a failed
`RT28xxPciAsicRadioOff()` result and continues through IRQ release and
`RTMPFreeTxRxRingMemory()` (or `RTMPResetTxRxRingMemory()` when
`RESOURCE_PRE_ALLOC` is selected). `os/linux/pci_main_dev.c:rt_pci_remove()`
also ignores the Boolean `RtmpPhyNetDevExit()` result before freeing the
adapter. The isolated candidate must replace these unchecked release edges
with one owned completion path, including callback/IRQ/work retirement and a
separate physical DMA receipt. A clean MAC/PDMA readback alone must never set
`physical_quiescent` in `adapter-release-gate.h`. This was source inspection;
no driver, image or router state was changed.
