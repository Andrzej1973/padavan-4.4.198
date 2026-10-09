# WR1200JS DHCP port readiness

[Commit 288b9d8](https://github.com/Andrzej1973/padavan-4.4.198/commit/288b9d8914586041b6c162ebf7fa659e6020b50e) reads the DHCP server port from the bounded configuration reader and preserves it separately for the old service and new candidate. Default port 67 remains unchanged. Bare `dhcp-alternate-port` selects 1067; explicit server/client values follow pinned dnsmasq 2.93 option parsing.

Before completing a restart or recovery, the controller requires the configured UDP port to belong to the unique trusted dnsmasq executable, then requires a bounded DHCPINFORM ACK. DNS checks remain separate. Socket ownership alone does not establish protocol readiness.

## Inspected evidence

[ABI 210](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37985927204) completed successfully. Its downloaded `band-steering-mips-abi` artifact contains an `iot-dhcp-transactions.json` report confirming:

- Actual pinned native dnsmasq owns alternate UDP port 1067, and port 67 is absent in that alternate-port fixture.
- DHCPINFORM responds on 1067 for the LAN and IoT gateway addresses without changing the lease file.
- Standard LAN/IoT DHCP OFFER/ACK, DNS and lease-preservation checks pass.

The actual controller fixture also covers a candidate socket-readiness failure and recovery using an old configuration with alternate server port 1067. Its daemon callbacks are injected; this is not execution of production RC on the router.

Downloaded MIPS objects:

- Controller fixture: 61,280 bytes; SHA-256 `556271180e64ab57f671e128b307bf18538d2fd37e91eaa035e2400524142eb9`.
- Socket fixture: 16,516 bytes; SHA-256 `ad4223b16f3812590b44ac1126331bed9daea58dfcf1d98034b47b29562aef41`.

## Remaining work

[Full build 120](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37985927189) remains pending at this checkpoint. Target runtime is unverified. Dynamic `conf-script`, DHCP ignore rules and DHCP with loopback excluded still need compatible readiness handling. These tests do not prove complete IoT activation, wireless isolation or remote tunnel reconnection. No router settings were changed.
