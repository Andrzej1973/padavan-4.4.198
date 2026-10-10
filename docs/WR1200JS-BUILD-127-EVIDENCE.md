# WR1200JS build 127 evidence

[Full run 127](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38012708872) completed successfully at source commit `7c0111e7ff1b2ab0f85036ab987df5eb7a791dd4`.

## Download verification

Artifact `11654513503`, `WR1200JS_4.4.198.9-100`, was downloaded and contains exactly two files:

- `WR1200JS_4.4.198.9-100.trx`: 13,104,832 bytes; SHA-256 `4e6e6f3f8c785b7314952ad342e110bba22fc267f620aca1030f9ec767d209d7`.
- `wr1200js.config`: 11,091 bytes; SHA-256 `0885e7885216ba8d170cb122553836bd8ab48981b79ad15bc6b2e68fb8e0dfee`.

The config hash matches the verified build 123 and build 120 downloads. The image is 5,673 bytes larger than build 123; this is an aggregate build difference, not an isolated performance or compression benchmark. The filename version is not the workflow run number.

## Image integration evidence

The actual build log reports `PASS staged homepage, exact assets and linked JSON route; raw asset bytes: 22345`. The image verifier checks exact installed classification/refresh/homepage/history/export assets, both authenticated device/history JSON route markers in the linked HTTP daemon, and preservation of the original network-map page. The full build also passes the corrected 64-client station-table ABI assertion.

This image contains passive radio association observations, shared cache, background RAM history and the homepage timeline with JSON export. The later steering action schema, wire transport and command wrapper were added after its source commit and are not evidence of live action recording in this image.

## Remaining verification

A successful image build does not prove router boot, Wi-Fi stability, actual Steering/RSSI Kick behavior, browser appearance on the real page, forwarding throughput, CPU/RAM overhead or remote AmneziaWG restoration. These require target evidence. No flashing, reboot or disruptive router test was performed. Preserve the management tunnel and arrange recovery access before any separately authorized upgrade.

Continue WR1200JS delivery before secondary boards. This milestone does not complete the project or authorize deletion of private backup files.
