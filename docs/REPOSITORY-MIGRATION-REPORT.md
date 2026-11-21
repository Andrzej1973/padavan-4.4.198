# Repository Phase 1 report — 2026-11-08 (reviewed 2026-11-21)

Status: Phase 1 implementation and lightweight verification are recorded below.
The detailed local inventory and Phase 1A call-site list remain outside Git
because they enumerate untracked owner/workspace paths. Any local commit is not
published; exact-SHA GitHub validation and full WR1200JS image checks still need
to run after a separately authorized push. No image or device acceptance is
claimed. Phase 1A source extraction has not started.

## Audit and decision

The private initial inventory records baseline 08b15eb27331fb28f106fd7d9f19df16c9d1da14, 4259 tracked files,
49 text files mentioning nilabsent and 432 exact duplicate groups. These are
snapshot counts, not a deletion list. Repeated partition/SKU donor files can
serve distinct provenance paths; untracked files include unfinished shared work.
No donor, source, historical evidence, archive or other task's files were deleted.

Our repository assembles a pinned 4.4 tree; current nilabsent contains a full
3.4 source tree. [The comparison](NILABSENT-ARCHITECTURE-ANALYSIS.md) records
upstream c29b12da69b1593a6e8cf65cd43767fc99bb6386. Keep stable overlay/config
paths and explicit source transforms. Copying trunk or relocating all board
files would introduce extensive workflow/script dependencies without proving
hardware support. There is no new common/SoC placeholder directory.

## Implemented changes

- tools/board-catalog.py remains the stable CLI and output-file entry point;
  its logic now uses tools/repository/board_catalog.py.
- New tools/repository/audit.py provides inventory and fail-closed validation:
  catalogue/config identity, required files, current WR1200JS DTS/layout and
  image-size agreement, local documentation links and owned archive hashes.
- New tools/repository/check-audit.py checks valid selection and rejects pending
  boards, corrupt IDs/paths/schema/SoC, missing source, DTS/layout/image drift
  and broken local links. No new Python packages are required.
- .github/workflows/build-multiple-boards.yml runs validation before selection,
  preserves the report and includes the module in its push path filters.
- Updated docs/README.md, REPOSITORY-STRUCTURE.md, REPOSITORY-MIGRATION-PLAN.md
  and BUILD-SYSTEM.md; added REPOSITORY-ARCHITECTURE.md,
  NILABSENT-ARCHITECTURE-ANALYSIS.md, BOARD-PROFILE-ARCHITECTURE.md and this report.
- Added scoped validation and public CI evidence under docs/evidence. The local
  inventory, which includes untracked owner/workspace paths, is retained outside
  Git; the Phase 1A call-site report is also retained locally.

No board catalogue admission, requested board configuration, driver, Wi-Fi/IoT
runtime, bootloader or flash layout was changed. Mi Mini and Mi-4 remain pending.
The unrelated dirty changes recorded at entry remain outside this package.

## Verification and CI boundary

Local commands (from the repository root):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/repository/check-audit.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/repository/audit.py --report docs/evidence/REPOSITORY-PHASE1-VALIDATION-2026-11-08.json
python3 tools/check-owned-build-dependencies.py
```

Regression and dependency checks passed. The validation JSON records the
source/profile/path/link/archive result; it is not a compiled DTB or image.
Old/new selector stdout, selected-boards.json and GITHUB_OUTPUT are compared
in isolated temporary directories for all-supported and explicit WR1200JS.
Shared checkout outputs are not overwritten for this test.

Existing [compiler A/B run 42476812968](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/42476812968)
builds baseline SHA 08b15eb27331fb28f106fd7d9f19df16c9d1da14. The control firmware job
128719900626 succeeded; candidate job 128722752808 failed at step 28 before firmware compilation.
The original traceback is tarfile.LinkOutsideDestinationError for archive member
./lib/bfd-plugins/liblto_plugin resolving outside the install prefix. The data
extraction filter correctly refused it. Comparison was skipped; overall A/B
failed. Later missing EoIP/StrongSwan artifacts are consequences, not the cause.
No matching monitor run was observed: the deployed main workflow does not yet
watch compiler comparison, although the branch list does. See the
[exact CI evidence](evidence/REPOSITORY-PHASE1-CI-2026-11-08.json).
It cannot cover this unpublished Phase 1 package. After authorized publication,
require selected-board validation and full WR1200JS image checks at the exact
new SHA. Physical acceptance remains separate and deferred by the owner.

## Residual work and Phase 1A recommendations

1. Inspect the candidate archive link graph and correct its packaging/relocation
   with a regression fixture, then rebuild/retest A/B before any compiler
   promotion. Do not disable the extraction safety filter. This is a separate
   toolchain fix, not grounds for risky repository migration.
2. Review and authorize publication of this coherent local package, then check
   exact-SHA CI/image evidence. Local acceptance is not full build acceptance.
3. For a later Phase 1A, inventory ordered source transformations and their
   callers before extracting any proven common board logic. Avoid a second
   board schema; extend current profiles/capability manifests when evidence exists.
4. Audit each future Xiaomi revision independently, especially NAND/SPI,
   Factory/calibration, Ethernet, GPIO/USB and radio lifecycle. WR1200JS remains
   the primary platform; mandatory IoT and its outstanding acceptance are retained.
5. Historical migration, donor pruning and unrelated Mi Mini/IoT changes remain
   separate tasks. This phase grants no permission to remove them.

Scratch cleanup: regression directories are created with TemporaryDirectory
and removed automatically. Narrow audit-only /tmp indexes and the old selector
comparison copy are removed after verification; retained JSON evidence is small
and needed to reproduce/review the claim. No firmware/toolchain tree was created
locally for Phase 1.
