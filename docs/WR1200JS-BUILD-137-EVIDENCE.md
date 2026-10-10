# WR1200JS build 137 evidence

[Full build 137](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38028689523) completed successfully from commit `52b7fceef8c9ba4bca78b1f4e79235999434057d`.

The actual staged-image check passed exact homepage assets and linked observation/action JSON markers. Raw JavaScript and CSS assets totalled 25761 bytes. This verifies image inclusion, not router runtime behavior.

## Final download

Artifact `WR1200JS_4.4.198.9-100` (ID 11662091842) was downloaded and inspected. It contains exactly two files:

- `WR1200JS_4.4.198.9-100.trx`: 13112636 bytes; SHA-256 `77b1df827b974811e5658b9e70213dbc0584e679afd2dbe2be4a56639748bf01`.
- `wr1200js.config`: 11091 bytes; SHA-256 `0885e7885216ba8d170cb122553836bd8ab48981b79ad15bc6b2e68fb8e0dfee`.

The config is byte-identical to verified build 127. The TRX is 7804 bytes larger than build 127; this is an aggregate image difference, not an isolated feature-size measurement.

## Regression checks

Full builds 129 through 136 were individually inspected and failed on the same missing GNU credential API declarations in actual `web_ex.c`. Build 137 selects `_GNU_SOURCE` before its libc headers and successfully compiles the actual HTTP service.

[ABI 284](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38028824555) completed successfully. Its credential API probe copies the actual prepared HTTP prefix and compiles for native Linux and MIPS. Maximum-width serialization of 512 observation/action events produced 101281 bytes plus bounded response metadata, below the browser limit of 131072 bytes.

## Not yet verified

Boot, Wi-Fi stability, tunnel restoration, feature behavior and CPU cost on the physical WR1200JS remain unverified. No router was flashed or restarted for these checks. RSSI Kick action instrumentation is not connected to the command history yet.
