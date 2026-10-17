# WR1200JS build 391 review — 2026-10-17

Firmware run https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39017562960
and service run 39017562977 completed successfully at
9e08a95ed9fb5589c6b554b5c1d7e923f501cee2.

Downloaded image WR1200JS_4.4.198.9-391_9e08a95e.trx is 12,604,115 bytes.
Locally computed SHA256 matches the original image report:
53dd84b70d04728a983024a1b039c18fe64b0906d18b23111767e4b9c26dc41e

All six uImage checks are true. Requested/effective/kernel configuration
comparison reports no mismatches and no pending options, and the router guide
check passed. The VPN profile image report passed 23/23 cases; the shipped MIPS
manager passed 15/15. `usr/libexec/wrvpn/action-worker` is present with SHA256
0f182e222da4377bf56dafca413e9cc2aec9d699a7f30df4de285ee22099c70e.

The board-port step reported the stored-profile table, action endpoint and
export handlers as integrated, `web_ex.o` compiled and `httpd` linked. Service
run 39017562977 passed the action-endpoint, export-endpoint, worker, list and
render host fixtures, including CSRF/`ack` guards, canonical ids, exact worker
argv, JSON escaping and timeout/overflow states.

Not verified: device runtime and browser behaviour on the router. Nothing was
flashed or rebooted.
