# WR1200JS test build 239

[Run 38430582676](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38430582676) completed successfully for commit `3d1e53b1f1833e8b5d8fd12f162449c9fcca53a2`. The image Stubby QEMU resolution step and ZRAM image/dependency step both report success.

Artifact `WR1200JS_4.4.198.9-239_3d1e53b1_TEST`, id `11832285889`, was downloaded to `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build239-final`. SHA256 values below were independently computed from downloaded files:

- `WR1200JS_4.4.198.9-239_3d1e53b1.trx`: 13,139,795 bytes; `6a15fe74692c9896b32e965d3a445cbe4c3149705396f47d0b4c6c63dbc2317f`.
- `SETUP_WR1200JS.txt`: 20,777 bytes; `7cc394a28b0602c0b0e69007dead054a194da4179524300d6d8f456d5469fe85`.
- `wr1200js.config`: 11,249 bytes; `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.

The guide includes `239_3d1e53b1`. The downloaded profile matches `configs.build/wr1200js.config` byte for byte and explicitly sets `CONFIG_FIRMWARE_INCLUDE_SQM=n`.

This image includes VPN handshake/interface refresh, DNS process refresh, periodic ZRAM observation and bounded source transfer retries. It predates the later ZRAM guide expansion and unconditional effective-profile CAKE exclusion gate; its requested profile still excludes CAKE/SQM.

No physical flashing, reboot, configuration migration, browser execution or router stability verification was performed for this image. QEMU checks are not physical device evidence. The full port objective remains unfinished.
