# PCI remove cannot refuse driver-core unbind

Pinned source: c25283e915a2a00a763774dd255b14aff997285e.

`drivers/pci/pci-driver.c:429` invokes the VOID driver remove callback.
After it returns, lines432-433 release platform IRQ routing and clear the
PCI driver pointer; line455 drops the PCI device reference. Independently,
`drivers/base/dd.c:683-689` calls the bus remove, then releases devres and
clears device driver/data. Physical removal can subsequently free PCI resources
in `drivers/pci/remove.c:44`. These are distinct paths; do not claim every
resource is freed on every ordinary unbind.

The candidate's early returns preserve its own memory/netdev references but
cannot veto these core actions. A module or netdev reference alone does not
prove PCI mappings, IRQ routing, callbacks or DMA remain usable afterward.
The new bounded pre-retirement retry improves a continuation opportunity;
it does not solve terminal detach when the retained operation still fails.

Required next implementation: separate ordinary radio/interface close (which
may refuse and remain attached) from unavoidable bus removal. Before returning
from bus remove, fence all new access, stop hardware/DMA/IRQ producers using
verified device-specific operations, join callbacks, and detach or quarantine
software owners without future hardware access. Preserve exact reference
accounting. Audit physical loss separately, where MMIO cannot be assumed safe.
Do not add unbounded waits, fake success, forced frees, kernel-core vetoes or
relax guards merely to pass removal. Prove ordering and failure paths against
actual source, target build and separately authorized device tests.

Status: source-confirmed production blocker, not an observed device crash.
No router changes or PCI unbind experiments were performed.

## Follow-up: target MMIO and PCI config receipts

The candidate path's `RTMP_IO_WRITE32()` resolves through
`common/rtmp_init.c` to `_RTMP_IO_WRITE32` in `include/os/rt_linux.h`. The
target PCI branch checks `bPCIclkOff`, endian-converts, and calls `writel()`;
the accessor is void and does not read back. The isolated v40 source gate now
pins this accessor shape against the configured target header. This is an
ordered accessor path, not a device-specific acknowledgement of all four
`AsicSetMacTxRx()` writes.

Target Linux 4.4.198 `pci_channel_offline()` only tests whether `error_state`
differs from `pci_channel_io_normal`. The MT7621 `config_access()` writes the
PCR address/data registers and unconditionally returns `PCIBIOS_SUCCESSFUL`
after the sequence; no timeout or endpoint completion status is surfaced.
Therefore `pci_wait_for_pending_transaction()` or config readback through this
host path cannot be treated as a reliable surprise-removal receipt without a
separate host-controller/device contract. The existing PCI pending-transaction
observer remains only a candidate guard for a responsive endpoint; it cannot
resolve inaccessible-device loss.

Pinned target references: [`pci_channel_offline()` and PCI config API](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/include/linux/pci.h), [`MT7621 config_access()`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/arch/mips/pci/pci-mt7621.c). Source review only; no config transaction, reset, unbind, or device access was performed in this follow-up.

## Stop primitive audit

The reproducible `tools/iot/audit-terminal-stop-primitives.py CANDIDATE OUTPUT`
records source hashes and reviewed limitations in
`WR1200JS-IOT-TERMINAL-STOP-PRIMITIVES-2026-11-01.json`. MT7603's DisableTxRx
hook is NULL; StopDmaRx/Tx reject HIF_MT. The void RTMPDisableRxTx chain drops
the DMA setter result, whose success has no post-write receipt. Interrupt
masking neither observes write completion nor joins the IRQ handler. Merely
moving these calls before a remove refusal does not implement safe terminal
shutdown. Changed source shapes remain unproven and need renewed review.

## Follow-up: MT7621 host reset controls are not a teardown receipt

Read the complete pinned `arch/mips/pci/pci-mt7621.c` from source revision
`c25283e915a2a00a763774dd255b14aff997285e` in the local bare source backup.
The driver defines PCIe ports 0, 1, and 2, but maps all three external
`GPIO_PCIE_PORT*` names to GPIO 19 (lines 67-77). During platform probe it
asserts reset for all three root ports, pulses the common GPIO19 PERST_N line,
then deasserts the configured port resets and the shared PERST_N line (lines
621-703). Its later per-port root-controller reset/clock handling only disables
ports whose links are absent during that same probe (lines 780-807); this file
does not provide a runtime port-reset API for a PCI endpoint driver's remove
callback.

This rules out treating GPIO19 PERST_N as an isolated reset for one Wi-Fi
endpoint: the target source deliberately shares it across the configured
ports. The separate root-port reset bits are not a DMA-drain receipt either;
the source provides no remove-time contract for in-flight transactions,
interrupt fencing, or reset completion. Do not toggle either control from the
MT7603 remove path based on this source alone. Establish board wiring and a
controller-level isolation/drain contract before considering such a control
for any endpoint. Source-only investigation; no register or router operation.

