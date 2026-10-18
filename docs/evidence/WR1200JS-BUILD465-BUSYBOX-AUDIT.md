# WR1200JS exact-image BusyBox audit — build 465

- GitHub run: `39122905943` (build #465), successful.
- Build commit: `1ec907d73c2f1bea21846a260cdace5c69169ae5`.
- Firmware source revision: `c25283e915a2a00a763774dd255b14aff997285e`.
- Target BusyBox: 1.24.2.
- BusyBox SHA-256: `bbd65a153da8632721092e5cf725af3d0feb16d0c4bfe002ce211f4a1981352b`.
- BusyBox config SHA-256: `9622f300e22e6942c302edbb422adb81691c31668c92adf2482383cb878101aa`.

## Passed in the exact image

- All 57 discovered shell scripts passed target BusyBox syntax checks.
- 150 applets and all 150 applet links were inventoried.
- BusyBox ELF loader/library closure resolved (three report nodes).
- Every emitted report check passed; no failed check keys were present.
- Nine selected service groups had mapped image entries present and mapped
  shell scripts syntactically valid: Dropbear, Stubby, DoH, Privoxy, iPerf3,
  WireGuard/AWG, ZeroTier, USBIP and vlmcsd.

## Limits and follow-up

The report deliberately records `selected_service_entrypoint_map_complete`,
`whole_service_audit_complete` and `runtime_verified` as false. Comparing the
effective config with the map exposed that Shadowsocks is enabled through
`CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS`, while the map looked for legacy
`SSREDIR`/`SSLOCAL` selectors. The map also needs the separate AmneziaWG
selector and WR Band Steering binaries. The local correction adds these entries
and a pre-build registry check; it still needs exact-image CI.

This is an exact-image BusyBox compatibility result, not a complete lifecycle,
service-interaction, or physical-router test.
