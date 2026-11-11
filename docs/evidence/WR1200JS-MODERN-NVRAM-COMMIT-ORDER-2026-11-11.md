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

## Batch target composition follow-up

`prepare-nvram-batch-candidate.py` composes the existing commit-order correction
with the exact host-tested batch core after actual _nvram_free definition.
The candidate exposes a global but unexported/uncalled batch symbol only to
prevent dead-code elimination during the target object check. It adds no ioctl,
userspace command, flash call or production hook. The CI object check now
requires defined text symbol wr_nvram_batch_candidate using the target nm and
records batch-core SHA256. Thus a passing check must compile the batch body,
not merely an unused include that the compiler discarded.

Fresh guarded composition of pinned source SHA256:
2298cbef2e3b9d756bdccd8deef6124a6216ceb9163f874c65ad471c935f9c83.
Host fixture asserts exact core inclusion and placement, and rejects repeated
or altered allocator anchors. Actual-core ASan/UBSan cases, including200
concurrent-writer trials, pass again. Scratch126658B removed, absence asserted.
Python syntax and whitespace checks pass. This updated composition is not
covered by already running997 or996; needs its own exact-source target run.
Kernel ABI, userspace ownership/copy, persistence policy and service integration
remain unfinished; no production activation or runtime acceptance.

## Bounded request decoder

Unpublished candidate layout in nvram-batch-wire.h: fixed5264 bytes, version1,
count1–16, sixteen328-byte records. __u32 metadata, no pointers, explicit
reserved bytes; 64-byte name and129-byte expected/value fields including NUL.
Whole request must be one immutable kernel-owned copy. Decoder checks exact
size/layout/version, flags, reserved/unused records, canonical zero string tails,
name syntax and duplicates before changing any output pointer. Absent check/set
fields must be empty. Native-endian local ABI only; this is not a wire-network
protocol. No ioctl number has been allocated or exposed.

Host tests execute valid decoded request through actual allocator/hash batch.
Ten malformed field cases and short/oversized requests reject with untouched
output. Existing allocator faults/concurrent cases still pass under ASan/UBSan.
Composed candidate source SHA256:
c3ac4e68c4f1c20ba50d91c5c11a194719c0009739810fb4bb079dab4719d1bc.
Fresh scratch155533B auto-removed, absence asserted. CI now requires compiled
decoder text symbol and records layout/decoder hashes. Still pending: privileged
user-copy wrapper, explicit copied-buffer wiping, ioctl admission, userspace
adapter and service integration. Decoder alone is not authorization or safe
user memory access; never pass a user pointer directly to it.

## Privileged owned-copy entry body

`nvram-batch-user.c.inc` checks CAP_SYS_ADMIN before allocation/copy because
this generic NVRAM operation can modify system keys, not just network values.
Uninitialized driver refuses EAGAIN. kzalloc then one copy_from_user obtains a
fixed-size owned request; partial-copy EFAULT still funnels through explicit
buffer wiping before kfree. Decoder outputs borrow only that owned copy.
Result is changed-count or errno; no flash commit, service operation, user copy
back, ioctl dispatch, export or production hook is introduced. The candidate
includes actual Linux capability/uaccess declarations for eventual target checks.

Host executes the actual entry body with explicit capability/allocation/copy
substitutes. It tests denied permissions with zero copy calls, startup refusal,
allocation failure, partial-copy failure, malformed/stale requests, mutation of
original user buffer after copy, and complete owned-buffer wipe before every
free. ASan/UBSan and prior200 concurrent/core/decoder tests pass. This does not
validate real copy_from_user faults, credentials or kernel ABI execution.
Composed candidate source SHA256:
0f11b2eb6a04753b2347a6c377a0eb84189aff7a54e2dbbac215cb5c0ac7b2e6.
Scratch173094B removed and absence asserted. Kernel-object CI now also requires
the actual wr_nvram_user_batch text symbol and records entry-body hash.
Next: versioned ioctl admission and userspace adapter, then complete HTTP/RC
integration with honest RAM/flash/service results. Production remains unchanged.

## Isolated ioctl admission and userspace client

The latest candidate supersedes earlier no-dispatch checkpoints: generated
`dev_nvram_ioctl` now routes WR_NVRAM_IOCTL_BATCH_V1 to the privileged owned-copy
entry. Header defines _IOW('N',0x51,struct wr_nvram_wire_request); compute it with
target ioctl headers, never hardcode a host numeric encoding (MIPS encodings
can differ). Existing four numeric commands are untouched; unknown commands
still EINVAL. This is a new explicitly defined Linux API, not a firmware command.
It is present only in generated candidate source, not the production kernel.

Userspace `nvram-batch-client.h` takes an already owned device descriptor and
caller-owned request. It attempts ioctl once, rejects impossible changed counts,
and leaves the output unchanged on error. EINVAL/ENOTTY on old kernels do not
fall back to per-field SET; EINTR is not retried. Caller must wipe its own packet,
classify uncertain syscall/transport outcomes honestly and reload configuration;
no response claims flash durability or radio acceptance. No automatic request
replay is introduced. Request descriptor lifetime/HTTP binding still pending.

