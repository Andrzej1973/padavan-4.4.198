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
and a pre-build registry check. At the time this build #465 report was written,
exact-image CI for that correction was pending; build #478 below supersedes
that pending status.

This is an exact-image BusyBox compatibility result, not a complete lifecycle,
service-interaction, or physical-router test.

## Follow-up exact-image CI — build 478

GitHub Actions run [39139346947](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39139346947), build #478 at commit `d1dc0ebaf82af316ad8ba65a01952c229c69e919`, completed successfully. The WR1200JS job reports successful completion of both **Check exact-image BusyBox service map before firmware compilation** and **Audit all shipped shell scripts with exact target BusyBox**; the `target-busybox-audit` artifact was uploaded. This is newer exact-image CI evidence for the selector/map correction described above, including the selected Shadowsocks, WireGuard/AmneziaWG and Band Steering entrypoint groups.

The correction does not close the full audit: the current checker still sets `whole_service_audit_complete` and `runtime_verified` to false. Its source also keeps explicit unverified image-entrypoint groups for ZRAM, QoS, SFE, U2EC and WPAD. These need feature-appropriate exact-image assertions and lifecycle review; some are kernel/runtime or WebUI features rather than shell entrypoints. Build #478 was not flashed, and no router state was changed.

## WPAD cross-gate wiring — local follow-up

The exact-image BusyBox report now consumes the successful
`wpad-image-checks.json` emitted by `verify-wpad.py`. When WPAD is selected, all
12 required ROMFS checks must be true; otherwise the audit reports a WPAD image
gap. WPAD is no longer described as a missing shell entrypoint when its actual
page/HTTP/PAC image gate passes. The pre-build map checker also enforces that
`verify-wpad.py` runs before `check-target-busybox.py`.

Local validation passed: the saved build #410 WPAD report satisfies the new
12-check contract, the map checker verifies all 43 active selectors and
workflow ordering, and both Python scripts parse. Build #478 separately shows
that its WPAD ROMFS step and exact BusyBox audit step both succeeded, but the
new report-consumption code was added afterward and has not run in CI. Physical
HTTP/PAC behavior and persistence remain unverified; build #478 was not flashed.

### ZRAM exact-image report linkage

The exact-image audit now consumes `zram-image-checks.txt` when ZRAM is selected
and marks that feature gate passed only for the expected successful verifier
record. The map preflight asserts that `verify-zram-image.py` emits this report
before the BusyBox audit runs. Build #478 confirms the dedicated ZRAM verifier
and BusyBox audit both succeeded in sequence; this new report-consumption check
is later local work and still needs CI. This establishes image dependencies,
startup command and BusyBox option evidence only. Active swap on the router and
reboot persistence remain separate runtime checks.

### U2EC exact-image entrypoint mapping

The WR1200JS build #478 job log confirms the U2EC ROMFS install step created
`/usr/sbin/u2ec` and reported it executable. The local selected-service map now
associates `CONFIG_FIRMWARE_INCLUDE_U2EC` with that exact image path, and the
pre-build map check requires the association. Local map validation passes. This
new mapping has not yet run in CI. It establishes binary presence only; rc start
dispatch, observed process state, printer protocol behavior and WebUI lifecycle
remain open.
