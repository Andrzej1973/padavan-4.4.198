# Padavan 4.4.198

Firmware project for YOUHUA WR1200JS and additional individually verified
router profiles. The original project history has been imported into this
repository; the preserved experimental branch contains the same 206 source
commits through ad5ab44cfc4e021027c9cfbbd1679324e86d929f. Main combines that
history with the source registry and delivery records.

## Build and download

Open **Actions → Build selected router firmware → Run workflow**, select
**main**, then choose **all-supported** or **wr1200js**. Each admitted board
builds independently. At the end, download **padavan-4.4.198-router-downloads**
for the combined index, per-board image files, SHA256 checksums and build
status. Individual board artifacts remain available separately.

The combined workflow is under verification. A failed or missing board
must not appear as a successful build in the download index.

## Router profiles

The explicit catalogue is [boards.json](boards.json); configurations live in
[configs.build](configs.build). WR1200JS is enabled for image compilation,
with its existing configuration preserved. Device runtime is still pending.

Mi Mini has a reduced documented profile: Samba/WINS, miniDLNA, Transmission
and Aria are disabled. Its full Linux 4.4 board port is pending, so it is not
yet admitted to firmware builds. Radio object compilation alone does not
prove a bootable firmware image. Further boards will be admitted individually
after their build and image checks are implemented.

## Build system and historical files

The active 4.4 build uses the vipshmily mipsel-linux-uclibc toolchain.
Historical nilabsent variables and build/release workflows are archived under
`docs/archive/legacy-3.4/` and are not active build entry points. The completed
import workflow is archived too. See [build system and toolchain](docs/BUILD-SYSTEM.md)
for source pins, diagnostic jobs and the remaining preservation work.

## Source preservation

[sources.lock.json](sources.lock.json) records initial direct dependencies and
preservation status. The complete nested-package inventory, owned source and
toolchain copies, license inventory and standalone rebuild verification
remain in progress. Builds still use pinned third-party sources at this stage.

See [migration plan](docs/REPOSITORY-MIGRATION-PLAN.md) and
[project delivery scope](docs/PROJECT-DELIVERY-SCOPE.md).

A local Git history backup has been created. A complete source/archive and
toolchain backup remains a separate deliverable. Third-party licenses and
notices are preserved individually. No device flash or reboot is included
in repository migration.
