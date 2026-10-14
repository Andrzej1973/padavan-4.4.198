# WR1200JS test build 250 — downloaded artifact evidence

[Run 38502695605](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38502695605) completed successfully at commit `ccc1ca3cd1b7d556fbabc33f7ab421eb29a9bdd5`. Artifact `WR1200JS_4.4.198.9-250_ccc1ca3c_TEST`, ID `11866719683`, was downloaded into the parent workspace's `build250-final` directory. Local SHA256 was computed on the extracted files:

- `WR1200JS_4.4.198.9-250_ccc1ca3c.trx`: 13,142,987 bytes; `d56c0d1a51036180e102138adbfcf1ac7c0a7c2755308022f9dafd0eff4aec95`.
- `SETUP_WR1200JS.txt`: 21,890 bytes; `9f37b146d8dab56c4f72686bdc84109173b3d49a955c617ebfcd425a135acef0`.
- `wr1200js.config`: 11,249 bytes; `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.

The guide identifies build 250 and the exact commit above and explains verification of actual ZRAM swap via `/proc/swaps`. The packaged requested configuration has `CONFIG_FIRMWARE_INCLUDE_SQM=n` and explicitly excludes CAKE/SQM. The run result and these downloaded files establish build/artifact evidence; the actual kernel/module exclusion gates and other service checks should be interpreted within their specific scope.

This image includes the client translation and stale collection-stage changes through `ccc1ca3`. It predates the later diagnostic utilities and physical-shape regression additions. It has not been installed on the user's router by this work. Current standalone collector success on the older live image does not establish rendered-page behavior, complete firmware stability, configuration retention or reboot persistence for build 250.
