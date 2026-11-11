# IoT network evidence recheck

This recheck corrects the scope of older packet-only status notes; it does not
activate IoT or establish router acceptance.

Successful ABI run42686718338, source5a3caacbdd6daf64e9ac4354a291ecc9a67788ab,
artifact13705960541 independently inspected in memory. The named real DHCP/DNS
step completed/succeeded in job129395824415. Its actual archived reports contain
13 protocol/readiness checks and21 filter checks, all true. Native daemon reports
dnsmasq2.90, built from pinned SDK; not the installed router daemon.

Protocol test uses actual DHCP DISCOVER/OFFER/REQUEST/ACK, matching XID/client MAC
and cookie, lease range, server ID, mask, router and DNS options. DNS verifies
transaction ID, response/rcode/question/answer and known fixture A record for IoT
and Main LAN. Checks include DHCPINFORM lease preservation, daemon ownership/
socket readiness, daemon-stop refusal and alternate DHCP port. This exceeds UDP
port echo coverage, but does not prove real ISP DNS or internet connectivity.

Four primary current files match exact historical Git bytes: check-dhcp-
transactions.py, dhcp-write.c, firewall.h, bridge.c. All392 tracked C/H inputs
under tools/iot and tools/shared-wifi compare equal after explicit CRLF-to-LF
normalization;10 have line-ending-only byte differences. This is not a claim
of raw-byte equality for the entire input set. Driver-generation Python/shell
changes are outside this network evidence and receive no acceptance here.
Manifest fingerprint and report hashes in companion JSON.

| Evidence layer | Result |
|---|---|
| Native dnsmasq IoT/Main DHCP/DNS transactions in isolated host namespaces | Verified historical CI, source correspondence refreshed |
| IPv4 and IPv6 routed packet filtering with static IPv6 neighbors |21 host checks verified |
| Dynamic IPv6 neighbor discovery / IPv6 internet service | Not verified; candidate policy blocks IoT IPv6 |
| Driver ownership, first beacon, RF/TxS retirement and RC activation binding | Not established by these reports |
| Final target image / actual Main-Guest-IoT client traffic on WR1200JS | Not established |

Do not repeat the claim that only DHCP ports have ever been tested. Do not
upgrade host evidence to target/runtime or treat unchanged network sources as
approval of changed driver generators. Original ROM ACK/stale TxS boundaries
and unbound activation/radio-stop controller remain open. Next implementation
work should address that lifecycle composition rather than repeat unchanged
host DHCP tests without a new failure or source change.

Cleanup: artifact ZIP/report/traffic files read in memory only. No namespace,
router, daemon, root launcher or retained scratch directory created by recheck.
Compact evidence retained; original source/previous evidence preserved.
