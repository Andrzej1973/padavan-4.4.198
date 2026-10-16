# WG/AWG server functions — exact image BusyBox, build 357

[Full run 38950105582](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38950105582)
at firmware commit `61bce23` completed successfully on 2026-10-16.
The `target-busybox-audit` artifact was downloaded and inspected.

- BusyBox SHA256: `653ca8714bc9a188baf2516aa58cf423cc77c679b0cf2a855c51af1891f07310`.
- Effective BusyBox config SHA256: `198a8b88415acc793b79053dfb4066519d3259f0f0e53699abde643668fc8501`.
- Shipped `/usr/bin/wgs.sh` SHA256: `f22fbe6a0a6682d2750747a3054a6d90cbb4d69508886fb391ec588547fd517f`.
- General audit: 56 scripts, 150 applets, all its bounded checks passed.
- Exact image shell/applet fixture: shared AWG server/export parameters,
  standard WG exclusion, invalid inputs, 32-bit boundaries and startup cleanup
  control flow passed. The fixture mocks NVRAM, wg and ip operations.
- The USB/IP restore fixture under target BusyBox also passed in this run.

This verifies the shipped shell and applets for the tested functions under
QEMU. It does not verify real interface creation/deletion, handshake, DNS,
routing, concurrent lifecycle actions or the physical router. The new
independent-profile manager is not packaged by this firmware commit.

Separately, [service CI #125](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38951822000)
at `ef3bd02` passed host-native import-adapter tests against WG tools commit
`3ba6527130c502144e7388b900138bca6260f4e8` (v1.0.20210914) and AWG tools commit
`ee0f0a9aa34ff0a0da4b3433b9512781cfe02843`, the versions selected by the firmware.
It exercised quick metadata, key validation, WG/AWG field differences,
unsupported hook/policy refusal and a resolver guard. This is host validation,
not target or runtime acceptance of the import adapter.
