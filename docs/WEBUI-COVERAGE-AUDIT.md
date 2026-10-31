# WR1200JS WebUI coverage and implementation backlog

Date: 2026-10-04. Source review of project main `fcc4e1b08674236a1b5e0cd7e790c1a8f97fc2a7` and pinned vipshmily/padavan-4.4 base `c25283e915a2a00a763774dd255b14aff997285e`.

## Scope and evidence limits

The inventory covers every assignment in the central WR1200JS config: **112 options, 59 uncommented and 53 commented**. It lists **147 ASP source files** across the base and project overlay/ports, including helpers and replacement pages, and **85 menu-definition lines** from base state.js. These are source counts, not counts of installed or working pages. Patch-generated controls such as WPAD and ZeroTier are additionally reviewed through their preparation scripts. Disabled options remain disabled.

See [configuration inventory](WEBUI-CONFIG-INVENTORY.csv) and [pages, form fields, capability checks and menu definitions](WEBUI-COVERAGE-INVENTORY.json). The inventory records every selector; its default classification means no independent service UI was inferred, not that every related backend has been proven correct. No live router settings were changed and no router functionality is certified by this audit.

## Existing menu coverage

| Area | Source controls | Remaining work |
|---|---|---|
| 2.4/5 GHz Wi-Fi | Separate main, guest, mode, ACL, security, advanced and status pages | Shared main-network settings, local connection QR, Band Steering controls; prove RSSI Kick behavior. Preserve separate advanced controls and disabled defaults for new features. |
| LAN | LAN, DHCP, static routes, IPTV, switch, WOL | EoIP has project settings/status source but is disabled in WR1200JS. Build #488's exact-image report confirms the disabled selector and absence from final ROMFS; runtime remains unverified. WAN reassignment still requires actual board/switch mapping and recovery-aware apply. |
| WAN | WAN, IPv6, forwarding, DMZ, DDNS | SFE and Hardware NAT already have selectors on Advanced_WAN_Content.asp; do not claim their UI is absent. Verify offload policy with Wi-Fi and shaping. |
| Firewall | Basic firewall, netfilter, URL, MAC, rules | Integrate service-specific rules with lifecycle. IPSet/TPROXY/XFRM/IMQ/IFB are capabilities, not independent daemons requiring empty pages. |
| USB/storage | Disk functions, Samba, FTP, modem, printer; USB/IP has localized module/process status, bounded device inventory, confirmed guarded bind/unbind, and a saved export-selection table with opt-in identity-checked restore. | Runtime export/transfer and reboot persistence are unverified. Verify the documented storage-save path on-device; the export endpoint itself reports `flash_committed:false`. Disabled NFS/SMB/FTP must remain gated. Optional network-mount and partition tools need bounded shared storage controls. |
| Administration | System, services, mode, upgrade, backup, console | Extend sparse service status; finish temporary upload-space feature through its existing project task. |
| Customization | Tweaks, scripts, internet detection | Keep scripts/console as advanced tools, not the only normal configuration path for supported services. |
| Monitoring | Wireless/Ethernet, logs, DHCP leases, firewall/routes/connections, traffic pages | Add process/listener/error state for managed services and bounded diagnostics. |
| VPN | VPN client/server and WireGuard; project AmneziaWG overlays | StrongSwan currently lacks a normal configuration/lifecycle UI. Recheck final packaging: base www/Makefile removes vpncli/vpnsrv under SoftEther selectors, so overlay assets alone do not prove that these pages survive ROMFS creation. |
| Applications | Shadowsocks, SmartDNS, ZeroTier, SQM and other conditional base applications | Source availability does not imply inclusion. state.js shares application group 16 among AliDDNS/ZeroTier/DDNSTO/WireGuard using a priority chain; verify all installed services remain discoverable through cross-links in the final image. |

The application inventory also contains inherited AdGuard Home, FRP, adbyby, scutclient, mentohust, DNS-forwarder, AliDDNS, DDNSTO and Aliyun-drive pages. They are not central WR1200JS requirements simply because files exist. Check build capability and page removal before exposing a menu entry.

## Enabled services with concrete gaps

Owner scope update, 2026-10-14: StrongSwan is now commented out in the active WR1200JS profile and deferred to final optional-service work. The table below is the historical inventory, not a requirement to finish StrongSwan before current testing. See [dependency analysis and deferral](STRONGSWAN-DEFERRED.md). Its private package is independent of the retained WireGuard/AmneziaWG, ZeroTier, DNS and Wi-Fi features.