Host executes actual generated ioctl switch with legacy-handler substitutes:
all four old paths retain return routing; unknown command rejects; batch path
checks permission and executes owned-copy core. Actual client adapter tests nine
error classes including EINTR/unsupported kernel, bounded success and unchanged
error output with exactly one attempt. ASan/UBSan plus previous suites pass;
latest host scratch194958B removed, absence asserted. Kernel/user target ioctl
encoding agreement and real target compilation remain unverified. No runtime
or ABI availability is claimed for released firmware.

## Compiled kernel/client ABI comparison gate

The shared header can emit four target-native u32 constants into a dedicated
.wr_nvram_abi ELF section: request size, item size, ioctl command, version.
Generator emits the kernel record. CI also compiles actual userspace adapter
through its actual libc headers using the source MIPS compiler. Target objcopy
extracts the section from both objects; exact16-byte layout and known sizes/
version are checked, then both records must be identical. This detects kernel/
libc ioctl encoding disagreement without running target code or assuming the
host command number. Both object files and client compile diagnostics retained.
Overall target_compiled becomes true only after kernel/client compilation and
ABI comparison pass. Neither object is linked or installed into firmware.

Native host executable and separately compiled actual userspace adapter record
match: request5264B, item328B, version1. Native ioctl number1418743377 is host
only, not a claimed MIPS command. Full ASan/UBSan host suites pass. Composed
candidate hash4961b8457d9f2975a9470541e5e24fb754ccdea36b2800718cfaf5ed702af554.
Scratch197441B removed and absence asserted. Python syntax/whitespace pass.
MIPS gate execution still pending; no device/runtime evidence added.

## Guest transaction planner

New uninstalled guest-batch.h runs existing Guest metadata/value/snapshot/key
admission, then owns a fixed request with thirteen public snapshot comparisons.
Posted fields are compare+set; omitted optional open-security fields compare
only. Keep-key is a fourteenth check-only item against the owned admitted key:
concurrent key change rejects the batch instead of overwriting the newer key.
Explicit change adds set-only key intent, deliberately replacing current key;
open/keep adds no key item and neither reads nor clears dormant credentials.
All temporary plan/packet copies are wiped; failed planning leaves caller
output untouched. The CGI callbacks must refer to an immutable admitted request.
This planner performs no ioctl, flash, notification or production mutation.

Tests compose actual admission/planner with actual decoder/hash/allocator/core
for rt/wl x keep/change/open. Concurrent key changes reject all public writes;
restoring expected key permits the batch. Main/IoT sentinel values stay unchanged.
After restoring public snapshots, invalid public data rejects before secret
read and leaves caller output unchanged. Missing optional security values on
open auth are retained through check-only entries. ASan/UBSan prior cases pass.
Actual userspace compile probe now also compiles the planner (including existing
validation headers), with source hashes in target report. Native compile and
ABI comparison pass; target execution still pending. Final scratch304708B
removed, absence asserted. Next: bind admitted HTTP lifecycle to exactly one
batch call and reconcile service/commit response without per-field fallback.

## Apply/notification admission boundary

New check_guest_notification_policy.py extracts actual Guest-control and common
fallback clauses from pinned validate_asp_apply and executes the full actual
ej_notify_services with notification/RC substitutes. It rejects new unexpected
Guest-specific branches rather than silently assuming the same classification.
HTTP source SHA256:dd6db5e31425491ed18ce0c9eddd2d288e675e1a20473dc47dea4b2f57a67a4e.

For each band, enable/date_x/time_x/time2_x map to WIFI_GUEST_CONTROL_BIT;
the other ten Guest fields (SSID, hidden flag, auth/WPA/cipher, isolation flags,
MAC rule, rate and key) reach WIFI_COMMON_CHANGE_BIT. Actual notification code
prioritizes common changes: common-only or mixed common+Guest requests select
RCN_RESTART_WIFI2/5, while control-only selects control_wifi_guest_rt/wl.
Tests cover all14 fields on both bands and both mixed-bit cases. Fixture macro
values are representative masks; restart command constants and notify_rc are
substituted. This proves branch selection, not actual RC/driver execution or
whether a hardware channel scan occurs. Earlier actual Guest control fixture
already separates successful wrapper return from failed ifconfig acceptance.

ASan/UBSan and warnings-as-errors pass. Scratch45209B removed, absence asserted.
Reproduce:
```
PYTHONDONTWRITEBYTECODE=1 python3 tools/webui-preview/check_guest_notification_policy.py /home/andrzej/padavan-build/firmware-source-backup/padavan-4.4-c25283e-git-exact.tar
```

Do not mark a full Guest credential/SSID apply as restart-free merely because
its storage is now atomic. New HTTP batch binding must preserve this distinction
and use existing notifications only after successful batch and readback.
Uncertain outcomes must suppress deferred flash/service effects and request
reload. No source/driver workaround, ACK change, production Apply activation
or router access was performed here. Full handler binding remains unfinished.
