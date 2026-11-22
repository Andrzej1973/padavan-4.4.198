# Repository structure

Canonical architecture: [REPOSITORY-ARCHITECTURE.md](REPOSITORY-ARCHITECTURE.md).
The names below are current operational paths; Phase 1 deliberately preserves
them because workflows/generators depend on them.

```text
boards.json                       explicit build admission
configs.build/                    requested board configs + donor reference/
configs/                          owned dependency manifests
sources.lock.json                 provenance, revisions, hashes, owned copies
sources/archives/                 exact durable source inputs, not build output
toolchains/wr1200js/               source-build compiler recipe/config
overlay/padavan-4.4/
  trunk/                          active source replacements and board/DTS files
  ports/                          explicitly integrated package ports
  patches/                        named version-sensitive source patches
  scripts/                        ordered base transformations and image checks
  candidates/                     isolated experiments, not implicit production
tools/
  board-catalog.py                stable CI selector wrapper
  repository/                     shared profile/path validation and audit
  iot/, band-steering/, ...        feature-scoped generators and checks
reference/boards/                 donor snapshots for review only
third_party/                      vendored components with original notices
.github/workflows/                build, comparison, ABI and diagnostics lanes
docs/
  README.md                       navigation
  evidence/                       smallest durable dated verification evidence
  runtime/                        historical device observations
  history/, archive/              historical checkpoints and old workflows
PROJECT_STATUS.md, CODEX_HANDOFF.md current shared-workspace coordination
```

## Stage 2 layout decisions

The reference tree bundles a buildable `trunk/`, compiler sources under
`toolchain/` and bootloader sources under `uboot/`. This repository assembles
Linux 4.4.198 from locked inputs and the WR1200JS overlay. Keep
`overlay/padavan-4.4/trunk/`, `toolchains/wr1200js/` and the existing board
catalogue as the canonical locations. A root SDK tree or Docker entry point
would require a separate build contract. Bootloader ownership stays separate
from firmware image assembly.

The standalone IE length and slot lookup models now live in `tools/iot/`,
alongside the checks they support. Their active navigation is in
[Local Nim helper notes](LOCAL-NIM-HELPER-NOTES.md). CI has no direct
references to either old root path. Historical records retain their original
command paths.

Generated assembled source, ROMFS, compiler trees, extracted CI artifacts and
native fixture binaries belong in runner/temp directories, not new permanent
source directories. Preserve uncertain/unowned local files. Phase scratch cleanup
is narrow and does not delete backups, references or unfinished work.

A local baseline inventory enumerated text-file nilabsent mentions, exact
duplicate groups, directory counts/sizes and source-path dependencies. Its raw
untracked-path list is retained locally because it includes owner-provided and
unfinished workspace material; it is not a repository artifact. Duplicate bytes
in donor snapshots or dated evidence are not automatically redundant: deleting
them can break provenance or citations.
[Migration plan](REPOSITORY-MIGRATION-PLAN.md) explains the no-mass-move decision.
