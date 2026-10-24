# IoT ABI gate after firmware build #552

Firmware run [#552](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40066799333)
on `7df3e9c22722b2039222bb35874ec3054c2ddac2` completed successfully.
The matching [ABI run](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40066799319)
failed in `inspect-driver-abi`, step `Check private IoT request mailbox`.
The first actionable diagnostic was:

```text
audit-full-beacon-locks.py: error: Candidate coverage changed:
(515, 45, 31, 9, 21, 12, 9); expected (515, 45, 31, 9, 20, 11, 9).
```

The additional SEM lock site is `WrBeaconDmaOutstanding` in generated
`common/cmm_data_pci.c`, introduced with the per-BSS beacon DMA snapshot.
It does not add a source unit or change the IRQ count. The pinned-source,
manifest-hash, and candidate-overlay checks passed before the shape check.
Updated the expected shape in `tools/iot/audit-full-beacon-locks.py` to
`(515, 45, 31, 9, 21, 12, 9)` after inspecting that generated site.

Local targeted replay against pinned source `c25283e` and assembled
`iot-dma-close-apguard-20261024` candidate passed:

```text
Verified 31 source blobs; found 21 lock sites in 9 units
```

The output is `../iot-dma-close-apguard-20261024/beacon-lock-audit-552.json`.
`git diff --check` passed. This fixes a stale source-inventory gate, not a
driver synchronization issue. Mixed SEM/IRQ use, selective TxS retirement,
target compilation of this candidate, and device runtime remain unresolved.
