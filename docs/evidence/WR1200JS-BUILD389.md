# WR1200JS build 389 review — 2026-10-17

Firmware run https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39014006915
and service run 39014006855 completed successfully at
d1a1638a3af8ff7d2279cfaffdf62a65a2e92249.

Downloaded image WR1200JS_4.4.198.9-389_d1a1638a.trx is 12,603,587 bytes.
Locally computed SHA256 matches the original image report:
05ac69293d2c8800ec32f4fbae92512cdee8c21a13989a64b74d0453de06c084

All six uImage checks are true. Requested/effective/kernel configuration
comparison reports no mismatches and no pending options, and the router guide
check passed. The VPN profile image report passed 23/23 cases; the shipped MIPS
manager passed 15/15. The report now also lists
`usr/libexec/wrvpn/action-worker` (7004 bytes, SHA256
0f182e222da4377bf56dafca413e9cc2aec9d699a7f30df4de285ee22099c70e), and the
service script keeps SHA256
2f922b139bc4b695e54b83cfed3932e1338e629058ee15570b8ed166bc565297.

The board-port step reported `PASS added the stored-profile table and action
endpoint to the VPN page` and `PASS VPN profile table: handler, page call and
dictionary keys are present`, so `web_ex.c` and `vpncli.asp` were patched and
compiled in this image.

Not verified: device runtime, browser interaction on the router, a real tunnel,
routes, DNS and handshake. The WebUI action flow (token, POST, worker state,
page refresh) is covered by host fixtures only. Nothing was flashed or
rebooted.
