# WR1200JS IoT PCI core fence API audit — 2026-11-01

## Scope

Read-only review of the exact pinned Linux 4.4.198 source at
`c25283e915a2a00a763774dd255b14aff997285e` in the local bare source backup.
This evaluates whether generic PCI APIs can establish a terminal DMA fence for
the MT7603 remove callback. No driver source was changed and no hardware or PCI
configuration space was accessed.

Relevant source blobs:

- `drivers/pci/pci.c`: `e5beb2a5a1a11bc9b2a9df711aedb5262feb15c3`
- `drivers/pci/pci-driver.c`: `43871373e4af0851b30f318e4dbc3309715c0520`
- `drivers/net/wireless/mediatek/mt76x3/os/linux/pci_main_dev.c`:
  `eb1118e720e49741261314226a5cc9f9f6ede150`

## Findings

- `pci_clear_master()` is available and exported. It calls
  `__pci_set_master(dev, false)` and returns `void`; this clears the PCI command
  bus-master bit but supplies no readback/result and is not itself evidence
  that transactions already issued have drained (`drivers/pci/pci.c`, lines
  3145–3153).
- `pci_wait_for_pending_transaction()` is available and exported. For PCIe it
  polls Device Status `TRPND`; for non-PCIe devices it returns success without
  polling (`drivers/pci/pci.c`, lines 3420–3433).
- The underlying `pci_wait_for_pending()` ignores the return value of
  `pci_read_config_word()` and inspects `status` regardless. A failed config
  read can therefore be mistaken for a clear pending bit; it polls four times
  and returns clear/pending only (`drivers/pci/pci.c`, lines 487–509). The
  pinned MT7621 host `config_access()` path also reports `PCIBIOS_SUCCESSFUL`
  without surfacing endpoint transaction errors, as recorded in
  `WR1200JS-IOT-PCI-REMOVE-BOUNDARY-2026-11-01.md`.
- Generic PCI remove invokes the driver's `void remove()` and then clears the
  binding; the pinned core does not unconditionally call
  `pci_clear_master()` there (`drivers/pci/pci-driver.c`, lines 425–480).
- The pinned MT7603 `rt_pci_remove()` does not call either API before teardown
  (`mt76x3/os/linux/pci_main_dev.c`, lines 408 onward).

## Decision

These APIs are useful ingredients for a responsive-device path only when all
driver DMA producers are already retired and config transactions are known to
work. They do not provide a fail-closed proof for an inaccessible/surprise-lost
endpoint, and a pending-bit timeout still needs a hardware-isolation action
before owned DMA memory can be released. Do not add an early return from the
void remove callback, do not free buffers after an unverified timeout, and do
not describe `pci_clear_master()` or this helper alone as the required terminal
fence. Continue searching for board-specific, endpoint-isolating reset or
host-controller guarantees; if unavailable, this remains a release blocker.

This audit narrows the next source investigation; it does not establish
hardware behavior or runtime acceptance.
