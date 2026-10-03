# Firmware port overlays

`padavan-4.4/` contains the active Linux 4.4.198 port: source changes,
package integration, patches and integration helpers. The reusable WR1200JS
build workflow defines which overlays are applied to the pinned base.

`padavan-4.4/candidates/` holds experimental code and isolated probes. A
candidate's presence or successful compilation does not establish inclusion
in the firmware or successful device runtime.

`padavan-ng/` and the older root `patches/` retain historical migration inputs.
They are not a complete description of the active 4.4 build. Source imports
from these paths must follow the current workflow and integration scripts.

Package sources still include external build-time downloads. This repository
is not yet a self-contained source mirror. Track origins and preservation
status in [sources.lock.json](../sources.lock.json) and read
[build system](../docs/BUILD-SYSTEM.md) for actual toolchain inputs.
