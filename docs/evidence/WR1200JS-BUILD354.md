# WR1200JS test build 354 — WireGuard/AmneziaWG QR

[GitHub Actions run 38943263134](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38943263134)
completed successfully for firmware commit `d690a6a8` on 2026-10-16. The firmware
job completed in 11m54s, including QR preparation, WR1200JS compilation, image
structure checks and upload. Service runtime-state workflow #119 also passed on
the tested VPN/QR source commit `83bec0d`.

Test artifact `WR1200JS_4.4.198.9-354_d690a6a8_TEST`, artifact ID
`12065200926`, downloaded and independently hashed on the host:

- `WR1200JS_4.4.198.9-354_d690a6a8.trx`: 12,546,005 bytes;
  SHA-256 `a72671cb8e1387092c7eb2d3ecbe9919c3c9604889d4000308e1a09a4d3cde48`.
- `SETUP_WR1200JS.txt`: 31,874 bytes;
  SHA-256 `d436b630457700c3fc2e0ebe3b1081a8fd78ad9c4ac4ac6972e901237c562cd4`.
- `wr1200js.config`: 11,407 bytes;
  SHA-256 `097785f7be4543245ceefd744e591b8ecd21ef8898522a0c1a469569ca409e5d`.

The generated guide identifies test build 354 and commit `d690a6a8`. The CI
configuration report has no mismatches or pending selectors; requested and
effective settings agree for the audited profile, including WireGuard,
AmneziaWG, Stubby, DoH and ZeroTier. `CONFIG_FIRMWARE_INCLUDE_SQM=n`; CI also
checks CAKE is absent from the effective kernel config. These checks establish
build/config/image evidence, not live service health.

The QR changes use the shared local UTF-8 renderer and the exact saved client
export for both QR and `.conf` download. Local tests cover exact payload
equality, WG/AWG cases, stale-state clearing, renderer failure, and AWG
parameter propagation/validation. The CI image gate checks the renderer,
server fields and server script are present in ROMFS.

The artifact has **not** been installed on the router. Current device
acceptance, retained settings/access, tunnel routing, reboot persistence and
stability under traffic remain unverified. This is a test image, not a stable
release. Artifact retention expires 2026-10-30 18:06 UTC unless downloaded
earlier.
