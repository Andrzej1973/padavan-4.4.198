# WR1200JS build 144 evidence

[Build 144](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38035198798) completed successfully. Its log confirms the RSSI observer wrapper compiled with the actual configured target kernel, and the staged homepage assets and linked observation/action JSON markers passed verification (25763 raw asset bytes).

The downloaded final `WR1200JS_4.4.198.9-100` artifact contains exactly two files:

- `WR1200JS_4.4.198.9-100.trx`: 13112548 bytes; SHA-256 `7a7fe70fa6976fb1fb74787980e5be25ba257c9159ad0fea09ecd4d899f71001`.
- `wr1200js.config`: 11091 bytes; SHA-256 `0885e7885216ba8d170cb122553836bd8ab48981b79ad15bc6b2e68fb8e0dfee` (identical to build 137).

[ABI 300](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38035321206) confirms changed second-radio source rejects RSSI preparation without partial writes.

The isolated full-driver candidate compile was skipped in build 144 because production steering was enabled. This is not proof that the new RSSI instrumentation compiles in either complete driver. Commit `ad920d349a4c231fafac07159f18401ca0df3128` removes that skip condition for subsequent builds. Candidate RSSI instrumentation is not installed in this firmware image. No router boot, client kick, roaming, tunnel recovery or performance behavior is verified by these build results.
