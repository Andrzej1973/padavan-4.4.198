# WR1200JS build 451 — independently inspected artifact

[Run 39114348390](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39114348390)
completed successfully for `b1e8803d9a4beb449f045d42b0afcc755f379d7f`.
Downloaded final artifact ID: `12132320166`.

- Image: `WR1200JS_4.4.198.9-451_b1e8803d.trx`.
- Bytes: `12621387`.
- SHA-256: `78d6bdf0c93f700a3e2beb4d4a1d258dbe6f8db0622997acf3a41553e0911d7c`.
- Local image verifier passed product ID, header CRC, payload CRC, length and
  configured upload-size checks; see `WR1200JS-BUILD451-STRUCTURE.json`.
- Downloaded configuration report has 112 options, no mismatches and no pending
  options. The verifier was independently rerun on downloaded requested,
  firmware-effective and kernel-effective configs and passed with no pending
  options. This is configuration evidence, not complete package/runtime proof.
- Guide contains build 451 and its project commit. It lacks final image name
  and SHA-256; `005c749` corrects subsequent packaging, not this old artifact.

Downloaded target BusyBox report passed 15 checks and syntax checks for 57
shell scripts. BusyBox SHA-256:
`cd1f56d48cf610552b2a1269c22191ddd193d4aae80ba7c2c0df44026fa0503b`.
It retains `whole_service_audit_complete: false` and `runtime_verified: false`.
The accompanying QEMU export check confirms synthetic WG/AWG export/validation
and failed-start cleanup, with real network lifecycle explicitly unverified.

Actual Kbuild radio-capacity reports are preserved in
`WR1200JS-BUILD451-IOT-MT7603.json` and `WR1200JS-BUILD451-IOT-MT7612.json`.
Their effective source/configuration limits are 16 and 8; the required 2.4 GHz
three-BSS gate passed. This is not a live SSID count.

No flashing or device mutation was performed for this evidence. Boot, retained
user settings after reboot, concurrent independent tunnels, complete service
lifecycle and physical IoT acceptance remain open. Independently inspected
configs explicitly request SQM off and enable neither effective SQM nor kernel
CAKE. The successful `Build WR1200JS firmware` CI step also asserts absence of
`sch_cake.ko` in final ROMFS; that filesystem assertion was not independently
rerun on an extracted image in this pass.
