# WR1200JS process status observation — local audit

Date: 2026-10-18

## Finding

The pinned Padavan `pids()` helper reduces process enumeration to `1` when
any matching PID is found and `0` otherwise. Its caller cannot distinguish an
empty process list from failures encountered while scanning `/proc`. The
service UI adapters had extra `/proc/self/stat` checks, but that does not prove
that the complete process table and each process `comm` file were readable.

Affected UI adapters were Stubby/DoH, SSH, Cron, Privoxy, iPerf3, Shadowsocks
client and USB/IP daemon. Their enabled-but-unobserved state could therefore be
shown as “not running” after a partial process-observation failure.

## Change

These adapters now call the shared `wr_process_present()` observation emitted
by `prepare-discovery-status.py`. It scans numeric `/proc/<pid>/comm` entries,
returns present/absent only after a complete scan, ignores process-exit races
(`ENOENT`/`ESRCH`), and returns unknown on procfs open/enumeration/read errors.
The UI still reports process presence only; it does not claim DNS resolution,
VPN reachability, proxy traffic, iPerf throughput, Cron job success or USB/IP
client connectivity. No service settings or lifecycle actions were changed.

The WR1200JS SSH image verifier now requires the DNS, SSH, Cron, Privoxy,
iPerf3, Shadowsocks and USB/IP status handlers in the final image.

## Local checks

- `python tools/check-discovery-status.py --output .discovery-proc-shared-selftest` — PASS; emitted UI fixture and host C fixture cover present, absent, proc open failure, readdir error and unreadable `comm`.
- `python tools/check-cron-status.py --output .cron-proc-status-selftest` — PASS; configured/observed states and unknown/error behavior.
- `python tools/check-usbip-status.py` — PASS; settings, UI, hidden-page and refresh fixture.
- `python tools/prepare-usbip-status-check.py --output .usbip-process-status-check.c`; MinGW `gcc -std=c99 -Wall -Wextra -Werror ...`; executable — PASS; emitted USB/IP handler states and invalid arguments.
- Python AST compilation for all edited generators/checkers — PASS.
- No `pids(` calls remain in `tools/prepare-*-status.py`.

## Limits and next evidence

No target MIPS compile or final ROMFS build has yet tested this change. CI image
verification and physical browser acceptance remain pending. The observer does
not alter or restart a service. The separate Padavan `is_stubby_run()`,
`is_doh_run()` and `is_privoxy_run()` lifecycle helpers still call `pids()`;
they are outside this WebUI-status patch and need a separate lifecycle review.
The router remains unchanged on the user-confirmed build #396.
