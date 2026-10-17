# WR1200JS build 401 evidence — 2026-10-17

Firmware workflow run:
https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39031929124

The run completed successfully for commit
`cda1e9ea12385c736577db884472efbc0ae247e8`. GitHub Actions reports the
`select`, WR1200JS build and final firmware ZIP jobs as successful.

Built image: `WR1200JS_4.4.198.9-401.trx`, 12,603,719 bytes.
SHA-256: `034aa6cbe70d5083174dce9c5a6ec8af44f318bd6bd61669d00966a6ecd13e63`.

The build log confirms the image header identifies WR1200JS and Linux kernel
4.4.198. The image-structure verifier passed and explicitly reports that boot
is unverified. The image checks also passed for the localized WR1200JS footer
credit while retaining upstream credits and the distribution notice, and for
the English, Ukrainian and Russian RSSI threshold captions and help text.

Other checks in this run passed for the requested/effective configuration,
firmware upload structure, Stubby resolution under QEMU, shipped scripts with
the target BusyBox, WireGuard server export, USB/IP restore orchestration,
VPN profile tools, and packaged services. These are build/image checks; they do
not prove every service works on the physical router.

Build 401 has not been confirmed booted on the physical WR1200JS. The prior
physical audit refers to build 396, so this report makes no device-runtime
acceptance claim.
