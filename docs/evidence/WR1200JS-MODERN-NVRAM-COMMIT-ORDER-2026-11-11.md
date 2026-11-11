# NVRAM commit ordering candidate

Status: isolated source/host verified; not installed, target/image/runtime unverified.
No ACK changes, router access or production Apply activation.

Pinned source c25283e915a2a00a763774dd255b14aff997285e:
`trunk/linux-4.4.x/drivers/nvram/nvram_linux.c`, nvram_commit lines282–329.
Original SHA256:5bdfa51add776cfe46eabd5c328859d74822220e7772335d08e21b91750190c1.
Transformed SHA256:c62f8aefe3101a37ec14bd4d216cf4f55ba1e93f0e47a4501773f09d38602aae.

`prepare-nvram-commit-order.py <isolated-source-root>` moves the existing
nvram_sem acquisition ahead of snapshot generation. Allocation remains before
locking. Both regeneration failure and normal/write-skip completion funnel
through the existing mutex release before buffer freeing. No spinlock spans
MTD operations. Only occurrences of nvram_sem in this source are its declaration
and commit acquire/release; moving it before nvram_lock adds no opposite nested
acquisition in that translation unit. Full target context still needs checking.
Changed or repeated transformation anchors reject rather than silently patch.

Reproduce host check:
```
PYTHONDONTWRITEBYTECODE=1 python3 tools/webui-preview/check_nvram_commit_order.py /home/andrzej/padavan-build/firmware-source-backup/padavan-4.4-c25283e-git-exact.tar
```

The actual original and transformed C function execute with pthread lock and
injected allocator, snapshot and MTD operations. Controlled scheduling pauses A
after snapshot1, sets RAM2, then starts B. Baseline B snapshots/writes2 before
A acquires the flash mutex; A then writes stale1. Candidate B cannot snapshot
until A completes, then writes2. Both expected outcomes asserted, not inferred
from source text. Generation error, output-buffer allocation failure, optional
read-buffer failure, unchanged partition and flash error paths also pass.
ASan/UBSan, warnings-as-errors: PASS. Owned scratch85100B auto-removed, absence
asserted. This does not prove power-loss safety, actual MTD behavior, kernel
IRQ scheduling or full transaction atomicity. Ordinary RAM writers may still
change values after a snapshot; persisted-snapshot semantics are not a promise
that current RAM equals flash. Batch/user ABI and service sequencing remain open.

CI99642967156122 freshly in_progress for requested5c30f49; not acceptance of
this uninstalled candidate. Next target-build integration and complete bounded
batch ABI, without changing production defaults until those checks pass.

## Target-check integration

`ci_compile_nvram_candidate.py` uses the already configured firmware kernel and
actual source-toolchain prefix. It copies only nvram.c/nvram_linux.c/Makefile to
an owned temporary sibling under drivers, transforms the copied C, and requests
that sibling's nvram_linux.o through Kbuild. No full local kernel build,
link/install/ROMFS or production source replacement. It requires ELF32LE MIPS
ET_REL, retains object/log/report and checks original sources/object, .config,
vmlinux and TRX hashes before/after. Scratch deletion is recorded on failure
as well as success. Optional workflow uploads diagnostics with always(); older
verification revisions lacking this script skip this new check. Same watched
firmware workflow: failure monitor already covers it; first real failure must
be compared with monitor artifact before any parser changes. No speculative
monitor edits. Python syntax and workflow YAML parse passed; target compilation
remains pending until a new exact-source optional run completes.
