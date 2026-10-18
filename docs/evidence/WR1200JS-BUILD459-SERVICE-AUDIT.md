# WR1200JS build 459 — service/WebUI audit checkpoint

Date: 2026-10-18. Firmware workflow run
[`39120542985`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39120542985)
completed successfully on commit `c7b72164265bbf598e93ce2aae4f293638adfd50`.
The `select`, `build (wr1200js) / build-wr1200js`, `firmware-zip` and
`downloads` jobs all passed. This is build and final-image evidence only.

## Relevant checks that passed

- The final ROMFS VPN status verifier ran after firmware assembly. The WG/AWG
  legacy client row no longer treats cached `vpnc_state=1` as a green
  connection; WG/AWG use the independent interface and handshake indicators.
- The exact image BusyBox/QEMU audit ran, along with VPN-profile lock, WireGuard
  server-export and USB/IP restore probes. These cover shell syntax and bounded
  synthetic cases, not every service lifecycle or the live device.
- Final-image gates ran for the shared Wi-Fi and connected-device pages,
  unified service navigation, ZeroTier, DoH, Stubby, Privoxy, iPerf3, SSH,
  ZRAM, USB/IP settings, WAN/RSSI controls and the setup guide.
- The target BusyBox report remains deliberately limited: `runtime_verified`
  and `whole_service_audit_complete` are false. A successful build is not
  blanket BusyBox compatibility or runtime acceptance.
- Service runtime workflow run
  [`39120542901`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39120542901)
  passed its lifecycle job: USB/IP status, VPN profile identities/parsers,
  private storage permissions, WAN socket plan and RC failure paths.

## Follow-up work in progress

Commit `7ef4964` extends the exact-image BusyBox gate to require and safely
exercise invalid-action rejection by every selected Stubby, DoH and Privoxy
dispatcher. This runs under build #460; it is not yet CI evidence. Commit
`467ee2b` makes the unified-navigation image check verify `#row_...` anchors,
not only the destination page; it is queued as build #461.

Service start/stop recovery and saved-setting persistence still need a
selector-driven per-service audit and additional bounded synthetic cases.
Physical browser/service behavior remains unverified: the router is still on
the user's confirmed build #396. No router settings, daemons or firmware were
changed by these checks.
