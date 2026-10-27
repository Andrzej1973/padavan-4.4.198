# Isolated IoT v42 target compile: firmware run #634

- GitHub Actions run: `40527671413`, completed successfully at commit
  `0641d962155baedf4c1441dca686ee1d71a7c677`.
- Pinned Padavan source: `c25283e915a2a00a763774dd255b14aff997285e`.
- The `Compile isolated merged IoT MT7603 candidate` step succeeded. The
  `iot-merged-driver-probe` artifact was downloaded into local
  `artifacts-634-v42/` and inspected, not installed.
- `target-compile-result.json` reports `candidate_variant=v42`,
  `target_compiled=true`, `production_installed=false`,
  `runtime_verified=false`.
- Actual `mt76x3_ap.ko`: 5,225,808 bytes; locally calculated SHA256
  `46ef52aea556529ca4f711f267c5308f11978b223197dd2c2e85ce595d3cab3c`,
  matching the result manifest. `mt76x3-elf.txt` reports ELF32,
  little-endian MIPS, relocatable, O32/MIPS32r2.
- `beacon-producer-binding.json` confirms `producer_gate_bound=true` but
  `recovery_owner_bound=false` and `pci_release_gate_bound=false`.
- The same run produced ordinary image artifact
  `WR1200JS_4.4.198.9-634_0641d962_TEST`; it does not contain the isolated
  v42 module. No on-device installation or runtime test occurred.

This closes the **target compilation** question for v42 only. Next required
driver work is a joined deferred MBSS recovery owner, an effective PCI
release fence and proof that late DMA/TxS reports cannot outlive teardown.
Keep the candidate outside production until those conditions are bound and
verified. The successful CI run is not an IoT acceptance result.
