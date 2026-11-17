# WR1200JS native flash readback contract

## Current package boundary — 2026-11-17

The experimental source now binds dedicated authenticated AUTO/EXPLICIT Save
POST routes through the existing single queue to the registered RC Save facade,
retained configuration owner and nonblocking child worker. Legacy runtime and
RAM-only routes retain their behavior. Automatic mode respects nvram_manual;
explicit Save uses the versioned conditional native ioctl. The native handler
checks expected profile and save policy atomically with snapshot creation and
checks full-image flash readback. Firmware ACK, TX/DMA ownership, radio timings
and Main/Guest restart policy are unchanged.

POST reports only queue acceptance. stored_in_ram and saved_in_flash have
separate result versions and private IPC types. saved_in_flash means a confirmed
save operation with its retained receipt and current matching RAM identity;
status does not synchronously reread flash in PID1. It is not proof against later
external flash modification. Unknown COMMIT/child receipts retain recovery and
never authorize replacement writes. Failed terminal publication retries only
verification/publication, not SET/fork/COMMIT.

Source staging and host checks are evidence only. MIPS kernel/RC/HTTP linking,
assembled candidate image verification, main-image promotion, Classic form UX
and physical acceptance remain open. configuration_flash_bound stays false
until its target/image gates are reviewed; a linked API is not router acceptance.
The sections below record design development and earlier draft boundaries;
this current scope supersedes their unpublished/unbound statements.

Status: guarded native readback and conditional save are source-staged and host-tested. RC save routing, durable receipts and device acceptance remain incomplete.

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
There is no startup caller or configuration-save route; the conditional write API is described below.
The reader observes bytes only; expected revision ownership/freshness and a durable
save receipt still need integration outside PID1.

Host checks pass for the actual handler, actual client capability0/1, exact source
capability refusal, and actual RC staging in snapshot0/readback0,
snapshot1/readback0 and snapshot1/readback1 combinations. Syscalls/MTD/capability
are fixture actors; these do not constitute kernel scheduling, target or device
verification. The exact pinned input is identified by
WR1200JS-STANDARD1357-SOURCE-HASH-2026-11-17.json; an older local cache had an extra
final blank line and must not be used as a whole-file source authority.

## Conditional profile save and child-only attempt journal

The versioned pointer-free Linux request for ioctl 51 is exactly 400 bytes on
host and MIPS native ABIs (four 32-bit fields plus a 384-byte bounded record).
CAP_SYS_ADMIN is required. It accepts only the fixed IoT profile key and native
Config partition. Under nvram_sem and nvram_lock, it compares the expected
record, validates native manual-save policy and generates the complete native
image. Automatic mode refuses manual policy; explicit Save may proceed. This is
the admission linearization point: subsequent native settings changes are later
operations, not permission to rewrite the admitted snapshot. A temporary-only
profile excluded from persistent generation refuses before any MTD write.

The handler requires the prepared generator's ENOSPC guard at source installation.
After generation it releases the spinlock while retaining the flash mutex,
requires a successful initial flash read, skips an already identical image, or
writes once then checks full image equality by readback under the same mutex.
MTD errors or mismatched readback return failure without retry. All allocated
buffers and request credentials are wiped. Existing native APIs are unchanged.
No firmware command or radio/ACK behavior changes.

flash-save-attempt.c is a child-only journal binding PID, self address, request
ID/time, canonical desired record and automatic/explicit mode. It refuses PID1.
It seals after one conditional ioctl attempt, an already matching flash
observation or manual-save deferral; later drift/errors cannot trigger another
write. Pre-submission errors can recover to a first attempt; post-submission
errors permit observation only. The native adapter calls only conditional ioctl
51, never unconditional native COMMIT. After an attempted conditional write, OBSERVED additionally requires its
successful kernel/close receipt: a matching profile alone cannot prove that a
partial or failed global flash write preserved other settings. Unknown write
outcomes retain observation-only uncertainty. Public status still needs parent
request ownership/freshness checks; OBSERVED is not a completed WebUI operation.

