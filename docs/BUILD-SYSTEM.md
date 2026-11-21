# Build system and toolchain

## Active recipe and source assembly

[Build selected router firmware](../.github/workflows/build-multiple-boards.yml)
uses [boards.json](../boards.json) and the stable catalogue selector. WR1200JS
is admitted; Mi Mini and Mi-4 remain pending. Choose the intended branch
explicitly; branch changes are not present on main until merged.

The reusable [WR1200JS recipe](../.github/workflows/build-padavan-4.4-wr1200js.yml)
assembles Linux 4.4 from vipshmily/padavan-4.4 at
c25283e915a2a00a763774dd255b14aff997285e, donor nilabsent/padavan-ng at
d2c5846299949c57a4e867284069900b561dd2a4 and this repository's explicit overlay
and transformation scripts. [sources.lock.json](../sources.lock.json) records
provenance. The local reference snapshots are not a complete build tree.

The Phase 1 local CI edit adds catalogue/layout/document checks before matrix
selection and uploads repository-validation.json even on failure. It is not
active remotely until the package is published. Image checks remain in the
existing recipe; this structural check does not replace compilation.

## Preserved control and source-built candidate

The control compiler remains GCC 10.5/uClibc 1.0.43. Its hash-pinned archive is
preserved in this account's build-toolchains-v1 release and reused through the
Actions cache/API asset path. The historical foreign download URL is
provenance, not the intended normal source. K2P diagnostics use a distinct
preserved compiler; their images are never WR1200JS acceptance evidence.

[Toolchain recipes](../toolchains/) and [toolchain tools](../tools/toolchain/)
produce an independent GCC 10.5/uClibc 1.0.48/Linux 4.4.198 candidate. Source
build run 42467546674 succeeded; its publish job was skipped, so its Actions
artifact must not be described as a published compiler release.

[Compiler A/B](../.github/workflows/compare-toolchain-firmware.yml) builds
control and candidate at one source SHA and compares requested/effective
config hashes, image metadata, ELF inclusion, architecture/ABI, interpreter
and dependency metadata. File hash/size changes are reported separately.
The comparison does not establish physical stability. Promote the development
compiler only after software results and review; the owner deferred physical
acceptance until IoT and the new WebUI are ready.

## Package inputs and failure diagnostics

[Owned dependency manifest](../configs/owned-build-dependencies.json) pins
mbedTLS, libqrencode, PCRE2 and AmneziaWG. Their small source archives are in
[sources/archives](../sources/archives/); the preparer verifies SHA256 and seeds
package caches without a network fallback. This does not imply that all other
base/donor inputs are offline or mirrored.

On CI failure, inspect the failure-monitor report when available and verify
its suspected cause against the original failed step/artifact. Never blindly
rerun or modify source from a bounded monitor excerpt. Follow separate
standard/optional lanes and exact SHA/input deduplication in [AGENTS.md](../AGENTS.md).
Full firmware/kernel/module builds run on GitHub; local checks stay lightweight.

The [architecture](REPOSITORY-ARCHITECTURE.md) and
[board admission contract](BOARD-PROFILE-ARCHITECTURE.md) identify source,
profile, image and runtime boundaries. Legacy 3.4 workflows under
[the archive](archive/legacy-3.4/) are historical, not active recipes.
