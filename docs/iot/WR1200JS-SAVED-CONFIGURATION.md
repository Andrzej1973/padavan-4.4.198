## Native save serialization traced — 2026-11-21

The conditional native save in native-flash-save.inc acquires nvram_sem, then
nvram_lock. Under the spin lock it compares the exact desired record, validates
nvram_manual and generates the whole snapshot. It drops the spin lock before
MTD I/O, retaining nvram_sem through comparison/write/readback. The reviewed
prepare-nvram-commit-order.py moves ordinary commit's same mutex before snapshot
generation, so commits serialize snapshot+flash in one order. Native readback
uses the same mutex. This source trace is not device execution evidence.

Ordinary RAM mutation is a different authority: the flash mutex does not mean
all NVRAM SET callers hold the IoT service guard, nor that RAM stays unchanged
after snapshot generation. flash-save-attempt.c therefore checks expected RAM
and policy before admission, checks flash independently, rechecks RAM/policy
before an attempt and after matching readback, and seals an attempted/skipped
write against replay. AUTO with manual policy returns manual-pending without
writing. Commit error plus later matching bytes does not become observed success.
A terminal receipt is an observation at that boundary, not a permanent lock on
future settings or proof that ra2 loaded the desired credentials.

No supported-source defect requiring a new lock was established by this trace.
Next inspect loaded-generation promotion and actual prepared startup/manifest
coverage; preserve the current strict false acceptance fields meanwhile.

## Current integration checkpoint — 2026-11-21

The 2026-11-22 owner decision selects Classic as the sole firmware WebUI and
supersedes the earlier Hybrid Modern resumption. IoT remains first priority;
current configuration and apply requirements use Classic controls.

Source recheck on main14ef311c finds saved-config-store.c, config-save-server.c,
flash-save-native.c and native-flash-reader.c. The save facade registers only
when both native readback and snapshot capabilities are verified. Native save
uses the checked WR_NVRAM_IOCTL_SAVE_PROFILE path outside PID1; it is not an
unconditional HTTP NVRAM write. prepare-runtime.py stages save/edit/view startup
and reports HTTP route binding separately. Those sources do not by themselves
prove durability, loaded-profile promotion or main-image installation.

The runtime report still explicitly sets configuration_flash_bound=false and
configuration_loaded_promotion_bound=false; package-candidate-pair.py requires
both false. Do not flip these fields to claim completion. Next trace the actual
edit-view HTTP → typed mailbox → RC edit owner → store/save → fresh observation
chain and its loaded-generation handoff. Reconcile implemented pieces before
adding another facade. Verify native writer arbitration, KEEP/REPLACE revision,
manual/automatic save outcomes and retained old-generation shutdown identity.
Only then change the manifest contract with source, target and image evidence.
Optional1451 proves prepared FT TUs, not this configuration acceptance.
No router state changes are authorized.

# Saved IoT configuration and loaded profile

## Current source scope — 2026-11-17

The experimental IoT candidate now stages a configuration-only authenticated
`wr_iot_config.cgi`, the existing single protected mailbox, RC continuation,
private configuration owner and fresh typed IPC observation. It is not yet a
main-image feature. Modern WebUI remains paused. No device was changed.

The complete desired profile is stored as one versioned `wr_iot_config_v1`
native RAM tuple. OFF preserves SSID, key and subnet in this record. The runtime
OFF request still contains no new credentials. Lowercase hex encodes seven
fields in a bounded 384-byte record; this encoding is not authentication.

| State | Authority | Current boundary |
| --- | --- | --- |
| Desired configuration | Complete versioned RAM record | `stored_in_ram` means freshly observed RAM receipt only |
| Loaded ra2 credentials | Existing generation and exact legacy profile/PMK proof | Desired changes do not replace this provenance |
| Runtime ON/OFF | Existing retained backend owner | Runtime APPLIED cannot acknowledge a configuration request |
| Flash persistence | Native save policy | Integration unfinished; RAM success does not prove durability |

## Ownership and transport

Configuration and runtime operations share one queue and outer RC admission.
Their request/result types are distinct. The configuration owner adopts the
server admission, captures the backend identity under the real service guard,
and attempts at most one SET after exact prior-record and capacity checks.
ACTIVE requires an already armed available normal-shutdown route; configuration
does not arm it. Read failure, uncertain write or foreign state retains ownership
for observation instead of replaying SET or rolling back another writer.

