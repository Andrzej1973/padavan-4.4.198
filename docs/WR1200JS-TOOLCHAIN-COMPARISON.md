# WR1200JS compiler comparison

The production default remains the pinned owned archive (GCC10.5/uClibc1.0.43).
The source candidate is the successful generator run42467546674, generator
revision5ef6a8577ae24be27d8d81b3fe44a587d8491a16 (GCC10.5/uClibc1.0.48).

WR1200JS toolchain comparison builds the same current source SHA twice through
the existing firmware recipe: control first, then source candidate. It uses the
optional queue and separate artifact namespaces. No defaults, firmware settings
or automatic promotion change. The new input is accepted only in the dedicated
source comparison lane; normal callers retain pinned behavior.

Candidate installation requires exact generator provenance, relocation/QEMU
checks, expected versions and archive hash/size. GitHub cross-run artifact
access is read-only. Expired/deleted candidate artifacts fail closed; rerun a
reviewed generator or preserve a new exact release before selecting new inputs.
The existing pinned owned Release is retained as the control indefinitely.

Each successful lane preserves its TRX, existing image gates, toolchain checksum,
compiler identity, full firmware/kernel effective configs and per-file ROMFS
ELF headers, attributes, interpreter and NEEDED libraries. The final comparison
requires identical source/configs, ELF inclusion, architecture/O32 flags and
runtime dependency identities. Binary hashes/sizes are reported, not expected
to match across compilers. A green report is software evidence only: review
libc ownership, full module/feature checks and physical router acceptance before
any production default change. No flash/reboot/service operation is performed.

Host negative fixtures reject wrong source/lane/target, config/inclusion/ABI
drift and invalid candidate provenance/hash. Results apply only to the exact
firmware SHA and generator run. Missing output or a failed build is not success.

## Network-failure correction (2026-11-08)

A/B42472697144 control attempt1 failed fetching mbedTLS (HTTP503), attempt2
failed fetching libqrencode (HTTP504). Neither is a source-toolchain regression.
configs/owned-build-dependencies.json pins identical mbedTLS2.28.8, qrencode
commit715e29fd4cd71b6e452ae0f4e36d917b43122ce8 and PCRE2 10.49 source archives
in our build-dependencies-v1 release. The firmware recipe seeds verified copies
into their original library directories before make, using an owned cache keyed
by the committed manifest. Source recipes, versions and compiler settings stay
unchanged. Every cache entry and installed archive is SHA256 checked; partial
network downloads cannot become accepted source archives. Other dependency
recipes still use their existing upstream sources; this does not claim a fully
offline or fully mirrored firmware build.

A/B42474205248 failed before compilation because even the owned mbedTLS asset
API returned504/connection56. Therefore the three small archives (6,415,071 bytes
in total) are now also committed in sources/archives and installed offline from
checkout. The command-line seeder never falls back to the network; missing or
corrupt repository inputs fail closed. Owned Release remains a preservation copy.
The existing verified cache may still be used. This eliminates per-build release
HTTP dependency for these three packages, not all firmware dependencies.
