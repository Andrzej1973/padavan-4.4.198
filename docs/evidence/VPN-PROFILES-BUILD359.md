# Independent VPN tools — build 359

- Run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38956267665
- Commit: 8a687e2f374e84d69cecc31c9055907a186e379d
- Full firmware workflow: completed / success, checked 2026-10-16.
- Downloaded artifact: vpn-profile-image. Reports are stored beside this file.

The shipped profile CLI and WG/AWG validators are executable little-endian
32-bit MIPS ELF files. Seventeen validator cases passed under QEMU using the
image's libraries: ordinary WG/AWG configs, protocol-specific fields, rejected
bad keys/hooks/manual tables and 32-bit H1 bounds/ranges. CLI rejects an invalid
ID before opening a store. Binary sizes and SHA256 are in the JSON report.

The MIPS-compiled link observation fixture also passed under QEMU. It exercises
bounded netlink parsing, identity matching and read-only loopback/missing-interface
queries against the CI host kernel. It does not test the physical router kernel.

The UAPI include fix resolves build 358's validate-wg compilation failure.
This report does not establish target CLI fork/exec/storage integration, real
link mutations, configured independent simultaneous tunnels, routing/DNS, WebUI,
throughput or physical-router acceptance. Newer unshipped lifecycle/config-plan
candidates are not part of build 359. The router was not flashed or changed.
