# WR1200JS test build 231

Observed 2026-10-13. [Run 38427208803](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38427208803) completed successfully for commit `e1a0a26cd3652697d214222e9f37aa64d375d5d2`.

Completed log: `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build231-log.txt`.

- At 16:17:12 UTC, the handshake image verifier confirmed shipped UI, EN/UK/RU labels and linked observer/utility paths.
- At 16:17:15 UTC, router guide checks passed. This commit adds explanations of handshake sampling and unavailable/stale status to the model-specific generated guide.
- The completed download manifest reports `WR1200JS_4.4.198.9-231_e1a0a26c.trx`, 13,139,291 bytes, SHA256 `a5828e414a1f4ffaaf9d49bea3f5bc14a1a4fb8cbe78959dc7cb608de1a2e7d5`. These are manifest values; the image has not independently been downloaded and hashed in this observation.

This image includes accepting completed workers before timeout cancellation and tracking observation age from worker start. It predates closing inherited HTTP descriptors in the worker itself, combined interface/handshake refresh and DNS process refresh. Later builds remain the candidates for those changes.

No physical flashing or router/browser execution was performed. These checks prove compilation and selected image contents, not router stability or completion of the port.
