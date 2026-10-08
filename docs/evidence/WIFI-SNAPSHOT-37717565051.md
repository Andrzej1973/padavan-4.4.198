# Wi-Fi policy/profile capture verification

Authoritative GitHub Actions job records inspected on 2026-10-08:

- Run 37717565051, source 0f0e11bea4e79338c66f9ed4d8d4844601dbc5b4.
- Job 113117471433.
- Verify complete NVRAM snapshot overflow handling: success.
- Verify immutable settings snapshot reader: success.
- Verify actual profile snapshot wrappers: success.
- Verify Wi-Fi apply snapshot capture and cleanup: success.
- The overall run was still in progress when those steps were inspected.

The Wi-Fi fixture extracts the actual prepared net_wifi.c callbacks, links the
real lifecycle and settings-snapshot modules, and runs with address/undefined
behavior sanitizers. Its NVRAM getall reader, profile binding/write operations,
compatibility policy and radio/service responses are mocked. It exercises
capture and binding failures before quiescence, cleanup through the existing
callback failure paths, rejection of live reads while bound, and a successful
retry. This does not prove actual driver behavior or hardware execution.

The separate profile wrapper fixture extracts actual prepared ralink.c helpers
and links the real settings-snapshot module. It verifies fixed captured reads,
derived WEP key type, suppressed live writes while bound and restored ordinary
fallback after unbinding. It is not an end-to-end two-profile generation test.

## Remaining scope

The isolated full rc compiler now applies prepare-wifi-snapshot.py after profile
snapshot preparation. It requires net_wifi.o references to nvram_getall,
wr_band_profile_bind_snapshot and wr_band_snapshot_capture, plus the existing
profile binding symbols and snapshot object. Compilation of this new combination
is pending. Production firmware does not install the candidate.

The candidate requires the overflow-reporting kernel getall patch. Boot profile
generation, live reads in original radio initialization routines, external
AP.dat additions and concurrent external writers still need explicit handling.
Do not describe the complete Wi-Fi transaction as immutable or runtime verified.
