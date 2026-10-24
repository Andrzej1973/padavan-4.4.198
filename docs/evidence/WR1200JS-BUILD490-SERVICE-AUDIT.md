# WR1200JS build #490 service/image evidence — 2026-10-19

[Run 39293102227](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39293102227)
completed successfully for PR head `8e3a6811711f1b6f10ca41d69dc9c719e03eed64`.
The pull-request merge revision used by the build was
`13f7939953e66185c5fa1f92b8e97171ed17edc3`; this is the `GITHUB_SHA` in the
image audit, not a different PR head. The firmware base revision is pinned to
`c25283e915a2a00a763774dd255b14aff997285e`.

The target BusyBox audit artifact (ID `12207491247`) was downloaded separately
into `.audit-build490-exact/`. SHA256 of `target-busybox-audit.json`:
`0cd456c422be5da5482191c29a8dfb01d45ec11261d043a2ad9ae862406f8869`.
It records `success:true`, no entrypoint gaps, and passing entrypoint checks
for all 12 active service groups. The effective image has 42 INCLUDE selectors;
the requested profile has 43 because SSLOCAL + SSREDIR are intentionally
normalized to one SHADOWSOCKS package selector. This matches the workflow and
configuration verifier, rather than indicating a lost client binary.

## QoS and SFE image checks

- All 15 configured QoS module paths and IMQ/IFB core symbols passed.
- `/bin/tc` is executable little-endian MIPS ELF with a complete image-library
  closure. QEMU with the ROMFS loader/libraries returned
  `tc utility, iproute2-5.12.0` from `tc -V`.
- SHA256 of `tc`:
  `bb84853e9865c4efdc8a88944a32eaa7ff4f058a685718f774218056a55c02da`.
- SFE passed presence checks for `/sbin/rc`, BusyBox `modprobe` and all four
  Shortcut FE modules. This does not exercise module loading or traffic.

BusyBox is version `1.24.2`, binary SHA256
`6ebb1ac81caf1a7d7053c0d8b8bd1548b2a3a80eae79fb6e9b9d987ce9374d68`;
effective config SHA256
`685dc97f73cb620b0908e5617b36189c9a68d0c072e7d4b41a7dc0825d5bdfde`.

## Localization and limits

Job metadata confirms successful execution of both the precompile inherited
dictionary regression and final-ROMFS dictionary verifier, plus the existing
settings-page presence check and target BusyBox probes. Firmware ZIP and
download packaging jobs also passed. The generated artifact name still uses
`WR1200JS_4.4.198.9-490_13f79399_TEST`; delivery naming remains a separate item.

The report deliberately retains `runtime_verified:false` and
`whole_service_audit_complete:false`. It does not prove usable QoS policies,
offload, physical protocol traffic, browser display, flash writes, service
interactions or reboot persistence. The later flash-feedback and USB/IP
uncertainty commits `931f1e4`/`9a6449e` are absent from #490 and were pushed
only after this run completed. No router was flashed or rebooted.

A local follow-up also classifies requested SSLOCAL/SSREDIR as service aliases
in the precompile map, so both requested and effective selector forms require
the Shadowsocks entrypoints. Its 12-group/43-selector fixtures pass; this
precompile alias correction is not part of #490.
