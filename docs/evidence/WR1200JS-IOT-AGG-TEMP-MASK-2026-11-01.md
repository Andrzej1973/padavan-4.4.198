# AGG_TEMP bit preservation and remaining serialization audit — 2026-11-01

Candidate only; production_installed=false; runtime_verified=false.

The generated RTS protection path in hw_ctrl/cmm_asic_mt.c used
`Value &= (0<<1);`: zeroing the full register rather than clearing bit 1.
The final generator now uses `Value &= ~(1U << 1);` exactly once.
The unchanged predecessor source is SHA256 pinned by the generator.

Executed checks:
- Whole prepare-peer-retirement-chain replay succeeded in /tmp/wr-iot-agg-full-chain.
- Strict production/RSSI source composition succeeded in /tmp/wr-iot-agg-full-merged.
- check-radio-off-send.py extracted actual generated mask into C; ASan/UBSan
  passed all 65536 low-bit patterns for upper words 0, 0x1234, 0xffff, 0x8000.
  The existing checked-send allocation/failure/success fixture also passed.
- Actual cmm_asic_mt.c compiled successfully with captured WR1200JS MIPS flags
  in /tmp/wr-iot-target-tu-nug6a699; command preserved as
  cmm_asic_mt-agg-command.json and output cmm_asic_mt-agg.log.
  This reuses captured rt_linux flags with TU paths/basename adapted; it is
  not independently captured hardware-TU Kbuild provenance or a full module link.

All source AGG_TEMP accesses in this candidate were inventoried:
- hw_ctrl/cmm_asic_mt.c:254/257 and 283/286: RTS workaround bit-1 set/clear.
- Same file:6172/6174 and 6179/6181: MTPciMlmeRadioOn upper-word clear.
- Same file:6437/6439 and 6444/6446: radio-off upper-word set.
- common/cmm_mac_pci.c:3077/3079: PciMlmeRadioOn upper-word clear.
- common/rtmp_init_inf.c:529/531: station-mode initialization upper-word clear.

The mask repair guarantees sequential bit preservation only. These eight
read/modify/write pairs do not share an explicit local lock. Caller-side
serialization has not yet been proved. An RTS stale read can still overwrite
an intervening radio-off upper word. Do not describe this patch as resolving
that race. Before adding a lock, prove adapter initialization/free boundaries,
IRQ/process call contexts and lock order for every caller; include startup
and station-mode paths rather than protecting only the two new candidate sites.
CPU locking cannot serialize firmware-owned changes by itself.

The LOAD_FW_ONE_TIME checked-off refusal stays intact. No register readback
has been accepted as firmware completion. Terminal PCI detach, DMA/IRQ joins,
full target-module build and device acceptance remain open.

CI664/run41276229051 passed on37a26e973000903fcf99c1c1779373953c013594;
it predates these changes. No router commands or production installation.

## Caller and transport audit follow-up

Current merged source locates transition-lock allocation at common/rtmp_init.c337,
after ring allocation and before adapter publication. Free at
os/linux/rt_profile.c1746 explicitly assumes entry quiescence and references
already retired; this source comment is not proof those preconditions hold.
MtCmdAsicUpdateProtect is dispatched by common/rtmp_init.c2850 command handling.
MlmeRadioOn in common/mlme.c2995 delegates to PciMlmeRadioOn, which clears
AGG_TEMP before its RADIO_OFF early-return and then delegates to MT on-path.
Thus locking only MTPciMlmeRadioOn would miss an earlier write.

Normal PCI RTMP_IO_READ32/_RTMP_IO_WRITE32 macros in include/os/rt_linux.h
perform conditional readl/writel based on bPCIclkOff; they contain no shared
RMW lock. When clocks are off, the normal read yields zero and write is skipped.
A CPU lock alone would not establish hardware availability, successful writes,
or protect a clock-state transition unless that transition participates too.
No force-I/O macro substitution is authorized by this audit.

Published coherent batch through5601556fa880554492eb679b4ed30c7383ef76d2;
remote ref independently matched. New ordinary CI runs on this exact SHA:
firmware41277434431 and ABI41277434460 were both in_progress when checked.
No duplicate candidate dispatch or interrupting push while those runs execute.

## Current-target clock clarification

Five real candidate units were preprocessed using captured/adapted MIPS flags:
cmm_asic_mt, cmm_mac_pci, rtmp_init_inf, rtmp_init and rt_rbus_pci_drv.
Direct bPCIclkOff assignments remaining are only zero (one each in
cmm_mac_pci, rtmp_init and rt_rbus_pci_drv). No TRUE assignment was observed.
See CLOCK-ASSIGNMENT-AUDIT JSON. Thus the earlier generic clock-transition
concern is not a demonstrated active-target transition and should not become
an invented prerequisite. Aliased writes/external components and real clock
state are not covered. Shared RMW serialization and adapter lifetime still
require proof; no change to LOAD_FW_ONE_TIME refusal follows from this result.

## Isolated shared-lock candidate

Final generator now adds adapter-owned wr_iot_agg_temp_lock, allocated beside
irq_lock in RTMPAllocAdapterBlock and freed in RTMPFreeAdapter beside existing
IoT locks. Eight exact source RMW blocks use IRQ lock/unlock; original RTS
conditional writes remain inside the lock and unlock occurs outside each
condition. No wait, MCU command, nested transition lock or polling is added
inside a critical section. Existing caller locks, IRQ masking, adapter pinning
and terminal cleanup still require broader validation; this does not repair
unavoidable terminal PCI cleanup or permit MMIO after hardware removal.

First merge failed closed because allocating next to transition_lock changed
a separately pinned RSSI conflict. Moving allocation beside existing irq_lock
preserved the reviewed conflict; no merger hashes/checks were weakened.
Full chain and strict merge /tmp/wr-iot-agg-lock-merged2 passed.

New check-agg-temp-lock.py extracts all eight actual C blocks. ASan/UBSan
fixture checks MMIO occurs under the injected lock, conditional unlock,
all 65536 bit-clear inputs with high word set, and concurrent low/high bit
set loops using pthread mutex substitution. This is not actual spinlock/IRQ
execution, device MMIO or adapter lifetime proof. First host fixture compile
missed the ULONG typedef; adding the host typedef corrected that harness error.

All five actual modified source TUs compiled with captured/adapted MIPS flags:
cmm_asic_mt, cmm_mac_pci, rtmp_init_inf, rtmp_init, rt_profile.
Command/log/results remain in /tmp/wr-iot-target-tu-nug6a699/*agg-lock*.
Single field/allocation/free inventory passed. Existing checked-send ASan/UBSan
and mask regression passed. New test is wired into optional candidate CI;
YAML and complete modified shell step bash syntax passed. Full target-module
Kbuild, runtime concurrency, terminal retirement and firmware acknowledgement
remain unverified. Default LOAD_FW_ONE_TIME refusal is unchanged.
