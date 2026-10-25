# IoT v39 isolated MIPS compilation: build #595

GitHub [build #595](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40207139904) completed successfully on commit `3d6c602`. Both `Build WR1200JS firmware` and `Compile isolated merged IoT MT7603 candidate` steps succeeded. The preceding automatic firmware #594 (`40205825840`) and Band Steering ABI run `40205825793` also passed on the same commit.

Downloaded the `iot-merged-driver-probe` artifact from #595. Its `build.log` ends with `LD [M] .../mt76x3_ap.ko` and a successful `make` exit. The artifact contains `mt76x3_ap.ko` (5,200,856 bytes; SHA-256 `2be70edfa1dd9eaa9402560000111f89657d456134072e91cc4b6d5e874a2039`). `mt76x3-elf.txt` identifies it as ELF32 little-endian MIPS, relocatable, O32, MIPS32r2. The merged-source manifest records 58 overlay paths and five reviewed prepared-source merges.

The build log also reports one kernel `modpost` section-mismatch warning without failing. This result verifies **target compilation of the isolated candidate**, not its packaging in the ordinary firmware image, runtime module load, radio behavior, lifecycle safety, IoT isolation or device acceptance. The manifest intentionally retains `target_compiled=false`, `production_installed=false` and `runtime_verified=false` as candidate-source claims; the separate CI artifact is the compilation evidence.

Next: address the outstanding PCI remove/adapter lifetime and deferred-close ownership gates before installing the candidate in a firmware image. Then verify image contents and perform separately authorized, recoverable on-device acceptance. No router state was changed for this result.
