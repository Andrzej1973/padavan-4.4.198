# WR1200JS service navigation runtime check — 2026-10-18

Read-only SSH inspection of `ASUS@192.168.20.1`. No settings, services,
network state, firmware or router files were changed.

## Observed state

- `uname -r` returned `4.4.198` and `nvram get firmver` returned `4.4.198.9`.
- `nvram get buildno` and `nvram get extendno` returned empty values; the
  optional `/etc_ro/version` file was unavailable. The exact installed build
  number therefore could not be established by this SSH sample. A WebUI
  screenshot in the conversation displayed build `4.4.198.9-474_4fc90055`,
  but that is separate screenshot evidence and was not confirmed by these
  runtime identifiers.
- The live `/www/Advanced_Services_Content.asp` navigation still sends Telnet,
  Cron, Watchdog and Network discovery to the top of the services page, without
  a fragment. Their target controls are present in the same page:
  `telnetd_on_of`, `crond_enable_on_of`, `watchdog_cpu_on_of` and
  `lltd_enable_on_of`.
- Read-only settings/process comparison returned:
  - KMS: `vlmcsd_enable=1`, process present.
  - SSH: `sshd_enable=2` (key-only mode), `dropbear` present.
  - iPerf3: `iperf3_enable=0`, process absent.
  - Cron: `crond_enable=0`, process absent.
  - LLTD: `lltd_enable=0`, `lld2d` absent.
  - ASUS Discovery: `adsc_enable=0`, `infosvr` absent.
  - CPU Watchdog: `watchdog_cpu=1`, but `/sys/module/rt_timer_wdg` is absent.
    A separate `watchdog` process exists; it does not prove the expected module
    is loaded. The WebUI screenshot's “enabled; rt_timer_wdg not loaded” text
    is consistent with this distinction.
    The optional module file was not found under `/lib/modules`, while
    `/dev/watchdog` and `/sys/class/watchdog/watchdog0` exist. The queried
    watchdog0 sysfs state/timeout attributes and driver link were unavailable,
    so these facts do not establish whether the built-in MT7621 watchdog timer
    is actively running or being serviced.
- This proves the navigation defect is present in the page currently served by
  the router and that the local source correction has not yet reached this
  installed page.

## Limits

This was a source-page/runtime read, not a browser click-through. It does not
validate the corrected links in a newly built ROMFS or confirm the exact
installed build number. Do not infer firmware identity from a blank NVRAM build
field or from a screenshot captured at another time.

## Read-only recheck — 2026-10-18 18:06 UTC

Repeated the page-source check over SSH after reviewing the local route gate.
`/www/Advanced_Services_Content.asp` still contains direct service-navigation
links without anchors for Telnet, Cron, CPU Watchdog and Network discovery.
The same source file contains their target IDs (`telnetd_on_of`,
`crond_enable_on_of`, `watchdog_cpu_on_of`, `lltd_enable_on_of`). This confirms
the live router still serves the earlier menu and that the local source
correction has not reached its WebUI. This was an HTML read only; no router
setting, file, service or firmware was changed. The source code and local
fixture are verified, but a new image build and browser click-through are still
required to establish the corrected navigation.
