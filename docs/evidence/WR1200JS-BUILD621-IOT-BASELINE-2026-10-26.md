# WR1200JS build #621: production image and IoT radio baseline

Source: GitHub Actions run `40385894396` (build #621), commit
`b2ec88960a545e67509d5e64b9f78ef580311054`, completed successfully on
2026-10-26. The separate Band Steering ABI run `40385894121` also succeeded.

Artifacts read from #621:

- `wr1200js-config-checks` (artifact `12682270208`):
  `firmware-config-checks.json` reports 113 checked options, zero mismatches
  and zero pending options. Effective `CONFIG_FIRMWARE_INCLUDE_ZAPRET2=y` and
  `CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG=y`; HTOP and MTR are both `n` as requested.
- `wr1200js-iot-radio-capacity` (artifact `12681077262`): `mt76x3.json`
  reports effective MBSS and PCI support, a 16-BSS source/config ceiling,
  `three_bss_requirement_satisfied=true`, and a compiled main-observer probe.
  The report explicitly has `runtime_verified=false`.
- The run uploaded `padavan-linux-4.4.198-wr1200js` (artifact `12680612759`)
  and the router download bundle (artifact `12682155650`). Their upload and
  the green workflow do not establish IoT inclusion or operation on hardware.

The downloaded image artifact contains
`WR1200JS_4.4.198.9-621_7387f877.trx` (13,064,542 bytes). An independent
local read of its 64-byte uImage header and payload confirmed magic, header
CRC32, declared payload length, payload CRC32, architecture ID 5 and
compression ID 3. Its independently computed SHA-256 is
`d99494e8eb870e84b80686b3b88d4329e9266a2d3bb26f8f23075b2ca3aa548e`,
matching `firmware-image-checks.json` inside the artifact. This verifies the
downloaded image structure and checksum, not boot or router behavior.

The ordinary #621 workflow did **not** select the optional isolated IoT v40
candidate. That candidate is compiled separately after the ordinary firmware
image when `run_candidate_checks=true`; it is not installed in the image.
The production third-BSS capacity check therefore proves only a prerequisite,
not a working IoT network, isolation, WebUI Apply, or device acceptance.
The optional #622 run (`40387415111`) was dispatched on the same published
commit with `candidate_scope=iot` and `iot_candidate_variant=v40`; evaluate
its result separately.
