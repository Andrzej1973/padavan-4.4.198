# WR1200JS test build 229

Observed 2026-10-13. [GitHub run 38425200060](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38425200060) completed successfully for commit `7fa96c1052ae04603484418ed88034bf6b8f5197`.

Downloaded artifact `WR1200JS_4.4.198.9-229_7fa96c10_TEST`, id `11829715578`, to `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build229-final`.

- `WR1200JS_4.4.198.9-229_7fa96c10.trx`: 13,139,311 bytes; SHA256 `3134a29b3cf8b007187e2b6f2c153f39c459eab4f618c1798375e6082730f5c3`.
- `wr1200js.config`: 11,249 bytes; SHA256 `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.
- `SETUP_WR1200JS.txt`: 17,850 bytes; SHA256 `72b5213799613d1634c22ebe686c9ed4374e8e947615f8fcb8170bc1003a3480`.

This build includes the first translated handshake UI and background observer. It predates the subsequent idle-loop timeout fix, worker descriptor isolation and joint interface/handshake refresh. It also predates the dedicated handshake image gate. Preserve as compilation evidence, not as the current runtime candidate.

No physical flashing, reboot, browser execution or device handshake verification was performed for this image. A successful build does not establish router stability or a completed device port.
