# IoT optional build: MIPS module link and merged lock gate

Run [40074321999](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40074321999)
used `boards=wr1200js`, `run_candidate_checks=true` at
`1a15f6e4f6b8f5c50e6c4c24a915e56c8f7f336c`.
The normal firmware build and ABI for this commit had already passed in
`40073309681` and `40073309606`.

The optional step assembled 46 candidate paths, made five prepared-source
merges and ran `make ... vmlinux modules`. Its `build.log` contains
`LD [M] drivers/net/wireless/mediatek/mt76x3_ap/mt76x3_ap.ko`, confirming
MIPS candidate compilation and module link. A modpost section-mismatch
warning also appeared; the build continued. The step failed after that link
at the workflow's exact merged beacon-lock count gate; readelf/copy/hash
checks located after that gate did not run. The downstream `downloads` failure
is a consequence, not an independent driver error.

The downloaded `iot-merged-driver-probe/merged-capacity.json` reports nine
units, 21 total lock sites, 20 active sites (11 SEM, nine IRQ), complete
per-unit flags and site-activity evidence, and no effective
`MULTI_CORE_SUPPORT`. The one inactive SEM site is at
`common/cmm_mac_pci.c:1490`; the new active SEM site is `ap/ap_nps.c:81`.
The workflow still required 20 total/19 active/10 SEM/nine IRQ. Its exact
gate now requires 21/20/11/9, retaining the complete flags, activity and
single-core checks. The corrected predicate passed locally against the
downloaded CI JSON; `git diff --check` passed.

This establishes source assembly plus MIPS module compilation/link for this
candidate. The corrected gate, ELF inspection, final artifact verification,
production installation and router runtime still require later evidence.
No router state was changed.