Before publishing a terminal RAM result, the configuration facade reobserves the
backend/store, releases its nested guards and retains a private receipt. Outer
server admission remains held until publication. Publication retry uses that
receipt without another SET. Fresh status checks both the typed request/result
and current native record; replies contain no credentials. Runtime IPC uses WIS1,
configuration IPC WIC1. Old result V1 cannot parse the new RAM-only result V2.

## Native NVRAM capacity and overflow

The capability defaults to zero. Source preparation requires exact verified
native dump/generator implementations, public header and effective kernel
configuration. NOR usable NVRAM is 0xF000 bytes with a 20-byte header, not an
assumed 64 KiB. The store checks projected full-dump usage, subtracting an old
configuration tuple before adding its replacement, both at begin and before SET.
No room rejects without SET.

The pinned SDK generator originally returned success on overflow after truncating
the tuple walk; rehash could lose live tuples and flash staging could accept an
incomplete image. The existing Band Steering NVRAM preparer now returns ENOSPC
before rehash/CRC/flash. This source transform affects the selected baseline
kernel too. Its existing getall overflow guard remains. Host reproduction uses
the exact original/prepared functions with modeled table/rehash/flash callbacks;
no MTD or router NVRAM was accessed. Target kernel and device verification remain
required. No ioctl or firmware protocol is introduced.

## Verification and remaining work

Host tests cover canonical records, real file mailbox cross-type rejection,
CGI validation, real forked Unix status IPC, owner/store/backend composition,
uncertain SET/cancellation, capacity boundaries, native overflow and staged
header/object closure. Native syscalls and external SDK resources are fixture
actors. These checks do not establish a MIPS image or physical runtime result.

The local unpublished generation package now selects the versioned desired record
in RC, pins its revision, and supplies captured credentials synchronously to
initial and post-RELEASE profile generation. New ON/OFF, mismatch and drift
rollback host composition passes. Staged dependency checks pass; broad regression
is still running. Generated-file provenance remains distinct from driver-loaded
SSID/PMK admission. Complete loaded-generation handoff and all composed target/
image/runtime checks before production promotion. Details and source references:
[Desired/loaded transition](WR1200JS-DESIRED-LOADED-PROMOTION.md). Do not redirect
legacy restart-profile or radio-off readers to newly desired credentials while
the old generation is active. Factory CSPRNG values remain boot-only.

Then integrate truthful native manual/automatic flash-save outcomes outside
PID1, Classic configuration/read/keep-password behavior, main-image promotion
and target/image gates. Ordinary IoT toggles must preserve Main/Guest and avoid
physical restart/scan. Physical acceptance remains separate. MCU ACK protection,
shared TX state machines, DMA ownership and radio timing are unchanged.

## Next-generation reader prepared locally

`wr_iot_saved_config_capture` reads the complete desired record under the actual
caller-owned service guard. Proven absence sets present=0 without replacing the
caller profile; malformed/native-error/capability-zero refuses with both outputs
unchanged. OFF retains credentials/subnet. No runtime admission, legacy fallback,
NVRAM mutation or radio action occurs. The prepared0/1 host fixture covers these
boundaries using actual store/guard/snapshot code and native syscall actors.
Cold-generation integration is still pending.

The generator insertion is in prepare-rc.py at gen_ralink_config; it currently
uses wr_iot_precreated_boot_request_read through the existing profile snapshot.
Both restart-profile.c and radio-off-profile-check.c still prove the legacy
loaded credentials. cold-on-generation.c calls those checks before Main startup.
A new-generation change must move these readers together under exact generation
ownership, retaining old provenance through OFF/recovery. A RAM save alone must
never promote the new profile or satisfy the loaded-key comparison.

Native web_ex.c nvram_commit_safe returns void and skips automatic commit when
nvram_manual=1; asus_nvram_commit clears nvram_modified before calling it. These
legacy callbacks cannot prove new IoT flash durability. The native kernel takes
the cache snapshot before its flash mutex, so a successful commit syscall alone
also cannot certify a particular concurrent desired revision without an owned
serialization/readback contract. Preserve existing global save policy while
adding explicit IoT outcome handling outside PID1.
