# WR1200JS build 383 review — 2026-10-17

Firmware run https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39011715710
and service run 39011715698 completed successfully at
d79f76f19f473b20a735c64fbe50210a3a52b578.

Downloaded image WR1200JS_4.4.198.9-383_d79f76f1.trx is 12,600,118 bytes.
Locally computed SHA256 matches the original image report:
9876d3e1525938f844684752c05d0375caadd103590a66c99205b1cb4ceaf0da

All six uImage checks are true. Requested/effective/kernel configuration
comparison reports no mismatches and no pending options, and the router guide
check passed. The VPN profile image report passed 23/23 cases; the shipped
MIPS manager passed 15/15, including `edit-WG`, `export-edited-WG`,
`delete-first`, `delete-missing` and `list-after-delete`. The service script in
the image has SHA256
2f922b139bc4b695e54b83cfed3932e1338e629058ee15570b8ed166bc565297 and is
byte-identical to `tools/vpn-profiles/service.sh`.

This build contains hostname endpoint pinning in `up`, the `delete` tombstone,
the validated `edit` command and the IPv6 protected-prefix guard. It predates
the read-only profile table in the WebUI.

Not verified: device runtime, a real tunnel, routes, DNS and handshake.
Nothing was flashed or rebooted.
