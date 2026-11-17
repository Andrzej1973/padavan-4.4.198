# WR1200JS native flash readback contract

Status: byte validator, typed comparison and guarded Linux flash readback are source-staged and host-tested. No new writer, durable-save receipt or device acceptance.

## Pure byte validator boundary

The first implementation must accept caller-supplied bounded bytes only. It must
not open MTD, issue COMMIT, infer persistence from RAM GETALL, or log settings.
Decode the five 32-bit header words explicitly as little endian; never cast an
unaligned buffer to the native header. Require the pinned magic/version and
20-byte header, and validate declared length against both supplied bytes and
the selected board NVRAM capacity before CRC or tuple access.

The vendor `nvram_calc_crc` in `kernel-nvram.c` starts CRC8 at 0xff,
processes bytes [9,20), then [20,header.len). The stored checksum is byte 8.
Use the exact `_hndcrc8` convention from `kernel-nvram_linux.c`; do not add a
final complement based on the generic CRC comment. Header bytes [0,8) are not
covered by this checksum, so independently validate magic and length.

Parse name=value NUL-separated tuples within declared length. Require bounded
termination, reject missing equals, empty names and duplicate keys instead of
silently selecting ambiguous configuration. Permit empty values and equals
inside values. Account for the generator's zero terminator/alignment padding;
never scan into the rest of the partition to recover malformed data. A stricter
parser is an admission check, not a replacement for vendor rehash semantics.
Do not label a valid CRC image durable unless its origin is authoritative flash.

## Required verification before integration

Compare validator CRC against the extracted actual vendor C implementation,
including randomized payloads, not only a second copy of the new algorithm.
Exercise truncated headers, invalid magic/version, under/oversized lengths,
unaligned input, corrupted payload/header, malformed/duplicate tuples and
normal empty-value/padded records. Failed validation must leave output unchanged.

A future persistence receipt additionally requires serialized commit/readback,
proven flash partition identity and offset, matching the intended configuration
revision, and handling skipped/error/unknown outcomes without declaring saved.
The original native cache snapshot precedes the flash mutex. The new source
transform moves mutex acquisition before generation and releases it on generation
failure as well as skip/write paths. A zero COMMIT return alone still cannot
establish a particular profile's durable revision.

## Source evidence

Pinned SDK revision: c25283e915a2a00a763774dd255b14aff997285e.
The following locally inspected vendor source hashes identify the inputs:

- `kernel-nvram.c`: SHA256 `b9cf4ea7898824ce0b89ae49d023fb661b8f08c18acab654037dd0f213fc8840`.
- `kernel-nvram_linux.c`: SHA256 `eb8ec04cf2c454dc9bc469f7f89a2540724bcb2cda2d76e310e1e29ab7c20487`.
- `kernel-bcmnvram.h`: SHA256 `411b381cdff5d6fea5fda76510e7a5dacff591dd067ce47c3cc3e225ae42b33e`.

## Implemented host boundary

`tools/iot/flash-image.h` validates caller-supplied bytes and looks up an exact
key only after validating the complete image. Lookup distinguishes found,
proven absent and error; insufficient output capacity or invalid input leaves
the destination unchanged. No configuration values are printed.

Run `python3 tools/iot/check-flash-image.py <pinned kernel-nvram_linux.c>`.
The script checks the source SHA256, compiles the actual vendor CRC table and
function with the validator under C99/Wall/Wextra/Werror, tests 1000 valid and
corrupted images, and checks exact-key/empty-value/absence/duplicate/refusal
semantics. A separate ASan/UBSan executable tests allocated input sizes 0..255.
These are host checks only. Readback source staging is described below. Target verification and durable
revision receipts remain incomplete; host checks do not establish persistence.

The typed `saved-config-flash.h` comparator validates both the expected and
image records through the actual canonical saved-config codec. It distinguishes
INVALID / ABSENT / DIFFERENT / MATCH, covers OFF with retained credentials,
and wipes temporary decoded profiles and credential buffers. MATCH describes
only the provided bytes; origin verification and commit/readback serialization
are still required before issuing any durable-save acknowledgement. The shared
record key now lives in saved-config.h; store callers retain the same key.
Codec and prepared0/1 store/guard regression tests pass after this move.

## Commit order correction

`tools/band-steering/prepare-nvram-commit-order.py` checks the exact original
native commit function hash and its sole mutex acquire/release pair before
changing source. `prepare-source-integration.py` runs it after the existing
NVRAM overflow preparation. Allocations remain outside the mutex, the spinlock
still covers only generation, and MTD I/O remains outside the spinlock. Native
early-uninitialized behavior and unchanged-image skip policy are preserved.
No new ioctl or firmware protocol is introduced.

`check-native-commit-order.py <pinned kernel-nvram_linux.c>` executes original
and prepared native function bodies with allocator/lock/MTD actors. The original
exposes unguarded generation; the prepared body protects generation and passes
generation error, read/write error, unchanged image, both allocation failures,
and early-uninitialized paths under host sanitizers. This does not test kernel
scheduling, MTD persistence or a concurrent device workload. The transformed
kernel still needs target/image checks. Readback acquisition is now source-staged below; target/device checks remain open.

## Fixed-target Linux readback source package

The native-flash-readback.inc handler uses existing anvram_ioctl_t through
new read-only Linux ioctl 50, CAP_SYS_ADMIN, Config/NVRAM_MTD_OFFSET/NVRAM_SPACE,
and nvram_sem. It validates a copied request, rejects early-uninitialized state,
normalizes positive MTD errors, and wipes its temporary buffer. Native APIs and
firmware commands are unchanged. prepare-source-integration runs host checks
before mutations and stages the handler after verified commit-order preparation.
The source gate accepts only exact prepared SDK bytes and the matching wire
header, refusing changed/missing/symlink inputs.

native-flash-reader.c opens only nofollow /dev/nvram, validates native char-device
major, makes one ioctl, rejects ioctl/close/corrupt readback, and wipes/frees all
allocated bytes. It never falls back to RAM GETALL. A partial user copy on kernel
EFAULT is discarded by this client. Capability defaults to zero and additionally
requires the existing verified native capacity/snapshot capability.

prepare-runtime stages its RC object/headers and generates a separate capability
from native-flash-source-guard.py evidence. compile-runtime-link requires source
capability and the reader target symbol; configuration_flash_bound remains false.
There is no startup caller, configuration-save route or new flash write here.
The reader observes bytes only; expected revision ownership/freshness and a durable
save receipt still need integration outside PID1.

Host checks pass for the actual handler, actual client capability0/1, exact source
capability refusal, and actual RC staging in snapshot0/readback0,
snapshot1/readback0 and snapshot1/readback1 combinations. Syscalls/MTD/capability
are fixture actors; these do not constitute kernel scheduling, target or device
verification. The exact pinned input is identified by
WR1200JS-STANDARD1357-SOURCE-HASH-2026-11-17.json; an older local cache had an extra
final blank line and must not be used as a whole-file source authority.
