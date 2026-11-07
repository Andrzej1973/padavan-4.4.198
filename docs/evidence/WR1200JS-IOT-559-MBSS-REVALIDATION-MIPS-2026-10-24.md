# IoT MBSS readiness revalidation: isolated MIPS candidate

[Optional GitHub Actions run 40080616642](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40080616642)
completed successfully at `3095603ca086224b33e447687b64f91862a64375`
with `boards=wr1200js` and `run_candidate_checks=true`. The ordinary ABI
and firmware runs at the same revision passed (`40079234798`, `40079234854`).

The optional `Compile isolated merged IoT MT7603 candidate` step passed.
Downloaded `iot-merged-driver-probe` to
`%TEMP%\wr1200js-iot-probe-40080616642`. Its source manifest lists 46
overlays and five prepared-source merges. `build.log` contains
`LD [M] .../mt76x3_ap.ko`; the resulting module is 5,111,688 bytes,
SHA256 `1f16748cd808837b54bbb5ec84fdacbf63fdc870b46d35c430b2794e8e106f3f`.
The uploaded ELF header shows a little-endian ELF32 relocatable MIPS32r2/o32
module. `merged-capacity.json` has 21 reviewed lock sites, 20 active
(11 SEM, nine IRQ). The unchanged kernel-config SHA256 is
`fa047c0252b38d5e9525dbbd80cd1ef8cd4564d01b384edb5d861c200177aaa9`.
The workflow's candidate source-copy/hash, lock, MIPS ELF and config checks
all passed.

This is target compilation/link of the isolated candidate containing the
new BSS-open readiness revalidation. It does not prove that every reset,
close or teardown path participates in the same transition owner; the
short-lock observer itself is a configuration check, not RF proof. Beacon
DMA admission and selective TxS retirement remain open. The candidate is
not installed in the production image, and the router was not changed.
