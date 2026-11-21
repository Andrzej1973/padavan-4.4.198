# lekswrt Padavan / Prometheus donor audit — 2026-10-27

Source: https://github.com/lekswrt/padavan-ng-rt-n56u-xiaomi-prometheus-openwrt
Pinned inspected `master`: `afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295`
(last source commit 2020-12-11). This is a source inspection, not a build or
router test. The GitHub recursive tree response was truncated; conclusions
below come from the named files and directory listings, not a complete code
inventory. No donor code was imported.

## Useful concepts

- `prometheus/start.sh` is an interactive menu for board/config selection,
  toolchain and firmware build, archives, modules, and status. Its
  `configs/routers/mi-mini.config.sh` is a concrete historical Mi Mini profile.
  Reuse the *workflow idea* at the final offline-build stage: select only
  admitted boards from our verified catalog, display pinned source/toolchain
  revisions, build and image-gate results, and keep an artifact manifest.
- `Dockerfile` records a Linux package/toolchain preparation recipe and
  `docker-compose.yml` provides an interactive container entry. A pinned
  Ubuntu 24.04 WSL 2 environment is a simpler initial Windows 10 candidate
  for our project; a container is optional after comparing actual dependencies.
- The Classic `trunk/user/www/n56u_ribbon_fixed` and its `bootstrap/css`
  offer historical UI references. Preserve our Classic behavior and separately
  implement the approved Modern design. Evaluate any visual element against
  current backend, localization, board capability, responsive behavior and
  license before reuse.

## Reasons not to copy the script or themes directly

- README reports Ubuntu 18.04 as tested and a WSL Ubuntu 20.04 firmware-build
  failure (`intltoolize: not found`). It does not establish WSL 2 success.
- `prometheus/start-99.sh`, `scripts/up1.sh`, `scripts/up2.sh` and `start.sh`
  install packages or download update archives from the network, including
  HTTP endpoints. `Dockerfile` clones a moving external branch. This cannot
  meet our pinned, offline, checksum-verified build contract as-is.
- `start.sh` offers flashing, U-Boot and EEPROM operations, and includes an
  `sshpass`/disabled host-key-check path. Exclude these from a build-only
  launcher. Never make menu selection perform router writes implicitly.
- The advertised grey, blue, yellow and white theme set is selected from
  `full-theme-pack*.zip` in Prometheus. The inspected Classic tree has
  `bootstrap/css`, but no `common-theme` directory at the checked path.
  Locate the actual ZIP, origin and licenses before considering visual reuse.
- GitHub's repository metadata did not expose a repository-wide SPDX license.
  Inspect component licenses and provenance before copying any files.
- Mi Mini's 2020 profile and old kernel/toolchain are references only; they do
  not validate current WR1200JS or our later Mi Mini image.

## Deferred adoption gate

After WR1200JS acceptance, Mi Mini and the agreed source consolidation:
inventory the Windows 10 version, WSL 2 and Ubuntu 24.04 host; pin Linux
packages, compiler, source, profiles and checksums; keep build work on the
Linux filesystem; provide a PowerShell launcher that invokes a small
non-flashing Linux build script. Verify from a clean directory with network
disabled, compare config, ROMFS, TRX and hashes with the reference, and record
any differences. Do not call the workflow portable or offline before those
tests pass. Keep the existing project sequence unchanged.

## Inspected sources

- https://github.com/lekswrt/padavan-ng-rt-n56u-xiaomi-prometheus-openwrt/blob/afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295/README.md
- https://github.com/lekswrt/padavan-ng-rt-n56u-xiaomi-prometheus-openwrt/blob/afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295/prometheus/start.sh
- https://github.com/lekswrt/padavan-ng-rt-n56u-xiaomi-prometheus-openwrt/blob/afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295/prometheus/start-99.sh
- https://github.com/lekswrt/padavan-ng-rt-n56u-xiaomi-prometheus-openwrt/blob/afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295/prometheus/configs/routers/mi-mini.config.sh
- https://github.com/lekswrt/padavan-ng-rt-n56u-xiaomi-prometheus-openwrt/blob/afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295/Dockerfile
- https://github.com/lekswrt/padavan-ng-rt-n56u-xiaomi-prometheus-openwrt/blob/afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295/docker-compose.yml
- https://learn.microsoft.com/en-us/windows/wsl/install-manual
- https://learn.microsoft.com/en-us/windows/wsl/wsl2-about
