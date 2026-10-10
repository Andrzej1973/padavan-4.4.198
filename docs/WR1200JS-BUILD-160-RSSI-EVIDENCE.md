# WR1200JS build 160: production RSSI inclusion

[Build 160](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38060549622) completed successfully. Its downloaded log confirms normal firmware driver compilation, both `wr_rssi_delete_entry` symbols, the HTTP RSSI route and exact staged homepage assets (31,692 raw bytes including CSS).

The downloaded `rssi-image-checks.json` reports both unique packaged modules as ELF32 little-endian MIPS with observer symbols and RSSI command strings. Factory RSSI thresholds remain disabled. The following hashes are reported for the ROMFS modules; independent extraction from the final TRX remains to be done.

- `mt76x2_ap.ko`: 1473468 bytes; SHA-256 `08df1533bc70e3286c2c4918338e8be07a614c64244a4dcf4d75894588fcb37f`.
- `mt76x3_ap.ko`: 1664308 bytes; SHA-256 `3daec04370d07c5bafb76d4965b8817419f17dc4e508c39d887bd7c4144a4445`.

This proves build and staged image inclusion. It does not prove boot, ioctl behavior under load, client disconnect delivery or roaming. No router was flashed or rebooted for this verification.

## Downloaded user artifact

The downloaded `WR1200JS_4.4.198.9-100` artifact contains exactly the TRX and central config.

- `wr1200js.config`: 11091 bytes; SHA-256 `0885e7885216ba8d170cb122553836bd8ab48981b79ad15bc6b2e68fb8e0dfee`.
- `WR1200JS_4.4.198.9-100.trx`: 13125415 bytes; SHA-256 `45a9925cbbc125a046d8792f7f94f9f1bf3ca1071f4022f8e0cd59953137423a`.

The config hash matches the earlier verified build 144 config. These checks establish artifact contents and identity, not router compatibility at runtime.
