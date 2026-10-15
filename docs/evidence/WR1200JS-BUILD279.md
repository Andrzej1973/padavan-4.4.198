# WR1200JS test build 279 — USB/IP lifecycle and packaging

[Run 38741650267](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38741650267)
completed successfully at `f86005bf263e383ba326d51932d7f2ddf4948da4`.
Artifact `WR1200JS_4.4.198.9-279_f86005bf_TEST`, ID `11977096208`, was
downloaded into `../build279-final` on 2026-10-15.

Independently computed SHA256:

- `WR1200JS_4.4.198.9-279_f86005bf.trx`: 12,593,835 bytes;
  `9b2fd3bb91af3d8fa88d26186ae6ba2ea2b462fadaba2cc3f66b6e5cf82149d9`.
- `SETUP_WR1200JS.txt`: 26,532 bytes;
  `b1caa5295a1821cf2772063bed22486e36aae061911e175c5223b297d941cd96`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The downloaded profile matches the local requested profile SHA256. The guide
identifies build `279_f86005bf` and the full commit. Requested/effective config
verification and guide generation passed. The build includes the corrected
ROMFS directory creation, managed controller and firewall policy, default-off
boot/shutdown hooks, and USB-service Apply control. The image verification at
this commit checks controller executability, exact installed script contents,
USB/IP UI selector and EN/UK/RU enable-help keys.

This image predates the device inventory (`51777f0`) and guarded bind/unbind
controller (`f2ad65c`). Do not use it as evidence for those later changes.
No firmware installation, restart or USB action was performed on the router.
Physical lifecycle, firewall behavior, saved enable state, reboot persistence
and USB transfer remain unverified.

Later isolated [service run 38743571036](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38743571036)
passed at `f2ad65c8598bda3e39ccaf4c6846e31934d001db`. Its log confirms the
candidate device-policy fixture and device-action fixture: identity mismatch,
preflight refusal, missing daemon ownership, direct argv, lock descriptor
closure, busy-device refusal, and observed binding with a mock USB/IP command.
These fixtures do not execute real kernel bind/unbind or prove a transfer.
