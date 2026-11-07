# IoT candidate: selective beacon DMA software snapshot

The pinned MT7603 candidate now has `WrBeaconDmaOutstanding(ad, BssId)` for
PCI AP builds. It scans the shared beacon ring under `BcnRingLock`, decodes
each pending packet's `own_mac`, and returns 1 when the requested BSS still
owns a DMA cell. Invalid indices, a short packet, an unknown/out-of-range
owner, a second packet in a cell, or a mismatch between occupied cells and
ring indices returns -1. A zero means only that this software snapshot saw
no pending descriptor for that BSS.

The checked MBSS close candidate calls the DMA snapshot after `MBSS_Close`
and before its existing TxS software snapshot. Pending DMA retains the
stage-2 close ticket for retry; uncertainty moves the ticket to the existing
fail-closed stage. The main and guest BSSs are not globally cleaned up by
this query. The two snapshots are not one atomic hardware barrier, so late
TxS reports, producers outside the reviewed admission path, reset races and
adapter lifetime remain open. The candidate manifest keeps
`beacon_ring_admission_atomic=false`,
`selective_bss_txs_retirement_proved=false`, `production_installed=false`
and `target_compiled=false`.

Verification on 2026-10-24:

- The unified candidate assembler completed from pinned `c25283e` source
  into `../iot-dma-close-apguard-20261024/`.
- A MinGW host fixture compiled the **extracted generated C function** with
  `-std=gnu11 -Wall -Wextra -Werror -O2` and passed empty, main/IoT/guest,
  unknown and out-of-range owner, short packet, extra packet, ring mismatch,
  invalid index and lock-release cases.
- The extracted checked MBSS open/close host fixture passed pending DMA and
  uncertain DMA paths in addition to its existing TxS cases. Python syntax
  and `git diff --check` passed.
- Generated `common/cmm_data_pci.c` SHA256:
  `344f9ebe14a27217c2f09b8bc5f97bff63d1efc13a7551a6b293877aed506860`.

No target MIPS compile of this revision, firmware image check or router
runtime test has occurred. No router state was changed.
