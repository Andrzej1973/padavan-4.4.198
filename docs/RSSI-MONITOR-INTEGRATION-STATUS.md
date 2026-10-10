# RSSI monitor integration status

The WR1200JS build workflow now prepares observation storage, station birth identities, RSSI event capture, matched entry-clearing evidence and a privileged read-only query in both vendor drivers. The HTTP collector reads one bounded page per radio on each background tick. `/wr_rssi.json` requires authentication. The homepage includes a collapsed event list and automatic refresh.

The monitor records decisions, allocation failures, frame submission and station-table clearing separately. None proves that a client received a frame or successfully roamed. Sessions retain their full 128-bit identity; history is limited to 256 RAM records. Failed queries retain history and disclose source availability.

## Verified evidence

- [ABI 326](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38059489157) completed successfully. Its downloaded log confirms the native RSSI history, collector, JSON, HTTP integration and source-preparation checks. The workflow also compiles its registered userspace probes for MIPS.
- Local Node tests exercise schema bounds, filtering, stage labels, retained expansion and scroll, network-error recovery and hidden-tab pause. These are synthetic tests, not router runtime evidence.
- Earlier isolated full-driver compilation is recorded in [build 151 evidence](WR1200JS-BUILD-151-RSSI-QUERY-EVIDENCE.md).

## Still required

Verify the new normal firmware build, exact packaged modules and HTTP/UI inclusion. Then exercise actual ioctl errors, concurrent observation and reads, and adapter lifecycle behavior on the router. Browser rendering and refresh against the real device remain unverified. No router flashing or configuration changes were performed for these checks.
