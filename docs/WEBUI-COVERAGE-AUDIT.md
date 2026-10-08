# WR1200JS WebUI coverage and implementation backlog

Date: 2026-10-04. Source review of project main `fcc4e1b08674236a1b5e0cd7e790c1a8f97fc2a7` and pinned vipshmily/padavan-4.4 base `c25283e915a2a00a763774dd255b14aff997285e`.

## Scope and evidence limits

The inventory covers every assignment in the central WR1200JS config: **112 options, 59 uncommented and 53 commented**. It lists **147 ASP source files** across the base and project overlay/ports, including helpers and replacement pages, and **85 menu-definition lines** from base state.js. These are source counts, not counts of installed or working pages. Patch-generated controls such as WPAD and ZeroTier are additionally reviewed through their preparation scripts. Disabled options remain disabled.

See [configuration inventory](WEBUI-CONFIG-INVENTORY.csv) and [pages, form fields, capability checks and menu definitions](WEBUI-COVERAGE-INVENTORY.json). The inventory records every selector; its default classification means no independent service UI was inferred, not that every related backend has been proven correct. No live router settings were changed and no router functionality is certified by this audit.

## Existing menu coverage

| Area | Source controls | Remaining work |
|---|---|---|
| 2.4/5 GHz Wi-Fi | Separate main, guest, mode, ACL, security, advanced and status pages | Shared main-network settings, local connection QR, Band Steering controls; prove RSSI Kick behavior. Preserve separate advanced controls and disabled defaults for new features. |
| LAN | LAN, DHCP, static routes, IPTV, switch, WOL | Add usable EoIP tunnel management; WAN reassignment requires actual board/switch mapping and recovery-aware apply. |
| WAN | WAN, IPv6, forwarding, DMZ, DDNS | SFE and Hardware NAT already have selectors on Advanced_WAN_Content.asp; do not claim their UI is absent. Verify offload policy with Wi-Fi and shaping. |
| Firewall | Basic firewall, netfilter, URL, MAC, rules | Integrate service-specific rules with lifecycle. IPSet/TPROXY/XFRM/IMQ/IFB are capabilities, not independent daemons requiring empty pages. |
| USB/storage | Disk functions, Samba, FTP, modem, printer | U2EC has controls; USBIP is a separate missing feature. Disabled NFS/SMB/FTP must remain gated. Optional network-mount and partition tools need bounded shared storage controls. |
| Administration | System, services, mode, upgrade, backup, console | Extend sparse service status; finish temporary upload-space feature through its existing project task. |
| Customization | Tweaks, scripts, internet detection | Keep scripts/console as advanced tools, not the only normal configuration path for supported services. |
| Monitoring | Wireless/Ethernet, logs, DHCP leases, firewall/routes/connections, traffic pages | Add process/listener/error state for managed services and bounded diagnostics. |
| VPN | VPN client/server and WireGuard; project AmneziaWG overlays | StrongSwan currently lacks a normal configuration/lifecycle UI. Recheck final packaging: base www/Makefile removes vpncli/vpnsrv under SoftEther selectors, so overlay assets alone do not prove that these pages survive ROMFS creation. |
| Applications | Shadowsocks, SmartDNS, ZeroTier, SQM and other conditional base applications | Source availability does not imply inclusion. state.js shares application group 16 among AliDDNS/ZeroTier/DDNSTO/WireGuard using a priority chain; verify all installed services remain discoverable through cross-links in the final image. |

The application inventory also contains inherited AdGuard Home, FRP, adbyby, scutclient, mentohust, DNS-forwarder, AliDDNS, DDNSTO and Aliyun-drive pages. They are not central WR1200JS requirements simply because files exist. Check build capability and page removal before exposing a menu entry.

## Enabled services with concrete gaps

| Service | Findings and evidence | Required deliverable |
|---|---|---|
| StrongSwan / IPsec | CONFIG_FIRMWARE_INCLUDE_SSWAN=y; base user/strongswan/Makefile installs ipsec/charon/starter/stroke and uses /etc/storage/strongswan. No StrongSwan/IPsec UI or matching service integration found in the inspected rc/httpd sources. | First establish managed start/stop, persistence and firewall integration, then profiles, credentials/certificates, remote networks, connection state and useful logs. Do not label the packaged binaries as an operational VPN. |
| EoIP | Enabled; overlay scripts/integrate-eoip.py registers kernel/eoip-ctl build assets. No matching WebUI found. | Tunnel table, endpoints, tunnel ID, MTU, optional bridge assignment, enable/autostart, lifecycle and status. Validate conflicts and preserve unrelated interfaces. |
| USBIP | Enabled; add-usbip build integration found, no corresponding ASP management found. | Device inventory, explicit export/unexport, service state and persistence; distinguish USBIP from the existing U2EC printer service. |
| iPerf3 | Advanced_Services_Content.asp provides an enable switch. | Server status and selected supported parameters; bounded start/stop of diagnostics and readable results. Performance tests consume link capacity and must be user initiated. |
| WPAD | integrate-wpad.py adds a capability-gated PAC editor to DHCP and persists wpad.dat. It explicitly adds no DHCP/DNS advertisement. | Explain PAC use and current advertisement behavior; a normal configuration wizard or optional advertisement needs separate integration and validation. |
| qrencode | Included utility, but no integrated Wi-Fi QR view found in the base wireless pages. | Implement the already accepted authenticated local QR view, payload escaping and shared/per-band settings behavior. |
| tcpdump / socat / IPv6 diagnostic tools | Included command-line utilities; no dedicated normal operation panels identified. | Shared diagnostics area. For tcpdump use interface/filter, bounded duration/file size and download. For socat expose justified supported presets rather than an unrestricted command form. IPv6 tools belong with IPv6 diagnostics. |

