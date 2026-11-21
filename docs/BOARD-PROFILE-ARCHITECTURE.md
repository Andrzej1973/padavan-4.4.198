# Board profile architecture — Phase 1, 2026-11-08

The admission registry is [boards.json](../boards.json). Package selection in
[configs.build](../configs.build/) does not by itself supply a board port.
The stable selector [board-catalog.py](../tools/board-catalog.py) delegates
validation to [board_catalog.py](../tools/repository/board_catalog.py).

| Board | SoC/profile evidence | Image admission | Missing evidence |
| --- | --- | --- | --- |
| WR1200JS | MT7621, Linux 4.4, board files, SPI16M DTS, MT7603E/MT7612E | Existing recipe retained | Physical acceptance; outstanding IoT gates |
| Mi Mini | MT7620 profile and isolated candidate | Disabled | Complete kernel/driver integration, image and runtime |
| Mi-4 | MT7621 package profile | Disabled | Exact board recipe, hardware manifest, image and runtime |
| Xiaomi 4A Gigabit | Future audit only | No registry entry | Exact revision, SoC, radios, flash, calibration and boot contract |
| Xiaomi 4 / 3G / other MT7621 | Donor references only | No additional target | Independent hardware identification and full board evidence |

Do not conflate 4A 100M with Gigabit, or equate R3G/R3Gv2 with an unidentified
retail revision. Establish whether Mi-4 and Xiaomi 4 name the same board before
creating another ID. Shared MT7621 does not establish NAND/SPI geometry,
Factory offsets, Ethernet wiring, GPIO polarity or USB availability.

## Component boundaries

Common package tools and checks belong in tools; shared SoC kernel code comes
from the pinned base. Board-specific DTS, GPIO, Ethernet, flash/image layout,
calibration offsets and radio selection stay in the exact board overlay.
Driver changes remain pinned patches/candidates with explicit application;
never infer runtime support from CONFIG or copied board headers.

WR1200JS retains its existing board.h, board.mk, kernel config and two DTS
files. The validator checks their presence, product/SoC selection and exact
existing partition map. It neither supplies missing kernel includes nor
replaces compiled DTB and image checks in the assembled build.

## Admission procedure

1. Identify physical revision and document source provenance and licenses.
2. Add a pending profile to the existing schema; do not enable the recipe.
3. Verify board/kernel/driver/defaults/backend paths and capability evidence
   using the existing [capability manifests](../tools/wifi-capabilities/boards/).
4. Prove DTS/image format, partition bounds, calibration preservation and
   board-specific Main/Guest/IoT inclusion, isolation and IPv4/IPv6 policies.
5. Add and verify an isolated recipe before enabling image admission; require
   device evidence separately before calling a board supported.

IoT inclusion is mandatory for every admitted release board; runtime default
OFF is a different setting. See the [IoT contract](IOT-WIFI-IMPLEMENTATION-CONTRACT.md).
The current validator deliberately admits only the existing WR1200JS recipe.
A future board requires extending validation with evidence, not flipping a
boolean or inheriting WR1200JS flash constants.
