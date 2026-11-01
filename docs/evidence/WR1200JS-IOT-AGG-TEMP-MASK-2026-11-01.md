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
