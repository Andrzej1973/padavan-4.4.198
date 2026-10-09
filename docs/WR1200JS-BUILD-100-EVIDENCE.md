# WR1200JS build 100 — verified build evidence

Firmware workflow [37967838212](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37967838212) completed successfully, as did build 99 and ABI workflow 37967838205. Firmware code commit: `3a5a21ae440bfbd283ab3dae67aa841c5301d63c`.

Downloaded final artifact `WR1200JS_4.4.198.9-100` contains exactly:

- `WR1200JS_4.4.198.9-100.trx`: 13,085,926 bytes.
- `wr1200js.config`: 11,091 bytes.

TRX SHA256: `3770164b8e761c0b3d5618cacdf76fe15f4b0dbd869dc4e47895e44288c162bf`.

Requested config selects WR1200JS, Wi-Fi2 driver 4.1, Wi-Fi5 driver 3.0 and WR Band Steering. Size optimization remains commented; CAKE is excluded. This establishes requested selections, not device behavior or independent proof of every image feature.

The RC service guard linkage regression that broke builds 91/92 is corrected and the complete image now links/builds. Native isolated namespace tests validate the tracked restart controller with injected daemon callbacks, retained recovery/retry and bounded file/kernel snapshots. Process presence is still a provisional readiness check; real DNS/DHCP protocol readiness, lease preservation, IoT activation and device runtime verification remain incomplete. This document does not authorize flashing or establish recovery of the remote management tunnel.

CI still publishes diagnostic and aggregate artifacts in addition to this minimal firmware/config artifact. Final delivery must remove redundant user-facing downloads after diagnostics are no longer needed.
