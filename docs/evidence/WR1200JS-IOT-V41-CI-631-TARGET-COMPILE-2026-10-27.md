# Isolated IoT v41 target compile, run #631

- Run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40511894915
- Workflow input: WR1200JS, `run_candidate_checks=true`, `candidate_scope=iot`,
  `iot_candidate_variant=v41`; head `3868270ad1f5105c1a728762e0d2e1a2df3b5656`.
- The select, build, firmware ZIP and downloads jobs completed successfully.
  Ordinary firmware #630 and Band Steering ABI #582 had already passed on
  the same head before this optional run was dispatched.
- Artifact `iot-merged-driver-probe` ID `12739320162` was downloaded locally
  into `.iot-local-check/build631-probe`. Its `target-compile-result.json`
  says `candidate_variant=v41`, `target_compiled=true`,
  `production_installed=false`, `runtime_verified=false`.
- `mt76x3_ap.ko` is 5,211,800 bytes; local SHA256
  `16ceb7287df44514e3d02daa801ec2d79c8dc257013e1412b57c92d6cc8134d9`
  matches the manifest. `readelf` reports ELF32 little-endian MIPS,
  relocatable, O32/MIPS32r2. The source manifest records 58 overlay files
  and one resolved prepared-tree text conflict.
- `mbss-stop-binding.json` describes the narrower source-binding stage and
  reports `checked_stop_bound=true`, `recovery_owner_bound=false`,
  `pci_release_gate_bound=false`. Its own `target_compiled=false` field is
  scoped to that binding stage; the top-level compile result and module
  establish the later isolated target compile.

This verifies only the isolated candidate compile. The normal firmware image
still uses the pinned driver. Deferred recovery ownership, callback and
adapter lifetime, PCI release, beacon DMA/TxS quiescence and router runtime
remain unverified; the candidate is not ready to flash.
