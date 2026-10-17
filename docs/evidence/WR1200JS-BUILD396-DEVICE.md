# WR1200JS build 396 — initial physical acceptance, 2026-10-17

The user explicitly authorised remote flashing despite no person being beside
the router. Private local backup completed before writes: full 16 MiB flash,
live storage archive and NVRAM. Backups remain outside this repository under
C:/Users/ANDRZEJ/Documents/Codex/private-router-backups/WR1200JS-before396-20261017-114638/.
No private config values or raw logs are published here.

Image 396_82233894 SHA256 matched locally and in router /tmp:
eb570de35f78eb01e7722931aef3007333f12cce1439a89a2ed292061c3a243a
Current NVRAM/storage were saved. mtd_write write targeted firmware only;
mtd_write verify returned success and FLASH_WRITE_AND_VERIFY_OK was observed.
A normal rc reboot did not immediately reset uptime; BusyBox lacks reboot applet.
The mtd_write -r verify reboot fallback was invoked, and the user then reported
restart. New boot ID and uptime confirm reboot; do not attribute it uniquely to
one trigger. Actual running version: 4.4.198.9-396_82233894, kernel 4.4.198 built
Sat Oct 17 09:17:02 UTC 2026. Manager and action-worker hashes match build reports.

Observed on physical router after reboot:
- SSH reachable through the existing tunnel; LAN address and default route preserved.
- Existing wg1 tunnel interface retained. No new profile was created or activated.
- Two ICMP requests to a public IP succeeded, with no packet loss in this small sample.
- Local dnsmasq resolved example.com. Stubby/DoH processes were not running as intended.
- /dev/zram0 is active swap: 30,912 KiB, zero used at observation.
- Updated check-device-readonly.sh returned RESULT OK / exit 0. Manager, service,
  worker and profile list checks passed; no new status-query/reaper noise in 30 s.
- Seventeen pre-existing selected LAN/DHCP/WAN/Wi-Fi/security/DNS NVRAM keys matched
  the private pre-flash snapshot. This is a selected-key comparison, not proof that
  every setting/file or all operational behaviour is preserved.

Remaining: Wi-Fi client behaviour/throughput and longer stability, new independent
WG/AWG profile lifecycle/routing/DNS/QR acceptance, WebUI upgrade through VPN,
IoT isolation, WAN reassignment and complete target BusyBox/service interactions.
This is verified initial physical boot/basic connectivity, not complete port acceptance.
