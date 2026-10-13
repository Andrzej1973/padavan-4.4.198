# WR1200JS test build 243

[Run 38438228550](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38438228550) completed successfully, including the corrected requested/effective disabled-SQM policy gate. Artifact `WR1200JS_4.4.198.9-243_8e785d96_TEST`, id `11835115651`, was downloaded to `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build243-final`.

Independently computed SHA256:

- `WR1200JS_4.4.198.9-243_8e785d96.trx`: 13,139,831 bytes; `bd6f235773f048debd9314aef36b5bb7af1669bab522884ac8ca1f21cb868951`.
- `SETUP_WR1200JS.txt`: 21,890 bytes; `0bd2861fe3bc81881e3ca23370a91fd0ac8e432964363ff257fa09a2411c9c0e`.
- `wr1200js.config`: 11,249 bytes; `1cc0a76dd60b44ee8b9c1b298747084c3cdfcac696d85c1bdf7a555d1816708b`.

The downloaded profile matches the requested central profile byte for byte. The guide identifies `243_8e785d96` and includes the ZRAM actual-swap and refresh instructions. This image includes VPN/DNS/ZRAM status updates and the effective CAKE exclusion correction; it has not been installed by this verification.

The physical router's older Linux 4.4.198 installation is operating in test mode, as separately recorded in `docs/runtime/WR1200JS-2026-10-13-TEST-MODE.md`. It is not evidence of runtime behavior of build 243. The latest attempted VPN/steering read timed out, so no new handshake or steering result was obtained. No flash, reboot or configuration change was performed. Full port acceptance remains pending.