Host tests execute actual prepared handler bodies with deterministic admission
race injection: policy/profile changes at mutex acquisition refuse before
generation/write; explicit/manual behavior, temporary exclusion, ENOSPC,
read/write/partial-write/readback errors and cleanup pass. Actual child journal
and native adapters pass with sanitizer checks and the real snapshot parser.
RC source stages both objects for target checks, but has no caller or Save route.
Parent nonblocking child routing, lost-result ownership and final publication
remain incomplete. A lost child result never authorizes a replacement COMMIT.

## Nonblocking child worker and RC save owner

flash-worker.c retains parent PID/self/request/mode/pipe identity and permits one
fork attempt. Only the child invokes the single-attempt native save journal;
parent begin/step never perform COMMIT, flash read or waitpid. It polls a private
nonblocking anonymous pipe and checks inode/device/type/flags before reading.
The 56-byte endian-explicit WFS1 receipt contains only request ID/time, child PID,
mode and outcome flags. Native credentials are wiped before sending it.

The child drops inherited parent descriptors and signal handlers; it spawns no
command/grandchild. A valid receipt is emitted only after native calls and private
cleanup, so the stock reaper may reap the child without consuming the receipt.
Pending shutdown can drain existing work, never authorize a duplicate begin.
OBSERVED and MANUAL_PENDING require exact matching receipts; known pre-submission
failure is NOT_STORED. Missing, truncated, mismatched or uncertain results retain
UNKNOWN and cannot retire or respawn an automatic commit. Descriptor substitution
is refused without closing the foreign descriptor.

Actual fork/pipe + real service-guard host sanitizer tests pass, including reaper,
capability0/1, shutdown drain, blocked child proving nonblocking parent, pipe/fork
failure, killed child, truncated receipt, copied owner, wrong request, reused fd,
unknown/no-respawn and known-no-submission cleanup. Native flash calls are actors.
config-save-owner.c now composes this worker with the actual RAM owner/store.
It captures the original backend, requires fresh RAM/backend identity before
starting and before terminal preparation, drains submitted children even during
backend drift, and preserves decisions through publication retries. It never
redirects a stale request to a newer desired profile. RAM_ONLY reasons distinguish
manual policy, cancellation and known no-submission; none is a flash receipt.
Unknown submitted work retains ownership without replay. Cleanup prepares a
private receipt while the outer mailbox server must retain shutdown admission.
Historical observed-save status rechecks current RAM, without pretending to do
fresh flash I/O in PID1. The caller must map this fact accurately in the future
public result format.

The facade and worker are source-staged as experimental RC units with target
symbol gates. No mailbox/HTTP Save route is bound; configuration_flash_bound
remains false. The next integration must add typed automatic/explicit save
requests/results, terminal publication and status semantics in the existing
single queue, without changing legacy runtime or RAM-only results. Host staged
checks pass for capability0/1. Target/image and physical verification remain
open. No router was accessed and no firmware save route was enabled.

## Next local draft: typed Save transport (unpublished)

control-record.h now has distinct AUTO/EXPLICIT configuration-save operation
kinds and WR-IOT-CONFIG-SAVE-1 envelopes, without changing old request bytes.
Mailbox flash result7 uses WR-IOT-RESULT-3 only; old result1/runtime and
result2/RAM remain incompatible with flash success. The same single private
queue and exact continued owner/ID/time checks apply. No new queue is added.

Original codec/mailbox and new Save tests pass with the actual filesystem
mailbox under sanitizers. While backend/status/HTTP binding is unfinished,
control-server explicitly rejects new Save operations before activation and
control-client refuses unsupported flash status. Actual RC/client host tests
confirm both boundaries. These local edits are not published or target-verified.
Next connect config-save-owner through a dedicated RC facade, extend typed
private status observation, then add authenticated automatic/explicit endpoints
and composed end-to-end checks before enabling any save route.

