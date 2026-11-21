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
