# WR1200JS test build 230

Observed 2026-10-13. [Run 38426900625](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38426900625) completed successfully. Version identity in the run's download manifest is `230_5ee8b883`.

The completed run log was downloaded to `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build230-log.txt`.

At 16:15:25 UTC, the image verifier reported `PASS shipped handshake UI, EN/UK/RU labels and linked observer/utility paths; runtime unverified`. This gate checks both VPN pages, fixed role selectors, refresh controls, shipped dictionaries, linked HTTP handler strings and executable utility path. It does not execute the observer on the physical router.

The run's common download manifest reports `WR1200JS_4.4.198.9-230_5ee8b883.trx`, 13,139,259 bytes, SHA256 `b8fa1b8d5b1cfe73526106f20757fd1e3cb2ef3acaf6b989fcb0f5167e6ff30c`. These are manifest values; this observation has not independently downloaded and hashed the image. Firmware artifact id: `11830446917`.

This build predates idle-loop result handling, worker descriptor isolation, joint interface/handshake refresh and DNS status refresh. It is retained as evidence of the initial handshake image gate, not the latest runtime candidate. No physical flashing, reboot or router/browser verification was performed.
