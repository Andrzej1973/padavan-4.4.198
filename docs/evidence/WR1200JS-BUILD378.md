# WR1200JS build 378 review — 2026-10-17

Firmware run https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39010171779
and service run 39010171751 completed successfully at
69f91b669ab01fa610863db756973bcb831abd26.

Downloaded image WR1200JS_4.4.198.9-378_69f91b66.trx is 12,597,918 bytes.
Locally computed SHA256 matches the original image report:
1af61c8d4a40bfb0ac7709b41ea7287c9d596a63706faaac969c57e95714dd18

All six uImage checks are true. Requested/effective/kernel configuration
comparison reports no mismatches and no pending options, and the router guide
check passed. The VPN profile image report passed 23/23 cases and the shipped
MIPS manager passed 10/10; `usr/sbin/wr-vpn-profiles-service` has SHA256
2f922b139bc4b695e54b83cfed3932e1338e629058ee15570b8ed166bc565297 and is
byte-identical to `tools/vpn-profiles/service.sh` at this commit, including the
`set -e` fix for a missing stored profile.

This build contains the IPv6 protected-prefix guard, strict protected-prefix
parsing (whitespace trim, overflow refusal), the pre-transport refusal for
missing protected prefixes, and runtime-only id teardown. It predates hostname
endpoint pinning in `up` and the `delete` command, which are in build 380.

Not verified: device runtime, a real tunnel, routes, DNS and handshake.
Nothing was flashed or rebooted.
