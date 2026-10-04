# Imported router reference profiles

Imported from the user-provided local extraction of [Plumbum-13/padavan-4.4-tplink](https://github.com/Plumbum-13/padavan-4.4-tplink), on 2026-10-04. The upstream README attributes the proto-project to sereja8. Original configuration/board bytes and upstream license are retained. No Git metadata was supplied; the precise source commit is unknown. [manifest.json](manifest.json) records hashes, board definitions and provenance.

These are reference profiles from that source, not verified device support in this project. They are outside configs.build, the build overlay and boards.json; importing them does not add targets to the build matrix. Future adaptation requires matching hardware revision, flash layout, drivers, build and runtime verification.

| Board ID | SoC in template | Template |
|---|---|---|
| ARCHER-C50 | MT7620 | [config](trunk/configs/templates/ARCHER-C50.config) |
| MI-4 | MT7621 | [config](trunk/configs/templates/MI-4.config) |
| MI-R3G | MT7621 | [config](trunk/configs/templates/MI-R3G.config) |
| MI-R3P | MT7621 | [config](trunk/configs/templates/MI-R3P.config) |
| MI-R3P-PB | MT7621 | [config](trunk/configs/templates/MI-R3P-PB.config) |
| MI-R3P-SPI | MT7621 | [config](trunk/configs/templates/MI-R3P-SPI.config) |
| MI-R4A | MT7621 | [config](trunk/configs/templates/MI-R4A.config) |
| TL_C50-V4 | MT7628 | [config](trunk/configs/templates/TL_C50-V4.config) |
| TL_C50-V4-16M | See board files | Not supplied for this variant |

All supplied board.h, board.mk, kernel configs, partitions, Wi-Fi profile/SKU data and device-tree reference files are preserved under trunk/configs. Shared BusyBox/uClibc configs are also included as references, not applied to the active build. TL_C50-V4 also contains a kernel-5.15.150.config; its presence does not establish Linux 4.4 support for that configuration. The C50-16M folder contains additional device-tree experiments; they are reference data, not an approved flash map. Incidental text notes/boot logs are omitted.

License: [original LICENSE](UPSTREAM-LICENSE). Original source description: [upstream README](UPSTREAM-README.md).

No compilation was requested or performed for these profiles. Existing WR1200JS settings and active build targets are unchanged.
