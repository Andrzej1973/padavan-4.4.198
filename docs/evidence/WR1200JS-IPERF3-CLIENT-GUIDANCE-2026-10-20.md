# WR1200JS iPerf3 LAN client guidance — 2026-10-20

The iPerf3 service page previously showed the configured enable flag and
observed server-process state, but did not explain how to run a bounded client
test. Source preparation now adds an EN/UK/RU help row with the router's
configured LAN address and the command:

```text
iperf3 -c <router LAN address> -t 10
```

The instructions require the server to be enabled and observed running first.
The ten-second default-TCP command runs on a LAN client; its output is produced
by that client. The page explicitly says this measures the client-to-router LAN
path, not WAN or Internet throughput. The row is hidden if iPerf3 is absent
from the image.

The exact-ROMFS verifier now requires the help row, LAN-address binding, bounded
command and all four new localization keys in EN/UK/RU. In-memory Python syntax
compilation passed for the changed preparation and verifier scripts, and
`git diff --check` found no whitespace errors.

**Evidence limits:** this source edit was made after build #502 started, so that
run cannot verify it. A later final-ROMFS build must pass the updated verifier.
No client test or throughput measurement has been run, and no router state was
changed. These remain open for a safe runtime test window.
