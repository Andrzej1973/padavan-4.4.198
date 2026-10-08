# Padavan 4.4.198

Custom Padavan firmware for **YOUHUA WR1200JS**, based on Linux **4.4.198**.
The project preserves our router configuration while adapting selected packages,
drivers and web interface features to the pinned Padavan 4.4 source.

The original Padavan / rt-n56u project was created by
[Padavan](https://bitbucket.org/padavan/rt-n56u).
This repository contains our build workflows, configurations, overlays and
integration scripts. The workflows fetch the firmware source and apply these
changes before compiling it.

## Firmware base and source origins

| Component | Source | Pinned revision / verification |
| --- | --- | --- |
| Linux 4.4 kernel, Padavan userspace and board templates | [vipshmily/padavan-4.4](https://github.com/vipshmily/padavan-4.4) | [c25283e915a2a00a763774dd255b14aff997285e](https://github.com/vipshmily/padavan-4.4/tree/c25283e915a2a00a763774dd255b14aff997285e) |
| Selected package sources and feature donors, including AmneziaWG | [nilabsent/padavan-ng](https://github.com/nilabsent/padavan-ng) | [d2c5846299949c57a4e867284069900b561dd2a4](https://github.com/nilabsent/padavan-ng/tree/d2c5846299949c57a4e867284069900b561dd2a4) |
| MIPS little-endian uClibc cross compiler | [vipshmily toolchain release](https://github.com/vipshmily/padavan-4.4/releases/tag/toolchain) | Archive SHA256 recorded in [sources.lock.json](sources.lock.json) and checked before extraction |
| Earlier project development history | [youhua-wr1200js-nilab](https://github.com/Andrzej1973/youhua-wr1200js-nilab) | Imported through ad5ab44cfc4e021027c9cfbbd1679324e86d929f |
| Individual package archives | Upstream URLs in the pinned package recipes and our source registry | Preservation and checksum coverage are recorded per component |

**Nilabsent is a component donor for this project.** The production kernel and
main source tree come from the pinned **vipshmily Padavan 4.4** base.
The donor's Linux 3.4 firmware and its historical toolchain settings are not
the active build base.

The exact direct dependency records are in [sources.lock.json](sources.lock.json).
A preserved copy of the DoH donor archive is already in
[sources/archives](sources/archives), with its provenance and license recorded
under [sources](sources).

## Added and adapted features

The WR1200JS profile currently requests:

- WireGuard and AmneziaWG, with their firmware integration and web controls.
- OpenSSL 3.5, HTTPS and TLS support for dynamic DNS.
- Stubby DNS-over-TLS, DoH proxy and Privoxy.
- WPAD, vendor logo and Russian / Ukrainian web resources.
- FQ-CoDel in the kernel configuration; CAKE/SQM is excluded from the current profile.
- IPv6, USB support and selected filesystem / networking utilities.
- VLMCSD, iPerf3, ZeroTier and Shadowsocks components.

The authoritative package selection is
[configs.build/wr1200js.config](configs.build/wr1200js.config).
Commented assignments are disabled; uncommenting a supported selector requests
its inclusion in a new firmware build. Including a package does not necessarily
start its service.

SmartDNS and size optimization are documented as commented options.
TOR, its GeoIP databases and ZAPRET packages are deferred to a later stage.
CPU sleep, CPU frequency scaling and the 900 MHz overclock selector are absent
from the central WR1200JS profile. Isolated MT7621 systick investigation does
not establish a production runtime feature.
RSSI Kick and other roaming behavior still require final verification.
Band Steering driver, daemon and coordinated Wi-Fi changes are isolated
candidates. Snapshot tests and isolated compilation do not establish their
installation in the normal image or operation on a router. See the
[radio snapshot evidence](docs/evidence/RADIO-SNAPSHOT-37718587396.md).

Compilation, image inspection and operation on a physical router are tracked
separately. A successful build does not establish that every selected service
has been tested on the device.

## Router profiles

| Router | Firmware build status |
| --- | --- |
| YOUHUA WR1200JS | Enabled; successful firmware builds recorded, Linux 4.4 device runtime verification pending |
| Xiaomi Mi Mini | Reduced configuration available; board port pending, excluded from normal firmware builds |
| Xiaomi Mi 4 | Matching package profile available; board recipe and image build pending, excluded from normal builds |

The catalogue is [boards.json](boards.json); profiles are in
[configs.build](configs.build). WR1200JS is the current priority.
Mi Mini disables Samba/WINS, miniDLNA, Transmission and Aria.

Additional upstream router configurations will be preserved unchanged at final
delivery, with their original source revision. Reference profiles do not imply
verified compatibility with our added features or admission to the build matrix.

## Build firmware with GitHub Actions

1. Fork this repository.
2. Enable GitHub Actions in your fork if GitHub asks you to do so.
3. Edit the appropriate configuration under `configs.build/`.
4. Open **Actions → Build selected router firmware → Run workflow**.
5. Select **main** and choose **wr1200js** or **all-supported**.
6. Wait for the build, image checks and packaging jobs to finish.

`all-supported` selects only profiles admitted in `boards.json`.
It currently builds WR1200JS; it does not enable pending router ports.

The firmware compilation job uses **Ubuntu 22.04**.
Selection, download aggregation and final ZIP packaging use **Ubuntu 24.04**.
Exact build dependencies and commands are maintained in the
[WR1200JS workflow](.github/workflows/build-padavan-4.4-wr1200js.yml).
See [BUILD-SYSTEM.md](docs/BUILD-SYSTEM.md) for further details.

## Download the firmware

In a successful workflow run, download the artifact **named after the firmware
image**. GitHub provides it as a ZIP with exactly two files:

```text
WR1200JS_….trx
wr1200js.config
```

The configuration is the central requested profile used by that build.
The `.trx` file is the firmware image; the ZIP itself is a download container.

Technical reports, effective kernel / firmware configurations and dependency
checks remain in separate diagnostic artifacts. The
`padavan-4.4.198-router-downloads` artifact is a combined index and checksums,
rather than the minimal per-router ZIP.

The minimal per-router ZIP contract was verified by inspecting a successful
artifact and matching its configuration bytes to the source revision. See the
[build and ZIP evidence](docs/evidence/BUILD-37717393036-AND-ZIP-CONTRACT.md).
This packaging result does not establish current firmware feature selection or
router runtime behavior. Failed or missing builds must not be reported as
successful firmware downloads.

## Repository layout

- `configs.build/` — central firmware profiles.
- `boards.json` — admitted boards and pending profiles.
- `overlay/padavan-4.4/` — board changes, feature ports and integration scripts.
- `.github/workflows/` — active build and diagnostic workflows.
- `tools/` — selection, verification and packaging helpers.
- `sources.lock.json` and `sources/` — dependency provenance and preserved assets.
- `docs/` — build evidence, port notes and delivery scope.
- `docs/archive/legacy-3.4/` — historical workflows and variables.

## Source preservation and reproducibility

Work is in progress to preserve complete source trees, nested package archives,
toolchain files and licenses under the project owner's account and in a local
backup. A local Git history backup has been created.

**The build is not yet verified as self-contained.** Some dependencies are still
fetched from third-party repositories and release servers. The source registry
states what has been preserved and what remains outstanding.

See the [repository migration plan](docs/REPOSITORY-MIGRATION-PLAN.md) and
[project delivery scope](docs/PROJECT-DELIVERY-SCOPE.md).

## Contributing

Fork the repository and submit a pull request describing the target board,
source provenance and changes. Record build results separately from physical
device tests. Preserve upstream license notices and document new dependencies.

Do not add an unverified board to the enabled build catalogue. Existing package
recipes may need adaptation when enabling options that have not yet been built
with this project's configuration.

## Credits and licenses

Thanks to Padavan, the Padavan 4.4 contributors, vipshmily, nilabsent and the
upstream authors of the included packages. Their original licenses and copyright
notices continue to apply to their respective components.

Firmware is provided without warranty. Use an image matching your exact hardware
and plan recovery before installing experimental firmware.
