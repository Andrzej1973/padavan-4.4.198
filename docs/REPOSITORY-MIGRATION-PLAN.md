# Repository architecture migration — Phase 1, 2026-11-08

This plan concerns the existing shared checkout. The older repository-import
plan is preserved below as historical context.

1. Inventory tracked/untracked files, exact duplicates, upstream mentions and
   path dependencies without deleting or moving donor/unfinished material.
2. Compare current nilabsent architecture at an immutable revision with our
   pinned Linux 4.4 assembly workflow; retain the distinct build model.
3. Extract catalogue validation into tools/repository while retaining the
   tools/board-catalog.py entry point and its JSON/output-file contract.
4. Add required-file, config, existing WR1200JS DTS/layout, pending-board and
   documentation-link checks; integrate the check into selected-board CI.
5. Document canonical component ownership and future board admission. Keep
   overlay/config/profile/image paths unchanged; no bulk tree migration.
6. Run local regression and output compatibility checks. Record the existing
   compiler A/B run separately: it cannot cover unpublished Phase 1 edits.
7. Review this local package before any commit/push, as explicitly required
   by the owner's attached prompt. After publication, verify the exact SHA in
   selected-board CI and a full WR1200JS image build.

Rollback before publication is a narrow restoration of the task's selector,
workflow and documentation changes, preserving all pre-existing dirty work.
No source/driver/partition migration or history rewrite is involved.
Phase 1A is a recommendation only and requires a separate task. See the
[migration report](REPOSITORY-MIGRATION-REPORT.md).

## Stage 2 — WR1200JS layout and verification

| Change | Published evidence |
| --- | --- |
| Move the standalone IE length and slot lookup models from the root into tools/iot/ | 45cbd61a, Git R100 on both files, both Nim syntax checks passed |
| Map the workflow, source lock, board profile and overlay entry points | 6901b8ca, local links resolved |
| Make active local documentation links checkable in a light workflow | e3508036, [navigation CI passed](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/45014362142) |

The existing Linux 4.4.198 build assembles the pinned SDK and overlay during
CI. The source lock, board profiles, compiler and overlay paths remain the
inputs to that build. The reference repository's root SDK, Docker and
bootloader layout would change those responsibilities.

[Standard WR1200JS build for the restructure revision](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/45014362085)
passed for e350803655ab3fb28b1633a4010f47c1663d0596. Board selection,
WR1200JS compilation, firmware ZIP and download aggregation all succeeded.
This verifies the Standard build path after the reorganization. IoT and
Hybrid Modern feature acceptance is tracked separately.

---

## Historical repository import plan (2026-10-03)

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
