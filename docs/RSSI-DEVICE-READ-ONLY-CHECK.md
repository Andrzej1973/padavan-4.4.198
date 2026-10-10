# RSSI monitor: read-only device check

Use this procedure only after the intended firmware is already running. It does not flash, reboot, restart services or change radio thresholds. Keep the existing remote-access tunnel available.

Open the authenticated router homepage and check the collapsed RSSI event section. With RSSI thresholds disabled, an empty event list is expected; an empty list alone does not prove the driver query is working. Both radio availability fields and the overall source state matter.

Save two authenticated responses from `/wr_rssi.json`, at least five seconds apart, as private local files. Do not publish them: device MAC addresses and activity are included. Validate them on the PC:

```sh
node tools/connected-devices/check-rssi-device-snapshots.js first.json second.json
```

The validator checks the actual response schema, size limit and sequence continuity within each observed adapter session. Its summary omits MAC addresses. A valid response proves only that these observations are structurally consistent; it does not prove correct driver behavior under load.

Also check automatic refresh, temporary connection loss and recovery, filtering, retained expansion and hidden-tab pause in the browser. Actual RSSI disconnect behavior requires a separate test client and explicit authorization to change the threshold. Do not use the client carrying remote management or the tunnel for that test. Record kernel version, firmware identity, radio availability and any errors before interpreting an empty history.
