# Build system and toolchain

## Supported firmware entry point

Use **Actions → Build selected router firmware**, branch **main**.
The catalogue in `boards.json` explicitly controls admission to firmware
builds. WR1200JS is currently admitted. Mi Mini has a config but its complete
board port is pending; it is not a selectable working firmware target.

The common workflow calls the WR1200JS recipe as a reusable workflow. Each
admitted board receives an isolated build. The final download artifact holds
the index, images, SHA256 checksums and build status. Failed or missing boards
must not be described as successful. Check the workflow conclusion as well
as the per-board status before treating an image as build-verified.

## Actual Linux 4.4.198 inputs

- Base: `vipshmily/padavan-4.4`, commit
  `c25283e915a2a00a763774dd255b14aff997285e`.
- Donor sources: `nilabsent/padavan-ng`, commit
  `d2c5846299949c57a4e867284069900b561dd2a4`.
- Toolchain archive:
  https://github.com/vipshmily/padavan-4.4/releases/download/toolchain/mipsel-linux-uclibc.tar.xz
- The build uses `TOOLCHAIN=mipsel-linux-uclibc` and records the downloaded
  toolchain SHA256 in its artifact. The archive content is not yet enforced
  against a committed expected SHA256; source preservation must close this gap.

The old nilabsent uClibc-ng 1.0.58 URL in the archived `variables` file is
historical input to the former build system. It is not used by the active
4.4 workflow, and compatibility with this port has not been verified.
Source provenance and preservation status live in `sources.lock.json`.

## Diagnostics

- **Diagnostic: upstream K2P control build** checks the upstream base. Its
  images are for K2P, not WR1200JS.
- **Diagnostic: Mi Mini kernel candidate** checks experimental kernel code.
  It does not produce a validated Mi Mini firmware image.

Compilation is separate from device runtime verification. Linux 4.4 boot and
runtime on the user's hardware remain unverified.

## Historical files

`docs/archive/legacy-3.4/` preserves the old workflow files and `variables`
byte for byte. They are not active GitHub Actions workflows. Their original
relative paths belong to the historical revision and cannot be treated as a
current build recipe. The completed history-import workflow is preserved in
`docs/archive/migration/` and is no longer an active Actions entry point.
