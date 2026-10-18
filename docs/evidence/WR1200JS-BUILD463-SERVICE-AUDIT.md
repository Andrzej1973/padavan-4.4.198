# WR1200JS build #463 — service/WebUI and BusyBox checkpoint

Date: 2026-10-18. Firmware run
[`39121882639`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39121882639)
completed successfully for commit `09e21de4deb711e0784d2a187c7f6402a28e0184`.
The `select`, `build (wr1200js)`, `firmware-zip` and `downloads` jobs passed.

## Shadowsocks status page

The final ROMFS gate ran `tools/verify-shadowsocks-status-image.py`. It checks
separate saved-setting/process observations for `ss-redir` and `ss-local`, the
HTTP handler and binary markers, manual refresh buttons, visible-page 30-second
refresh, 45-second expiry, and EN/UK/RU labels. A green state means only that the
saved option is enabled and the corresponding process was observed; it does not
verify server reachability, DNS, or client traffic. Browser acceptance on the
physical router remains open.

## Exact-image BusyBox evidence from build #460

Run
[`39120898001`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39120898001)
passed its target BusyBox audit. The downloaded `target-busybox-audit.json`
records BusyBox SHA256
`76e8995d81e0f26b4d1d204c09742c459debad3d9276bf5c758522adf33e9193`, config
SHA256 `974bd8ab62b9703337bfa2d34886c5c71eded32e7805423dc2742b455040f457`, 57
shell scripts, 150 applets, and safe invalid-action probes for Stubby, DoH and
Privoxy. All reported checks passed.

That report explicitly keeps `whole_service_audit_complete: false` and
`runtime_verified: false`. It did not identify the BusyBox version or source
revision, inventory applet symlinks, or report the BusyBox ELF loader/library
closure. Commits `789a85b` and `1ec907d` add those report fields and a partial
selected-service entrypoint map; firmware runs #464 and #465 are the evidence
gates for those changes and were still running/queued when this note was written.

## Limits and next checks

The complete audit still needs per-service lifecycle, setting persistence,
failure/recovery and dependent-chain coverage under the exact image BusyBox.
The current entrypoint map is explicitly partial. CI/image evidence is not
physical runtime acceptance; the router remains on the user's confirmed build
#396 and was not changed.
