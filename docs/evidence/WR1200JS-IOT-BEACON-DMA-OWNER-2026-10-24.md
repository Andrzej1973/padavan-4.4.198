# IoT candidate: per-descriptor beacon DMA owner reset

The isolated MT7603 `RTMPHandleBcnDmaDoneInterrupt` reclaims several beacon
ring cells in one `while (TxSwFreeIdx != TxDmaIdx)` invocation. Its `bss_idx`
was initialized once before that loop. A recognized `own_mac` in one cell
could leave the index set for the next cell; if that next `own_mac` was
unrecognized, the previous BSS could receive its DMA-done state update.

`tools/iot/prepare-radio-queue-candidate.py` now resets `bss_idx` to the
invalid sentinel inside each non-null descriptor's decode block, before
reading its `own_mac`. The existing current-count/capacity guard then rejects
an unrecognized owner while ring reclamation continues. This is only an
isolated candidate fix; it does not prove hardware TxS report retirement.

Verification on 2026-10-24:

- Assembled the candidate from pinned `c25283e` source at
  `../iot-pinned-mt76x3-c25283e/mt76x3` into
  `../iot-owner-reset-declsafe-20261024/` successfully. The assignment is
  after local declarations and before reading the descriptor.
- Inspected generated `driver/common/cmm_data_pci.c`: its DMA handler has
  `bss_idx = 0xff` within `if (tmac_info)`, before own-MAC decoding and the
  `BssidNum`/`MAX_MBSSID_NUM` guard. The generated manifest records SHA256
  `8c63564789e3b949338ae4193cc6384a49fa96f31f452c55a6152b16128f12cc`
  for that file.
- `python -m py_compile tools/iot/prepare-radio-queue-candidate.py` and
  `git diff --check` passed. The first attempt against a different locally
  prepared source stopped at the pinned-source hash guard; no source was
  overwritten. A target MIPS compile of this new candidate has not run.
- A source-order check extracted the DMA handler from the previous candidate
  and the new one. It rejected the previous handler and accepted the new
  handler only when a per-cell invalidation lay between `if (tmac_info)` and
  own-MAC decoding, before the BSS bounds guard. This is a structural check,
  not execution of the target driver.

Remaining IoT gates include selective beacon DMA/TxS drain or exact report
identity, atomic ring admission, production binding, image checks and device
acceptance. No router state was changed.
