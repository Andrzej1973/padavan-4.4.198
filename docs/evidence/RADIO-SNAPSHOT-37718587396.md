# Radio configuration capture evidence

Inspected authoritative GitHub Actions records on 2026-10-08:

- Run 37718587396, source 3df67cba3eb74496fdd4d9dce3ba61dbdadf4a92.
- Job 113120738430.
- Verify original radio snapshot settings and live status: success.
- The overall run was still in progress at inspection.

This supersedes the failed integrated fixture compilation in run 37718400539.
The fixture now matches the real nvram_wlan_get API's char-pointer return type
and includes stdlib.h for atoi. No compiler warning or sanitizer was suppressed.

The radio fixture extracts the actual prepared net_wifi.c settings adapters and
links the real settings-snapshot module under address/undefined sanitizers. It
checks captured auth mode, radio mode, guest enable and RSSI threshold reads;
missing defaults; an unchanged capture; live mlme radio state changing from 1
to 0; and ordinary fallback after clearing the capture pointer.

The integrated fixture extracts the actual Wi-Fi apply helper and those radio
adapters. Its simulated radio restart callbacks require the same capture as the
profile binding and check both SSIDs, guest enable and live mlme status. Existing
apply failure tests and capture/binding failures verify that both binding
pointers clear before returning. Kernel reading, compatibility decisions,
profile writes, radio restarts and driver/service responses remain mocked.

## Full compilation and remaining work

The isolated full rc compiler now applies prepare-radio-snapshot.py after Wi-Fi
snapshot preparation. It requires the actual net_wifi.o radio capture state
symbol and archives prepared source plus source/object hashes. Compilation of
this new combination is pending; the production image does not install it.

External AP.dat files, dependent routines in other translation units, external
processes and router runtime behavior are outside these fixture results.
The candidate requires the kernel overflow-reporting getall change before
activation. Preserve guest, WDS/APCLI, authentication and WAN behavior when
closing these remaining integration paths.