| Service | Findings and evidence | Required deliverable |
|---|---|---|
| StrongSwan / IPsec | Deferred by owner decision; `CONFIG_FIRMWARE_INCLUDE_SSWAN` is commented in the active profile. XFRM kernel support remains independently selected. | Keep StrongSwan absent from current image. If re-enabled in final optional-feature work, provide managed lifecycle, persistence, firewall integration, profiles, credentials/certificates, connection state and useful logs before exposing it as operational. |
| EoIP | Project source contains a localized eight-slot settings/status page, HTTP integration and managed controller. `CONFIG_FIRMWARE_INCLUDE_EOIP` is commented in `configs.build/wr1200js.config`. Build #488's `eoip-image-checks` report confirms the disabled selector and final-ROMFS absence; image verifier rejection cases also passed. | Keep the optional feature hidden when not built. Enable it only if selected for a future image, then verify Apply/autostart and tunnel transfer on a supervised device. The current disabled-image result does not establish runtime behavior. |
| USBIP | Enabled; localized status panel, device inventory, confirmed lifecycle-locked bind/unbind actions, export selection, default-off restore, and exact-image BusyBox/image gates are present. Current build #478 completed the restore BusyBox step and produced `usbip-settings-image`; see [build evidence](evidence/WR1200JS-BUILD478-USBIP.md). | No device runtime/transfer or reboot-persistence acceptance. Saved export rules are synchronized under `/etc/storage/usbip`, while the endpoint explicitly reports `flash_committed:false`; verify the router's storage-save lifecycle before claiming durable persistence. Keep USB/IP distinct from U2EC. |
| iPerf3 | Enable switch plus localized requested/observed process status and refresh are in the build #478 ROMFS; the live sample found it disabled with no process. | Process presence does not prove a client connection or throughput. A user-initiated, bounded test flow/readable results and device acceptance remain open; performance tests consume link capacity. |
| WPAD | Capability-gated PAC editor in DHCP persists `wpad.dat`; EN/UK/RU help states that DHCP/DNS do not announce the PAC URL and clients need manual configuration. | Source change and translations are present. The next selected image must pass the final-ROMFS translation/help gate; verify the rendered page in the router browser. Any automatic advertisement remains a separate feature requiring explicit integration and validation. |
| qrencode | Included utility, but no integrated Wi-Fi QR view found in the base wireless pages. | Implement the already accepted authenticated local QR view, payload escaping and shared/per-band settings behavior. |
| tcpdump / socat / IPv6 diagnostic tools | Included command-line utilities; no dedicated normal operation panels identified. | Shared diagnostics area. For tcpdump use interface/filter, bounded duration/file size and download. For socat expose justified supported presets rather than an unrestricted command form. IPv6 tools belong with IPv6 diagnostics. |

## Services with existing/project WebUI source

* **ZeroTier:** existing Advanced_zerotier.asp plus project prepare-ui-lifecycle and its network/status/locking/persistence/firewall helpers. Continue existing completion task and runtime acceptance; do not create a duplicate page.
* **WireGuard / AmneziaWG:** existing WireGuard page and project VPN overlays/preparation scripts. Confirm backend fields, routes, final packaged pages, keys and restart behavior. Installed binaries and visible forms alone do not establish tunnel connectivity.
* **Shadowsocks:** Shadowsocks.asp, log/action pages and capability-gated menu already exist. Inspect the final SSLOCAL/SSREDIR-to-SHADOWSOCKS selector mapping and actual processes.
* **Stubby DoT, DoH, Privoxy:** dedicated project pages and integration scripts are present. Stubby integrate-build.py actually registers UI assets/menu and other integration despite its stale completion message saying runtime/backend/UI are still required. Review the applied tree and resulting image, not that message alone. Avoid new duplicate implementations.
* **ZRAM:** project service patch modifies existing administration controls. Confirm applied configuration and runtime reporting.
* **SSH/Dropbear, HTTPS, DDNS over TLS, SFE:** existing service/WAN/DDNS/firewall controls. Library flags (OpenSSL variants, EC, curl/QUIC) do not need individual daemon switches. They require accurate dependent-service capabilities and diagnostics.
* **SQM:** the original audit snapshot contained CONFIG_FIRMWARE_INCLUDE_SQM=y; base and project contain Advanced_SQM.asp and lifecycle integration. The current requested WR1200JS profile sets CONFIG_FIRMWARE_INCLUDE_SQM=n, matching the goal excluding CAKE. Image checks reject enabled CAKE kernel selection and a shipped sch_cake.ko. Existing optional source is not evidence that the feature is enabled in this profile or running on the router.

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

Next wireless UI work remains shared main-network settings and authenticated local Wi-Fi QR; EoIP and USB/IP managed actions remain subsequent separate tasks. StrongSwan is deferred by owner decision. No missing-service completion is inferred from the Band Steering or read-only USB/IP status changes.

## Current status observations — 2026-10-13

