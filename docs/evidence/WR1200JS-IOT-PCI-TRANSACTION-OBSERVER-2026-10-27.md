# WR1200JS IoT PCI transaction observation candidate — 2026-10-27

Pinned Linux 4.4 source at `c25283e915a2a00a763774dd255b14aff997285e`
exports `pci_wait_for_pending_transaction()`. It checks PCIe Device Status
`PCI_EXP_DEVSTA_TRPND` through `pci_wait_for_pending()` (four reads, with
100/200/400 ms sleeps), but `pci_wait_for_pending()` does not inspect the
return from `pci_read_config_word()`. It can therefore treat an invalid or
uninitialized read as a successful observation. The MT7621 host's config
accessor has no separate hardware-completion result, so even a checked
software return is not a full bus proof.

The saved read-only PCI dump shows both Wi-Fi functions `14c3:7603` and
`14c3:7662` as PCIe v2 endpoints with capability at `0x70`. Their Device
Status at `0x7a` was `0x0010`, where Transaction Pending bit `0x0020` was
clear at that instant. This is a snapshot, not a stop or drain test.

Added host-only `tools/iot/pci-transaction-observer.h`. It requires a
readback showing PCI bus mastering disabled and four bounded Device Status
samples. It rejects config read errors, all-ones data and a persistent
Transaction Pending bit. `tools/iot/check-pci-transaction-observer.c` passed
GCC C11 `-Wall -Wextra -Werror -O2` fault injection for active bus master,
failed reads, all-ones reads, pending timeout and eventual clear.

The initial observer neither cleared bus mastering nor proved that device DMA rings,
callbacks, IRQ handlers, work items or posted PCI writes have retired. It is
now an additional host-only input to `adapter-release-gate.h`, but is **not** a
physical-quiescence receipt. Before production binding, the path needs a checked bus-master
disable/readback sequence, an independently proven ring and callback drain,
and retained ownership on any uncertain outcome. No driver, image or router
state was changed in this step.
# Release gate follow-up, 2026-10-27

Release input is now `wr_iot_pci_observation { result, radio_epoch }`, not a
bare enum. The host gate requires a nonzero current radio epoch and exact
epoch match, so a previously clear observation cannot be reused after a
radio lifecycle change. Both direct and PCI-retirement fixtures reject a
stale observation; four strict GCC C11 fixtures passed. This is a validation
contract only: the production owner must capture the epoch under the common
adapter lock before and after hardware observation, reject a changed epoch,
and keep all bus-master writers fenced through resource retirement. Merely
tagging a result with the current epoch after an unlocked observation would
not satisfy this contract.

Added a separate host-only final-remove operation,
`wr_iot_pci_disable_master_and_observe()`. It validates the PCIe capability
offset and callbacks before touching state, calls a supplied bus-master clear
operation, then checks PCI_COMMAND and bounded Transaction Pending reads.
The fault fixture rejects a failed or silently ineffective clear, a missing
callback and an invalid capability offset; strict GCC C11 compiled and passed.
This must not be called on ordinary Wi-Fi close, because that path may reopen
the same PCI device. There is no production `pci_dev` callback binding yet,
and a successful read still depends on an adapter-wide fence against all
later bus-master writes and independent DMA/IRQ/work retirement.

The observer now re-reads PCI_COMMAND immediately after seeing Transaction
Pending clear. Fault injection covers bus master re-enabled during the poll
and a failed final read; strict GCC C11 test passed. This does not prevent a
later re-enable. The future production owner must fence every bus-master
writer across this observation and resource retirement.

Source-chain audit of the isolated v39 candidate found another blocker:
`RTMPDrvClose` is `VOID`; `rt28xx_close` discards it and returns zero;
`CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN` discards that close result; and
`MainVirtualIF_close` returns zero. The PCI remove callback ignores the
`RtmpPhyNetDevExit` Boolean and proceeds to `RtmpRaDevCtrlExit` and root
netdev free. Consequently a radio-off failure cannot reach the final release
decision. Converting only one function to a checked return is insufficient:
the shared close and remove paths must carry one adapter-owned failure state
through these callers and prevent release on uncertainty. A `void` remove
callback cannot use a simple early return as a complete recovery strategy.

The host-only `adapter-release-gate.h` and `pci-retirement-owner.h` now require
`WR_IOT_PCI_TX_CLEAR_OBSERVED` as an additional input before release can be
claimed. Invalid PCI reads, active bus master and persistent Transaction
Pending reject release in the host fixtures. Four GCC C11 fixtures passed with
`-Wall -Wextra -Werror -O2`: PCI transaction observer, adapter release gate,
PCI retirement owner and auxiliary close recovery owner. `git diff --check`
passed. No production driver binds this input yet. A clear PCI Transaction
Pending bit is not proof that DMA rings, IRQs, callbacks or work are retired;
the existing `physical_quiescent` input still lacks a verified producer.
Next bind checked bus-master disable/readback and ring/IRQ/work drain to one
adapter-owned lifetime path, with fail-closed handling on read or drain error.