## Services with existing/project WebUI source

* **ZeroTier:** existing Advanced_zerotier.asp plus project prepare-ui-lifecycle and its network/status/locking/persistence/firewall helpers. Continue existing completion task and runtime acceptance; do not create a duplicate page.
* **WireGuard / AmneziaWG:** existing WireGuard page and project VPN overlays/preparation scripts. Confirm backend fields, routes, final packaged pages, keys and restart behavior. Installed binaries and visible forms alone do not establish tunnel connectivity.
* **Shadowsocks:** Shadowsocks.asp, log/action pages and capability-gated menu already exist. Inspect the final SSLOCAL/SSREDIR-to-SHADOWSOCKS selector mapping and actual processes.
* **Stubby DoT, DoH, Privoxy:** dedicated project pages and integration scripts are present. Stubby integrate-build.py actually registers UI assets/menu and other integration despite its stale completion message saying runtime/backend/UI are still required. Review the applied tree and resulting image, not that message alone. Avoid new duplicate implementations.
* **ZRAM:** project service patch modifies existing administration controls. Confirm applied configuration and runtime reporting.
* **SSH/Dropbear, HTTPS, DDNS over TLS, SFE:** existing service/WAN/DDNS/firewall controls. Library flags (OpenSSL variants, EC, curl/QUIC) do not need individual daemon switches. They require accurate dependent-service capabilities and diagnostics.
* **SQM:** central config currently contains CONFIG_FIRMWARE_INCLUDE_SQM=y; base and project contain Advanced_SQM.asp and lifecycle integration. This contradicts the earlier goal wording excluding CAKE. This audit does not change the setting or claim shaping is running: reconcile the documented scope with the current config in the SQM task. Upstream Linux 4.4 alone is not proof of native CAKE availability; project backports/integration are the evidence to check.

## Disabled optional packages

* **SmartDNS:** substantial existing Advanced_smartdns.asp and backend integration. When explicitly included, verify packaging, fields, status and consistent translations; do not implement from scratch.
* **Samba/WINS, FTP/TLS, NFS server, printing:** existing storage/printer pages and conditional backend controls. NFS has at least an enable control; review exports/access configuration for practical completeness. Keep requested commented selectors. Optional build verification remains required.
* **NFS/CIFS clients, parted, hdparm, ADB:** possible shared storage/diagnostics controls when built; these are not all permanent services. Commented selectors are not proof their enabled builds work.
* **OpenSSH/SFTP, OpenVPN, RPL2TP:** integrate into applicable SSH/VPN pages when included and validate actual prerequisites. Do not expose a disabled package as available.
* **DNSCrypt, Redsocks2, Tor/GeoIP/OBFS4, NFQWS/Zapret/Zapret2:** no dedicated project/base ASP management was identified in this snapshot. Keep disabled and preserve the heavy-package second-stage decision. Implement lifecycle and capability-gated normal controls only when their optional port is supported; GeoIP datasets do not need their own service pages.
* **WPS:** remains excluded. Optional commented central build selector and its separately verified build stay the **last WR1200JS feature task**. Do not enable WPS to fix Band Steering.

## Implementation order and completion contract

1. Finish current WR1200JS driver/service integration and protect remote access; complete Band Steering source/runtime work before enabling it on a router.
2. Implement shared Wi-Fi settings, local QR and Band Steering WebUI, preserving existing independent settings; verify RSSI Kick.
4. Review every existing enabled-service page against backend field registration, validation, capability gate, restart dispatch, persistence and actual image packaging; fix navigation discoverability and stale labels.
5. Verify optional commented features separately without enabling heavy packages in the main image. Keep WPS last. Secondary Mi Mini work must not delay WR1200JS.

For each managed service: documented enable/configuration, validated inputs, actual running/error status, start/stop/restart semantics, autostart and persistence, appropriate logs, translated help and capability-gated navigation. New services are off at first flash unless an explicitly accepted policy says otherwise. Missing packages must have no operational-looking controls. Completion requires build evidence, image-content checks and later router acceptance; source inspection is the current evidence level. Preserve the active central configuration during this audit.

## Verified build update — 2026-10-08

The original inventory above remains a dated source snapshot. Coordinated WR Band Steering now has a requested-state switch on the 2.4 GHz advanced page and an explicit status-refresh button for both radios. [Status semantics](BAND-STEERING-STATUS.md) and [image evidence](evidence/WR-IMAGE-37787484281.md) distinguish packaged controls from runtime proof. Shared SSID configuration, Wi-Fi QR integration and client/runtime acceptance remain outstanding.

[Build 37790206125](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37790206125) passed with Wi-Fi HNAT mode handling and a factory LAN-only default. The existing WAN mode selector remains available. This does not establish Wi-Fi stability or modify a user's saved runtime NVRAM.

Next wireless UI work remains shared main-network settings and authenticated local Wi-Fi QR; StrongSwan, EoIP and USBIP managed backends/pages remain subsequent separate tasks. No missing-service completion is inferred from the Band Steering changes.
