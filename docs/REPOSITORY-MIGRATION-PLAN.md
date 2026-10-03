# Padavan 4.4.198 repository migration

User authorized creation of Andrzej1973/padavan-4.4.198 on 2026-10-03,
including explicit Public visibility confirmation. Preserve the existing
repository and history. Migration is an active delivery step, not deferred
until the end of the port.

## Required delivery

1. Import the existing project history and experimental/Padavan-4.4.198 branch.
   Preserve the migration source SHA and compare files before changing defaults.
2. Keep configs.build as the catalogue of board profiles, with explicit board
   support status. WR1200JS remains the full profile; Mi Mini is reduced and
   pending its complete board port. Unsupported profiles must not masquerade
   as working targets.
3. One workflow dispatch selects one or several supported boards. Isolated
   matrix builds, fail-fast false, each image named by board/version/revision.
   Collect checksums, requested/effective configs and verification results.
4. A final aggregation job provides a common download index and board-specific
   image archives. It must distinguish missing/failed images from successful
   ones, and never report all targets passed when some failed.
5. Track original source URLs, immutable revisions, SHA256, licenses, local
   preservation paths and owned mirrors/assets in sources.lock.json. Unknown
   hashes and pending preservation must remain explicitly pending.
6. Preserve upstream source history, kernel, drivers, package archives and
   toolchain under the user's account. Keep component license notices; do not
   assign a blanket new license to third-party sources.
7. Verify builds from the owned sources and assets. A source registry alone
   does not make the repository self-contained.
8. Create a full local backup including required release assets, record hashes
   and total size, then the user chooses external cloud storage.

## Starting source

Repository: https://github.com/Andrzej1973/youhua-wr1200js-nilab
Branch: experimental/Padavan-4.4.198
Observed HEAD: ad5ab44cfc4e021027c9cfbbd1679324e86d929f
Pinned base: vipshmily/padavan-4.4 c25283e915a2a00a763774dd255b14aff997285e
Pinned nilabsent donor: d2c5846299949c57a4e867284069900b561dd2a4

The current workflow still fetches third-party source/toolchain/package URLs.
Nested package recipes require a separate complete dependency inventory.
No device flash or reboot is included in this migration.