The dated source snapshots above are not the current implementation inventory. See [actual-state contract](SERVICE-RUNTIME-STATUS-CONTRACT.md) and [build 239 evidence](evidence/WR1200JS-BUILD239.md). Current code includes background VPN handshake observations, joint interface/handshake refresh, Stubby/DoH process-state refresh and ZRAM active-swap refresh. These have native tests and selected image gates; physical browser/device acceptance remains pending. DNS process presence is not DNS/TLS health, and handshake statistics are not routing proof.

Existing shared Wi-Fi and local QR preparation/image checks are now wired into the normal build. Source/image inclusion does not establish correct behavior for the user's retained settings, both radio-page entry points or real client connections. Continue the full existing-page/backend/lifecycle/localization and hardware acceptance requirements above, including deferred optional ports and the WPS-last policy. Do not mark this audit complete based only on current green builds.

## Current wireless implementation status — 2026-10-18

This update supersedes the older Wi-Fi and `qrencode` backlog statements above;
it does not turn historical build checks into current-device acceptance.

- **Shared 2.4/5 GHz main-network controls:** implemented and checked in final
  ROMFS by build #378. Live cross-band application, preservation of independent
  settings, and persistence on the currently installed image still need device
  acceptance. See [shared Wi-Fi evidence](evidence/WR-SHARED-WIFI-BUILD-37827202052.md).
- **Local Wi-Fi QR:** page assets, payload, renderer and translations passed the
  image verifier in build #377. Scanning the generated code with a phone and
  joining the intended band/security profile have not been verified on the
  router. See [QR image evidence](evidence/WR-QR-BUILD-37796800950.md).
- **Band Steering:** the 2026-10-18 read-only sample observed its daemon and
  control socket active. No client transition or successful steering action was
  observed. See [runtime snapshot](runtime/WR1200JS-2026-10-18-ACCELERATION-STEERING-SNAPSHOT.md).
- **RSSI Kick:** both radio pages, NVRAM names, disabled defaults and driver
  commands passed the historical image gate. Runtime threshold enforcement,
  action-to-client correlation and persistence remain unverified. See
  [RSSI image evidence](evidence/RSSI-KICK-37152674078.md) and
  [action-monitor gaps](WIFI-ACTION-MONITOR.md).
- **Client monitoring:** bounded association/action recording and automatic UI
  refresh have source, ABI and synthetic-browser evidence. Router-load cost,
  real device event quality, RSSI Kick action instrumentation, and a proven
  client band transition remain open. See [roaming monitor contract](WIFI-ROAMING-MONITOR.md)
  and [browser evidence](WIFI-MONITOR-BROWSER-EVIDENCE.md).

## WPAD / PAC help localization — 2026-10-18

The capability-gated PAC editor now explains in the active UI language that
`/wpad.dat` and `/proxy.pac` are served by the router but their URL is not
announced through DHCP or DNS, so clients need a manually configured PAC URL.
The source integration adds EN/UK/RU strings and the exact-ROMFS verifier
requires the help token and each shipped translation. This keeps the existing
no-automatic-advertisement behavior explicit; it does not add DHCP/DNS
advertisement. Build #502 passed the final-ROMFS page/help check; router-
browser acceptance and actual client discovery/configuration remain pending.

Therefore this feature group is implemented in part, but is not accepted as
complete until the listed device checks are performed. No setting was changed
and no disruptive Wi-Fi test was run for this update.

## Current EoIP source and image status — 2026-10-18

This entry distinguishes optional source support from the active firmware
profile and is updated with exact-image evidence from build #488.

- Source preparation creates `Advanced_Services_EoIP.asp`, its localized
  settings/status assets and a link from Administration / Services when the
  EoIP selector is enabled. The exact-image verifier checks those files,
  translations, HTTP markers, disabled defaults and RC boot/stop hooks.
- The requested `configs.build/wr1200js.config` still comments out
  `CONFIG_FIRMWARE_INCLUDE_EOIP=y`. Build #488 uploaded `eoip-image-checks`;
  its report records `PASS disabled EoIP selector and final ROMFS absence; runtime unverified`.
  The selected-image gate also passed integrity, disabled-image absence and
  rejection cases. This verifies correct omission from the current image, not
  EoIP operation.
