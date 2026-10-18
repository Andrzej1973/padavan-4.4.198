# WR1200JS firmware build 448 — image and configuration evidence

- GitHub Actions run: [39104625566](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39104625566)
- Firmware source commit: `5dd2c80088bbaf1ba5199d45f335792452dc8b8f`.
- Result: completed successfully; all four jobs succeeded.
- Image: `WR1200JS_4.4.198.9-448_5dd2c800.trx`, 12,621,347 bytes.
- SHA-256 independently recomputed from the downloaded TRX:
  `23dbbfb40abd873063d5c40c3f2d63ea8ea63e1c3a1dd639702c6edf5f5dc399`.
  It matches the build artifact's `SHA256SUMS` entry.

## Target and configuration checks

The build's effective firmware configuration matched all 112 requested firmware
options: zero mismatches and no pending options. The effective kernel config
identifies the `wr1200js` built-in device tree, selects MT7603E and MT7612E,
keeps FQ-CoDel enabled, and leaves `CONFIG_NET_SCH_CAKE` unset. The firmware
selector `CONFIG_FIRMWARE_INCLUDE_SQM` is not set. The successful build step
also ran the disabled-SQM gate, which rejects both an enabled CAKE kernel option
and `sch_cake.ko` in ROMFS. The image structure report passed product ID,
uImage header CRC, declared length, payload CRC and size checks.

## Service and image evidence

The build passed the final-image checks for Stubby and DoH, Privoxy, SSH,
iPerf3, ZeroTier, VPN profile tools, USB/IP, ZRAM, WPAD, RSSI controls and the
WAN page. The target BusyBox audit succeeded: it inventoried 150 applets and
validated syntax for 57 shipped shell scripts. Its report explicitly retains
`runtime_verified: false` and `whole_service_audit_complete: false`; image
packaging and bounded BusyBox probes do not complete the full service audit.

The generated `SETUP_WR1200JS.md` covers the enabled services, including
ZeroTier, Stubby/DoT, DoH, WireGuard, AmneziaWG, ZRAM, USB/IP, Privoxy,
Shadowsocks, WPAD and Band Steering.

The image's Stubby binary was also run under QEMU with the generated
`stubby.sh` configuration. The test resolved names over authenticated DNS-over-
TLS, observed `SERVFAIL` in strict mode while TCP/853 was blocked, and recovered
immediately after the test unblocked the port. This is target-binary emulation;
it is not a physical-router or WAN acceptance test.

## Remaining acceptance

No physical router was flashed or rebooted for this build. Boot, WAN/LAN,
wireless under load, service interactions, remote-management continuity,
performance and reboot persistence remain unverified on the device. The build
and image checks are positive evidence for this exact image, not proof of a
completed device port.
