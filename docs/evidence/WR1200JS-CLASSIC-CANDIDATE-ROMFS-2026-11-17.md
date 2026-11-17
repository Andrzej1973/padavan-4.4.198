# Classic configuration in the isolated IoT image

The pair manifest now requires complete typed edit/view source metadata and
hashes that metadata alongside its existing driver/RC/HTTP lifecycle inputs.
No missing or truthy-but-untyped capability can silently pass pairing.

After isolated binary/module ROMFS staging, CI adds only
`www/Advanced_IoT_Content.asp` and `www/classic-iot-config.js`. An existing page
must equal the known pending template; an absent page can be created. Existing
scripts, linked destinations, changed pages and incomplete metadata refuse.
All unrelated ROMFS entries and existing page permissions are compared before/
after staging. This page edits desired configuration; it has no activation
control and does not establish working Wi-Fi/DHCP/isolation.

The existing complete SquashFS extraction comparison includes these new assets.
Only after it succeeds does the Classic report mark TRX content verified and
record the image SHA256, after rechecking the exact staged asset hashes.
Main firmware ROMFS is never edited by this candidate stage.

Host tests completed exit0: `check-package-candidate-pair.py`,
`check-stage-candidate-romfs.py`, `check-classic-config-romfs.py`.
Shell syntax and scoped diff checks passed. These use synthetic ROMFS/ELF
inputs and prove no actual MIPS image or browser/router acceptance.

Required next evidence: GitHub exact-source target build and candidate TRX
reports, independent image review and rendered Classic form testing. Draft
Ukrainian labels still require localization work before release.