Source locator: pinned bare repo
`/home/andrzej/padavan-build/firmware-source-backup/padavan-4.4.git`, object
`c25283e915a2a00a763774dd255b14aff997285e`, file
`trunk/linux-4.4.x/arch/mips/pci/pci-mt7621.c`.

## Independent board-tree cross-check — 2026-11-01

The OpenWrt WR1200JS board DTS independently places its two radio endpoints
under MT7621 PCIe ports 0 and 1. Its inherited MT7621 PCIe node defines one
parent `reset-gpios = <&gpio 19 GPIO_ACTIVE_LOW>` for the controller; the
per-port children describe separate RC reset/clock controls, not separate
endpoint PERST GPIOs. This corroborates the pinned Padavan host source above:
GPIO19 is shared, so it is not an isolated reset for one radio. The OpenWrt
DTS is independent board-tree evidence, not a Padavan build input or a
substitute for schematic/PCB-revision inspection.

The newer upstream MT7621 host driver was checked as a design comparison. It
parses per-port reset controls and applies RC/endpoint reset during host
initialization; its platform `remove` only releases reset handles. It exposes
no endpoint-driver DMA/IRQ drain or isolation API. This newer source is not a
transplant candidate for the pinned 4.4.198 target and does not establish the
electrical effect of reset on this board.

Primary source references:

- [WR1200JS board DTS, pinned OpenWrt staging revision](https://git.openwrt.org/openwrt/staging/hauke/tree/target/linux/ramips/dts/mt7621_youhua_wr1200js.dts?h=84cb0f7ace73fad15e29e1d74c469b37f90b334d)
- [MT7621 common DTS PCIe reset and port nodes](https://github.com/lede-project/source/blob/master/target/linux/ramips/dts/mt7621.dtsi#L2656-L2746)
- [Upstream MT7621 host driver, pinned source revision](https://gbmc.googlesource.com/linux/%2B/d19ea320d3029a12993c671f4815bf6c02ae0727/drivers/pci/controller/pcie-mt7621.c)

Decision unchanged: do not toggle GPIO19 or a per-port RC reset from the
MT7603 remove callback, and do not treat either as a DMA terminal fence. A
board-wiring plus controller-level isolation/drain contract is still missing.
Read-only source review; no hardware or router operation.

## Effective-config and sysfs removal path — 2026-11-01

The WR1200JS kernel config has `CONFIG_MT7603E_RLT_WIFI=m`, `CONFIG_MODULES=y`,
and `CONFIG_SYSFS=y`; `CONFIG_HOTPLUG_PCI` and `CONFIG_MODULE_FORCE_UNLOAD` are
disabled. This does not make the PCI remove callback unreachable. In the
pinned Linux 4.4.198 source, `pci-sysfs.c` includes the writable per-device
`remove` attribute in `pci_dev_type`; its handler calls
`pci_stop_and_remove_bus_device_locked()`. That path reaches `device_release_driver()`
and the PCI bus `remove` callback before clearing the binding and releasing
devres. `rt_pci_remove()` is void, so an early return cannot veto this sequence.

The generic driver `unbind` attribute is also created unless the driver sets
`suppress_bind_attrs`; writing it calls `device_release_driver()`. Suppressing
that attribute alone would not hide PCI's separate per-device `remove` file.
Thus `CONFIG_HOTPLUG_PCI=n`, normal (non-forced) module policy, or hiding only
driver `unbind` cannot substitute for a correct remove protocol. No sysfs
operation or device unbind was performed.

Exact target inputs and source: `overlay/padavan-4.4/trunk/configs/boards/WR1200JS/kernel-4.4.x.config`;
pinned commit `c25283e915a2a00a763774dd255b14aff997285e`, files
`drivers/pci/pci-sysfs.c` (`dev_remove_attr`, `remove_store`,
`pci_dev_hp_attr_group`, `pci_dev_type`), `drivers/pci/remove.c`,
`drivers/pci/pci-driver.c` (`pci_device_remove`), `drivers/base/bus.c`
(`unbind_store`), and `drivers/base/dd.c` (`__device_release_driver`).
The source chain confirms the software entry point; it does not show that a
DMA/IRQ terminal fence exists.

The pinned MT7603 `rt_pci_driver` initializer registers `.remove` but no
`.shutdown` callback. The effective WR1200JS config also has `# CONFIG_KEXEC is
not set`. Linux `pci_device_shutdown()` invokes a driver shutdown callback only
when one is present; its optional KEXEC-only bus-master clearing path is not
enabled here. Therefore ordinary reboot/shutdown is a separate system-reset
path and supplies no driver-level remove fence. It must not be used as evidence
that sysfs unbind/device removal is safe. MT7603 source blob:
`eb1118e720e49741261314226a5cc9f9f6ede150`; PCI core blob:
`43871373e4af0851b30f318e4dbc3309715c0520`.
