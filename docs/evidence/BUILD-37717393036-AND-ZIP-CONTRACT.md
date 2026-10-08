# Isolated kernel link and user ZIP evidence

Inspected GitHub Actions REST records and downloaded artifacts on 2026-10-08.

## Successful full workflow

- Run 37717393036: completed, success.
- Source: 77ced24ec596bb5b899694b562a1a8dbf5271ca4.
- Firmware job 113116952188: success.
- Normal WR1200JS firmware, isolated steering drivers, isolated complete rc and
  isolated MT7621 systick/NVRAM kernel link steps: success.
- Firmware ZIP job 113123750816: success.
- Downloads job 113123750912: success.

The isolated kernel artifact 11524943589 contains the actual
nvram_linux.o disassembly, source/object hash records and linked kernel symbols.
Pinned drivers/nvram/Makefile builds nvram_linux.o; nvram_linux.c includes
nvram.c. The earlier check for standalone nvram.o was incorrect.

- Patched nvram.c SHA256:
  8a978e2e7a31fce4f8ec7ab1b541d16b52599e16746c008d6e02603298d0a2c7.
- Compiled nvram_linux.o SHA256:
  1c480603bff3f45236b719ae185f42c4cebadf08d3dcebd0a8d78a24218487ee.
- Linked vmlinux SHA256:
  b0750d1ff7fd246013609c4bff7ab637c666484aa93778599836cf7c14c7fd9a.
- Linked symbol: ffffffff812df93c T _nvram_getall.
- Within the _nvram_getall disassembly, instruction 2402ffe4 loads v0 with -28
  (ENOSPC). Earlier extracted-function fixtures cover the overflow boundary.

This proves isolated target compilation/linking of the overflow-reporting
candidate. It does not establish installation in the normal image or router
behavior. This revision predates the Wi-Fi capture/radio integration changes and
the current CAKE exclusion; its success is not evidence for those later changes.

## Actual minimal ZIP contents

Artifact 11508016138, WR1200JS_4.4.198.9-100, from successful run 37673562400
was downloaded and inspected. It contains exactly these two files:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| WR1200JS_4.4.198.9-100.trx | 13247836 | f77182d68d3c2c9d2986203545f05b5731870c2cb92d6f8f496e7e10c8fd197d |
| wr1200js.config | 10814 | fc09e14cd5b14f8b2c648baf91ccd6f1d7a0d9a9ef16dcfc66ac1c09a4a8156b |

The configuration bytes exactly match configs.build/wr1200js.config at that
run's source revision 5d515a13d263769f7e913277ed39350bb9d4eace. No third file or
nested archive was found. This proves the minimal per-router download contract,
not current firmware feature selection or readiness to flash remotely. This
older archive includes the earlier SQM request and is not the new CAKE-free build.