Local Save-backend registration now binds a copied complete callback set to the
current PID once, before active/shutdown/radio-owned work. Unregistered or
fork-inherited registration cannot execute Save. Registered Save uses its own
execute/progress/terminal callbacks under the existing single queue; old RAM and
runtime paths retain their callbacks. Actual RC/mailbox host tests pass for
missing callbacks, active-admission refusal, duplicate registration, one execute,
one continuation and exact flash terminal publication. Production registration,
private status observer and HTTP wiring remain incomplete and unpublished.

Local config-save-server.c now supplies the actual execute/progress/terminal
callbacks using the retained config-save-owner. It rejects terminal-kind mismatch,
keeps unknown owners rather than replacing them, and rechecks receipts on every
publication retry. Its observer distinguishes RAM_ONLY from confirmed historical
flash save and requires current owner/RAM identity. Host tests of the actual
facade pass with an explicit modeled owner. Startup registration, shared status
routing and HTTP endpoints are still unbound; this draft is unpublished.

Local status-channel adds WIF1 for saved_in_flash, distinct from WIC1 RAM and
WIS1 runtime. Real fork/Unix SOCK_SEQPACKET tests pass for exact flash response,
cross-kind response refusal and retained PID/UID/nonce/length/timeout checks.
The wire parser derives the requested result type from the magic. This is only
transport: production RC observer/startup registration and HTTP acceptance remain
unbound, and the client continues to refuse flash status until that integration.

Local source staging now includes config-save-server.c/h in experimental RC
object/header closure and verifies its install/observer symbols after target
linking. Source preflight includes Save codec/mailbox, facade and private status
regressions. Actual staged host compilation passes in all three native capability
combinations, alongside old CGI/transport/status regressions. No startup install
call or HTTP Save route is present; the draft remains unpublished and
configuration_flash_bound remains false until full routing/verification.

Local startup preparation now attempts Save-backend installation once after
init_router and before optional IoT boot arm. Actual generated-fragment tests
cover WR/non-WR and boot-policy0/1, including refused registration without boot
failure. Capability checks remain in install; no HTTP Save route is added.
Source verification requires exactly one call in that order. Current preflight
recipe has 39 unique ordered steps. The whole package remains unpublished until
private observer/HTTP binding and composed checks complete; target verification
of this startup change remains outstanding.

Local private status observer is now routed in RC runtime: SAVED_FLASH queries
must be accepted by the retained Save owner and cannot fall through to runtime
activation. RAM queries may use the Save RAM_ONLY receipt or the existing RAM
configuration observer. HTTP-side status client now sends WIF1 for flash results
and requires the authenticated private observer roundtrip plus unchanged mailbox
recheck before returning status. The status denotes the original confirmed save
with current RAM identity, not fresh flash readback on each request. No HTTP
Save submission endpoint is enabled yet. New routing remains unpublished.

Local HTTP preparation now stages authenticated POST endpoints
wr_iot_save_auto.cgi and wr_iot_save.cgi for automatic and explicit mode.
Endpoint identity selects policy; the request body cannot upgrade it. Both use
the existing strict complete configuration/CSRF parser and once-only body,
return only queue acceptance/ID, and wipe configuration buffers. The client
submits the distinct typed save operation in the same queue. Existing runtime
and RAM-only endpoints retain their semantics. Handler auth/POST/MIME/CSRF,
complete disabled provisioning and status rendering tests pass. Full composed
queue->actual facade/owner->worker->terminal/status validation and assembled
HTTP route verification remain required before publication/target claims.

Local composed Save-route test now links actual client, real filesystem mailbox,
shared RC server and registration, Save facade, owner, RAM store/parser/guard and
fork worker. Confirmed flash, automatic manual-policy RAM-only, uncertain COMMIT
retention/no replay and changed-RAM status invalidation pass. Native SDK/flash
and the private observer transport boundary are explicitly modeled; private IPC
has its separate real-process tests. Pinned assembled HTTP source also passes
route/auth/metadata checks after actual prepare-http transformation. The current
40-step source preflight includes this composed test. The package is still local;
full frozen-package regressions, target/image checks and physical acceptance are
outstanding, and configuration_flash_bound is not upgraded on host evidence.
