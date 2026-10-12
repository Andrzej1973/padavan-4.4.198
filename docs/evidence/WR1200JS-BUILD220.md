# WR1200JS test build 220

[Run 38261975445](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38261975445) completed successfully at commit `932424a34ef13498803aa2ec20840250666e6547`, including the ZRAM page-alignment correction. The independent native lifecycle regression at the same commit also passed. Image verification does not prove physical-router operation.

Downloaded final artifact `WR1200JS_4.4.198.9-100_TEST` contains exactly:

- `WR1200JS_4.4.198.9-100.trx`, 13133615 bytes, SHA-256 `d5d16aa2910cc1a5c2ddec03f618f60e20d50922914204ce6c1f4a997b93646f`.
- `wr1200js.config`, SHA-256 `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.
- `SETUP_WR1200JS.txt`, 17709 bytes, successfully decoded as UTF-8, SHA-256 `a02a69ad0ef39f44404cfd012d5290b4502df915d8deba3c9ae1451cf493d4af`.

This build predates the workflow-number/SHA version identity. Its inherited filename must therefore be identified together with this run and checksum. Build 221 introduces image/UI identity; build 222 also identifies the generated guide. Their results are pending at this observation.

Router SSH is reachable after the owner restored the tunnel, but available noninteractive authentication failed. No flash, restart or device configuration change was performed. ZRAM activation, DNS lifecycle, sustained stability and management-access acceptance remain unverified on hardware.