- Keep the EoIP shortcut hidden for this profile. Since the option is disabled,
  settings-page HTTP behavior, boot lifecycle, tunnel connectivity and frame
  transfer are not applicable to this image and remain unverified for any future
  enabled image. See [build #488 service audit](evidence/WR1200JS-BUILD488-SERVICE-AUDIT.md)
  and [EoIP managed-service evidence](EOIP-SERVICE.md).

## Current iPerf3 service status — 2026-10-18

Build #478 (`d1dc0eb`) ran the selected-image verifier against final ROMFS; its
log reports the status page, HTTP handler and EN/UK/RU labels present, and the
`iperf3-image-checks` artifact was uploaded. This proves image packaging for
that build, not test traffic or throughput. The same-day read-only router sample
reported `iperf3_enable=0` and no iPerf3 process. No start/stop test or bandwidth
test was run on the router. See [iPerf3 image evidence](evidence/WR1200JS-BUILD478-IPERF3-IMAGE.md)
and [service runtime sample](runtime/WR1200JS-2026-10-18-SERVICE-NAV.md).

Build #502 passed the final-ROMFS status page, HTTP handler and EN/UK/RU label
check. Build #503 then passed with the bounded LAN-client command/guidance from
commit `5d1385f` included; build #504 also completed successfully. These image
checks do not establish router-side client execution, traffic or throughput.

## Service navigation return path — 2026-10-18

Stubby, DoH and Privoxy shortcuts open their compact full-page views in a new
browsing context, while each standalone service page includes a return link to
Administration / Services. Build #488 passed the final-ROMFS route, page and
EN/UK/RU localization verifier, including the same-tab return destination
`/Advanced_Services_Content.asp`. Physical router-browser click-through is
still unverified; the firmware has not been installed for this check. Other
service shortcuts retain their agreed navigation behavior. See
[navigation evidence](evidence/WR1200JS-SERVICE-NAV-LAYOUT-2026-10-18.md).

## StrongSwan optional-service image gate — 2026-10-18

StrongSwan is deferred and excluded from the active WR1200JS profile; this is
not a missing current WebUI service. Build #478's main image policy gate
required the selector to remain disabled and rejected its principal binaries
and libraries in ROMFS. Build #502 now passes the explicit exclusion verifier
and uploads `strongswan-image-checks`; the prior missing-report gap is closed
for that image. See [build #502 service evidence](evidence/WR1200JS-BUILD502-SERVICE-AUDIT.md).
This still does not establish runtime behavior for a feature intentionally
excluded from the active profile.

## Service/WebUI image refresh — 2026-10-20

Build #502 passed the unified service navigation route/page/EN/UK/RU check,
the Shadowsocks final-page CJK and dictionary check, settings backup/restore
route and safe-session/browser-harness checks, USB/IP settings and target
BusyBox fixtures, Stubby dependency checks plus a QEMU authenticated DoT query,
WPAD/PAC localized final-ROMFS checks, KMS/Watchdog status UI checks, and the
247-file `/www`-to-httpd-route audit. The run also produced the explicit
StrongSwan exclusion report. These are CI and built-image results; they do not
prove live Apply, service lifecycle, physical browser behavior or persistence.
See [build #502 service evidence](evidence/WR1200JS-BUILD502-SERVICE-AUDIT.md).

At the original #502 checkpoint, builds #503 and #504 were still in progress;
that historical status is superseded by the follow-up below. The target BusyBox
audit still explicitly reports the whole service/runtime audit as open.

## Build #504 follow-up — 2026-10-20

The earlier in-progress note above was refreshed: build #504 completed
successfully for PR head `9c1e9b169acc28dd621e3374a81297755b16fa55`. Its CI
passed unified service navigation and locale checks, Stubby packaging plus an
authenticated DoT lookup through the image binaries under QEMU, DoH packaging,
the target BusyBox service audit, and the final served-WebUI route check. See
[build #504 service evidence](evidence/WR1200JS-BUILD504-SERVICE-AUDIT.md).
Its job log also confirms the settings-backup final-ROMFS verifier and
synthetic browser-behavior fixture passed: route, secure-session gate,
localized labels, safe-session actions, uploads/downloads and save feedback.
This does not prove operation in a physical browser or successful backup/
restore on the router.

The separate Service runtime state checks #247 passed source-level fixtures for
SSH/iPerf3/Privoxy observation expiry, Cron and LLTD/ASUS/KMS/Watchdog state,
VPN profile lifecycle logic, and USB/IP guards. Its VPN and USB/IP device
operations are mocked; it is neither firmware/image nor physical-router
evidence. See [run #247 evidence](evidence/WR1200JS-SERVICE-STATE-CHECKS-247.md).

This is CI/image evidence only. Router-side service lifecycle, live DNS
behavior, persistence and physical browser use remain open. The local
unsupported PPTP/L2TP selector fix is commit `35d70be`, after the PR head, and
is therefore absent from #504; its final-ROMFS/browser verification still
requires a build containing that change. The target BusyBox report continues
to mark the complete service/runtime audit open.

## Unsupported VPN choices removed from WR1200JS pages — 2026-10-20

Source review found that the inherited VPN client and server selectors still
offered PPTP and standalone L2TP even though the WR1200JS profile excludes
them. The source preparation now removes those choices on both pages, and the
OpenVPN absence check targets its option value instead of a brittle index.
The build-time WebUI checker covers both pages and an in-memory transformation
fixture. Source checks passed locally; final-ROMFS and browser verification are
pending. See
[unsupported VPN UI evidence](evidence/WR1200JS-UNSUPPORTED-VPN-UI-2026-10-20.md).
