# Isolated MT7603 TIM admission for IoT close

The pinned driver has a second producer of `Q_IDX_BCN` besides the regular
beacon sender. `ap/ap_nps.c:51-80` calls `HAL_KickOutMgmtTx` for a TIM frame
under `BcnRingLock`. `common/cmm_data_pci.c:1514-1523` calls
`APMakeAllTimFrame` from the pre-TTTT interrupt path, which iterates every
configured BSS. The original TIM sender did not check the selected BSS's
`bBcnSntReq` under that lock. The checked `MBSS_Close` candidate revokes
that request under the same lock. Without a TIM gate, the close path could
sample an empty beacon DMA ring and the TIM sender could add a new packet.

`tools/iot/prepare-radio-queue-candidate.py` now overlays `ap/ap_nps.c`
in the isolated candidate. The TIM sender validates the BSS index before
dereference and, for secondary BSSs, checks `bBcnSntReq` under `BcnRingLock`
before publishing. The unchanged main BSS path remains available. Its
vendor `PNDIS_PACKET *pkt` declaration was also corrected to
`PNDIS_PACKET pkt`: the actual typedef is already `void *` in
`include/os/rt_linux.h:221`.

Local checks against pinned source `c25283e`:

- Candidate assembly completed into `../iot-tim-admission-v2-20261024/`.
- Generated C fixture compiled with host GCC `-std=c11 -Wall -Wextra -Werror
  -O2` and passed bounds, close-before-lock, close-at-lock, peer and main
  BSS cases.
- Complete source-text lock inventory passed: 515 pinned files, 46 overlays,
  32 verified source blobs, 21 lock sites in nine units (12 SEM, nine IRQ).
- Python syntax and `git diff --check` passed.

This is an isolated candidate only. The tests inject locks and packet
submission. No MIPS compile of this revision or RF/device test has run.
The full ring-admission, TxS retirement, adapter lifetime and production
integration gates remain false. The router was not changed.
