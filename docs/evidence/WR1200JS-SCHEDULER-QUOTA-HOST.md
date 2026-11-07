# Isolated scheduler quota checks — 2026-11-06

The unbound `prepare-mcu-boot-scheduler-quota.py` layer copies the SDK scheduler
body, preserves the ordinary SDK function, and redirects only the private
bootstrap wrapper. It rejects all-ones/zero PCI quota observations and refuses
group subtraction unless a positive group0 remainder exists. The positive
remainder requirement is a conservative candidate policy, not yet device
validated. A preflight checks this arithmetic before the first scheduler
register write; the later subtraction guard remains defensive. Unsupported
non-AP or non-LMAC calls refuse before MMIO. Remap acquisition/restoration
still precedes quota validation and requires producer serialization.

Executed against `/tmp/wr-scheduler-run-jpoYun`:

- `check-mcu-boot-sdk-quota.py`: actual generated SDK body, injected MMIO,
  ASan/UBSan, E1/E2, BSSID1..16, AMSDU off/on, quota pages0..160, 128/256-byte
  pages, all-ones rejection, group0 boundary and remap restoration: PASS.
- `check-mcu-boot-scheduler.py`: native/FPGA wrapper gates and executed
  SDK-failure mutation: PASS.
- Full generated-tree SHA256 inventory and preserved original SDK-body hash:
  PASS.

Fresh generation using the CI layer sequence additionally passed SDK quota,
wrapper, owner and Method1 fixtures, the full inventory and duplicate-install
refusal. Unsupported AP/mode tests assert zero register writes; insufficient
quota tests assert only the two remap writes, with no scheduler writes.

The fixtures model register access; they do not prove hardware serialization,
register effects, MIPS compilation, ROMFS inclusion or router behavior. The
checked copy is not connected to MCUSysInit or normal admission. Remap producer
serialization and failure/promotion integration remain required. The peer82 CI
recipe now stages the quota layer and fixture; target results are pending.
Fresh fixture temporary directories are removed
automatically; the generated candidate is retained for unfinished work.

Remap audit found direct users in `common/cmm_data_pci.c:MonitorRxPse`,
`common/cmm_mac_pci.c:PSEWatchDog` (calls MonitorRxPse before its reset gate),
and `hw_ctrl/cmm_asic_mt.c:MtAsicGetThemalSensor` (called from AP/config/info
paths). GPIO, EFUSE, chip init and reset paths also access the register.
No claim of exclusion follows from the scheduler ticket alone: callers and
their active-bootstrap admission must be traced before integration.
