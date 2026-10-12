# WR1200JS test build 222

[Run 38263576527](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38263576527) and preceding build 221 completed successfully. Build 222 uses commit `b337efa95800db6f16eac5d60f7acb00c6ab937b`. Compilation logs include `FWBLDSTR=222` and `FWREVSTR=b337efa9`; runtime WebUI display is not yet verified.

Downloaded final artifact `WR1200JS_4.4.198.9-222_b337efa9_TEST` contains:

- `WR1200JS_4.4.198.9-222_b337efa9.trx`, 13133567 bytes, SHA-256 `271d9e7b81ede2100e1f701397ac0fcef583ffdc21c91c9954794b87678b8ad2`.
- `wr1200js.config`, SHA-256 `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.
- `SETUP_WR1200JS.txt`, 17850 bytes, SHA-256 `6f8a3099fc8a8d3ad6438e2b6889f89aa7f48e8fc8f4ba3d2b9f364069994558`. Its UTF-8 text identifies build 222, suffix `222_b337efa9` and the full commit.

The device remains on the earlier `100_shmily` image. This artifact verification does not prove boot, ZRAM activation, client-list rendering, DNS lifecycle, management-access preservation or sustained stability on hardware.

## Follow-up collection-stage diagnosis

[ABI 408](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38267269097) completed successfully for commit `6337794`, which adds the networkmap/radio stage to the unavailable-device response and its HTTP-hook tests. Full build 223 is pending. The actual failing stage on the installed older image remains unknown.
