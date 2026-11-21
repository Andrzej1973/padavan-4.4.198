# Repository architecture — Phase 1, 2026-11-08

This repository is a **versioned firmware assembly layer**, not a complete kernel
checkout. The active image recipe fetches vipshmily/padavan-4.4 at
c25283e915a2a00a763774dd255b14aff997285e, applies our overlay and ordered source
transformations, selects WR1200JS, builds kernel/userspace and checks ROMFS/TRX.
The exact source pin and owned inputs are recorded in [sources.lock.json](../sources.lock.json).
A source recipe, compiler success and runtime acceptance are separate facts.

## Operational boundaries

| Layer | Canonical location | Responsibility |
|---|---|---|
| Build admission | [boards.json](../boards.json) | Only explicitly enabled boards receive image jobs |
| Requested policy | [configs.build](../configs.build/) | Board package/config requests, not proof of support |
| Board hardware | [WR1200JS board](../overlay/padavan-4.4/trunk/configs/boards/WR1200JS/) | ID, GPIO, kernel configuration |
| Kernel/SoC integration | [kernel overlay](../overlay/padavan-4.4/trunk/linux-4.4.x/) | DTS/layout, selected source replacements |
| Shared firmware/services | [overlay trunk](../overlay/padavan-4.4/trunk/), [ports](../overlay/padavan-4.4/ports/), [tools](../tools/) | Shared implementation and explicit generators |
| Experimental board/driver work | [candidates](../overlay/padavan-4.4/candidates/), [IoT tools](../tools/iot/) | Isolated source candidates, not automatic image inclusion |
| Source preservation | [sources](../sources/), [toolchain profiles](../toolchains/) | Owned exact archives, provenance and compiler recipes |
| Donor evidence | [reference](../reference/) | Read-only comparison snapshots; no automatic target discovery |
| Evidence/coordination | [docs](./), [status](../PROJECT_STATUS.md), [handoff](../CODEX_HANDOFF.md) | Dated results and single-writer context |

## Reorganization implemented locally

`tools/board-catalog.py` stays the stable command/output entry point. Its
admission logic is consolidated in `tools/repository/board_catalog.py`, shared
with the new architecture validator. This is one module move with a compatibility
wrapper, not a second catalogue. The original boards.json schema is unchanged.
Validation checks board/config identity, enabled recipe, required source files,
WR1200JS SoC/kernel selectors, existing DTS/include and exact flash partitions.

The existing selection job now has a lightweight validation step and an uploaded
report before board selection. The validator and its negative fixtures use only
the standard Python library. No code source tree, calibration data, bootloader,
partition or kernel/Wi-Fi runtime path is moved or changed in Phase 1.

## Intentional limits

WR1200JS is the active image-build reference, not a claim of complete production
IoT acceptance. Mi Mini and Mi-4 remain pending. SoC similarity cannot authorize
another board's flash layout, GPIO, Factory addresses, Wi-Fi chip or USB controls.
Common/SoC/board boundaries are explicit ownership rules on existing files;
empty common/SoC directories are not created. Future extraction requires proven
shared code, callers and tests. See [board architecture](BOARD-PROFILE-ARCHITECTURE.md).
