# IoT RC ABI evidence — 2026-10-18

Run [39113907911](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39113907911)
completed successfully for project commit `52c802b8b90a2de720ded007abc1bae6d3daa25d`.
Pinned donor source: `c25283e915a2a00a763774dd255b14aff997285e`.
Downloaded artifact: `band-steering-mips-abi`, artifact ID `12131333653`.

Independent inspection of `iot-services-ex-mips.o` confirmed ELF32,
little-endian, ET_REL, EM_MIPS. Its SHA-256 matches the compile report:
`5abe19f9fd90d928616dacadc5b0b87e4d09654d20d0e3cb6e75ec761a037bad`.
The report records prepared `services_ex.c` SHA-256
`50491787a42750af852a454806b4ad946114eb5cfedc8ac3e8880d7a4617375b`;
the prepared source itself was not independently rehashed from this artifact.

Downloaded `iot-dhcp-transactions.json` has 13 passing checks using pinned
native dnsmasq: separate IoT/LAN OFFER/ACK pools and options, DNS responses,
existing lease preservation, process-owned sockets, stopped-daemon rejection,
alternate DHCP port and no-hosts/no-ident DNS readiness.
`iot-firewall-packets.json` has 21 passing host-kernel checks for IPv4 TCP/UDP,
DHCP source-port filtering, stale conntrack isolation, preserved main-LAN WAN,
and IPv6 isolation. IPv6 uses static neighbors; NDP is not verified.

These are host integration and MIPS object results. They do not prove linked
production IoT firmware, live radio capacity, three concurrent SSIDs, hardware
offload isolation or physical-device lifecycle. `iot-rc-source.json` still
reports `activation_integrated: false`, `writer_journal_lifecycle_bound: false`
and `dnsmasq_service_rollback_complete: false`. Production activation and the
remaining writer/rollback lifecycle must be implemented before acceptance.
