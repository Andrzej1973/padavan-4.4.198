# WR1200JS IoT isolated MT7603 candidate: optional MIPS build

[GitHub Actions run 40077253251](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40077253251)
completed successfully on PR head `6eec863556927a58e35f74b4dec8a81e6819def6`
with `boards=wr1200js` and `run_candidate_checks=true`. The
`Compile isolated merged IoT MT7603 candidate` step and its diagnostics upload
both passed. The ordinary firmware and ABI runs for this head had already
passed: `40075915187` and `40075915089`.

Downloaded artifact `iot-merged-driver-probe` to the local temporary directory
`%TEMP%\wr1200js-iot-probe-40077253251` and inspected its files. The source
manifest reports 46 overlays and five prepared-source merges. Its
`target_compiled=false` field describes the source assembly manifest before
the subsequent build; it is not an assertion about the completed run. The
workflow verified the copied candidate source against its SHA256 manifest.

`build.log` has `LD [M] .../mt76x3_ap.ko`. The uploaded 5,108,316-byte module
has SHA256
`57807c92ead518e072a684f58cc9e067863d2c24f49216260f19d976c4b3e01c`.
The uploaded `mt76x3-elf.txt` identifies ELF32 little-endian, relocatable,
MIPS32r2/o32. `merged-capacity.json` contains nine reviewed lock units,
21 sites, 20 active (11 SEM, nine IRQ), complete per-unit macro/activity
evidence, and no effective `MULTI_CORE_SUPPORT`. The corrected exact lock
gate passed. The workflow's module existence, MIPS readelf, source-copy and
unchanged kernel-config checks all completed successfully. The saved config
SHA256 matches `config-before.sha256`:
`fa047c0252b38d5e9525dbbd80cd1ef8cd4564d01b384edb5d861c200177aaa9`.

This proves isolated candidate assembly and target module compile/link plus
the named CI gates. It does not install the candidate into the production
firmware or prove beacon DMA admission, selective TxS retirement, adapter
lifetime, RF behavior or IoT operation on the router. Those flags remain
false or unverified. No router state was changed.
