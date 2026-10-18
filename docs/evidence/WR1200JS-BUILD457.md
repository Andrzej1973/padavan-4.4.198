# WR1200JS build 457 — image and configuration evidence

[Run 39116103457](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39116103457)
completed successfully for commit `4cd56a8e9587bbb48f87e1540c32ea0a2a56cf21`.
The final TRX was present in both the per-image artifact
`12132279061` and the combined download artifact `12132792374`.

- Image: `WR1200JS_4.4.198.9-457_4cd56a8e.trx`.
- Bytes: `12621335`.
- SHA-256: `063be5fbf4d70334b0092a1da4362f3f16cb9d7188fc42d597ebe0dd21ef7161`.
- Independent local checks passed for uImage magic, WR1200JS product ID,
  header and payload CRCs, declared length and allowed image size. The setup
  guide's image filename and SHA-256 binding also passed. See
  `WR1200JS-BUILD457-STRUCTURE.json`.
- The independently rerun requested/effective/kernel config verifier checked
  112 firmware options with no mismatches or pending options. Requested SQM is
  `n`, effective `CONFIG_FIRMWARE_INCLUDE_SQM` is unset, and
  `CONFIG_NET_SCH_CAKE` is unset in the kernel. See
  `WR1200JS-BUILD457-CONFIG.json`.
- Actual Kbuild capacity reports confirm the required MT7603 three-BSS
  source/config gate (effective limit 16) and report MT7612 limit 8. Both
  explicitly retain `runtime_verified: false`; the driver does not yet prove
  a live third SSID. See the two `WR1200JS-BUILD457-IOT-*.json` files.
- The separate station-capacity diagnostic records target compiler formulas
  for client-array sizing. These values describe station capacity, not BSS
  count; see `WR1200JS-BUILD457-STATION-CAPACITY.json`.
- Target BusyBox/QEMU audit succeeded: all 57 discovered shell scripts passed
  syntax checks and bounded applet/dispatch probes passed. Its report sets
  `whole_service_audit_complete: false` and `runtime_verified: false`; service
  lifecycle behavior is not established. See `WR1200JS-BUILD457-BUSYBOX.json`.

These are build, package/configuration and bounded QEMU/source checks. They do
not prove device boot, preserved settings after reboot, physical radio behavior
or a complete Linux 4.4.198 device port.
