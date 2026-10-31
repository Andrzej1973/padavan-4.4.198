# WR1200JS build #504 — service/WebUI image checkpoint

GitHub Actions [build #504](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39461735957)
completed successfully on 2026-10-20 for PR #2 source head
`9c1e9b169acc28dd621e3374a81297755b16fa55`. The build, firmware packaging,
and download aggregation jobs all completed successfully. The run uploaded
`padavan-linux-4.4.198-wr1200js` (artifact `12284185914`, 12,847,450 bytes).

## Item 4 service/WebUI evidence

The build log confirms these checks passed:

- Service navigation panel, capability parsing, return links and VPN profile
  route; unified service routes/pages and EN/UK/RU labels.
- Inherited dictionaries: 35 values and 30 contextual help keys transformed
  and verified in EN/UK/RU.
- All 247 served `/www` files matched effective httpd routes.
- Stubby final-ROMFS packaging and ELF dependency checks, followed by a
  successful authenticated DNS-over-TLS lookup through the image binaries
  under QEMU.
- DoH final-image packaging and ELF dependency checks.
- Settings backup/restore final-ROMFS check confirmed the page, Administration
  menu route, secure-session gate and EN/UK/RU labels. The browser-behavior
  fixture passed for the exact safe-session rows, cancel paths, form encoding,
  downloads, upload routes and flash-save success/error feedback. These are
  image-content and synthetic browser-logic checks, not a live authenticated
  browser session or real backup/restore on the router.
- WPAD, Privoxy, iPerf3, SSH, ZeroTier, KMS/Watchdog, StrongSwan exclusion,
  target BusyBox and service-specific image/UI checks reported by the build.
- The exact `9c1e9b1` target BusyBox gate also ran the conditional Lua image
  audit. Its source requires the MIPS Lua 5.1 executable, `cjson.so` and
  `nixio.so` dependency closure, syntax checks for shipped Lua files, JSON/Lua
  converter round-trip, and rejection of malformed JSON and Lua under QEMU.
  The build log reports the aggregate target BusyBox gate as PASS; that gate
  returns success only when all included checks, including
  `image_lua_utilities`, pass.

These results prove CI and selected final-image properties only. The target
BusyBox report itself leaves the full service/runtime audit open. No router
service was started or stopped, and no physical browser, live DNS/TLS,
persistence, or reboot behavior was tested by this run.
The Lua result is image/QEMU evidence for interpreter, modules and converters;
it does not exercise services which consume Lua, actual `nixio` socket/filesystem
operations, or physical-router behavior.

## Source boundary

PR #2 still points to `9c1e9b1`. Local commit `35d70be` removes unsupported
PPTP and standalone L2TP choices and corrects the OpenVPN capability check,
but it is newer than the PR head and is not contained in build #504. That
change still needs a build containing it and final-ROMFS/browser verification.

The run demonstrates a successful firmware build, not router runtime
acceptance. No firmware was installed and no router state was changed.
