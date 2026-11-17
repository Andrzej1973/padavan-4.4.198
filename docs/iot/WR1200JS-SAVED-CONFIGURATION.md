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

Next implement desired-to-loaded promotion through an owned cold-generation
transition, preserving old loaded identity until safe retirement. Do not redirect
legacy restart-profile or radio-off readers to newly desired credentials while
the old generation is active. Factory CSPRNG values remain boot-only.

Then integrate truthful native manual/automatic flash-save outcomes outside
PID1, Classic configuration/read/keep-password behavior, main-image promotion
and target/image gates. Ordinary IoT toggles must preserve Main/Guest and avoid
physical restart/scan. Physical acceptance remains separate. MCU ACK protection,
shared TX state machines, DMA ownership and radio timing are unchanged.
