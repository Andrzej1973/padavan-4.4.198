# WR1200JS test build 265 — USB/IP observation

[Run 38603817098](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38603817098), commit `223d49dcd2950033ba46583f18d2aedab8f3f14a`, completed successfully. Downloaded artifact `WR1200JS_4.4.198.9-265_223d49dc_TEST`, ID `11915139087`, is stored in the parent workspace's `build265-final` directory.

Independently computed SHA256:

- `WR1200JS_4.4.198.9-265_223d49dc.trx`: 12,589,050 bytes; `7c654ed1da314e05093f0e67d0890af1e33f1f99aa92678e6b4a1014b32bf9bb`.
- `SETUP_WR1200JS.txt`: 23,353 bytes; `38b9ced43f349f5f0700d94f73ea3724f8be1a29325b71a359a05a77c3d9b90c`.
- `wr1200js.config`: 11,333 bytes; `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The downloaded profile matches the requested profile byte for byte. The guide identifies `265_223d49dc` and includes USB/IP status guidance. StrongSwan remains deferred and CAKE remains excluded by the existing configuration policy.

The full build log at 17:19:19 UTC confirms the new endpoint marker in the packaged USB/printer page and compiled `httpd`, and the title key in packaged `EN.dict`, `UK.dict` and `RU.dict`. USB/IP ELF closure verification passed for five files. This establishes compilation and packaging, not correct device behavior or complete translation rendering.

Build 264 compiled the image but failed its subsequent verification because the gate incorrectly expected source-only `EN.footer` in ROMFS. Build 265 corrects the gate to packaged `EN.dict`; the firmware behavior was not changed by that correction.

The panel reads module paths and uses the existing process-name lookup for `usbipd`. It does not verify executable ownership, a listener, exported devices, connection success or data transfer. Native integration regression checks passed in [service run 38601555065](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38601555065); that test checks source transformation and does not execute the endpoint or browser refresh behavior.

This image has not been flashed by this work. Physical UI rendering, module loading, daemon operation, device export, configuration retention, reboot persistence and sustained stability remain unverified. Managed USB/IP actions and persistence remain open work.
