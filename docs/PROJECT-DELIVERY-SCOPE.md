# WR1200JS project delivery requirements

User-approved extension, 2026-10-02.

Primary objective remains the Linux 4.4.198 port of YOUHUA WR1200JS,
preserving the user's configuration and required features, excluding CAKE
under the active thread objective reaffirmed on 2026-10-08. Earlier CAKE
proposals below are retained as history and are outside the current delivery.
Compilation alone does not establish a successful device port.

## Delivery order — user confirmation 2026-10-10

1. Finish YOUHUA WR1200JS first: complete the accepted firmware and WebUI work, verify the target build and image, then verify device behavior with the user. Compilation alone is insufficient. Preserve the central configuration and keep CAKE excluded.
2. Immediately after WR1200JS, complete Xiaomi Mi Mini with the reduced profile and stable 5 GHz wireless uplink/repeater requirements already recorded below.
3. After both router stages, finish the local source/reference databases and complete offline preservation and the verified WSL 2 offline build project.

Defer offline preservation and donor/database expansion until stage 3. Retain existing backups. This changes task order; it does not remove any accepted deliverable. Report concrete completed steps and maintain a short working checkpoint.

## WR1200JS execution sequence — user approval 2026-10-10

Complete these steps in order, carrying all existing acceptance requirements forward:

1. IoT Wi-Fi: finish activation/shutdown and recovery; integrate the third BSS, owned bridge, DHCP/DNS, isolation/firewall and scoped WAN NAT; add authenticated enable/SSID/credentials/subnet/status/local QR controls; verify simultaneous main/guest/IoT operation and isolation.
2. Wi-Fi and roaming: finish shared 2.4/5 GHz controls and QR, Band Steering, RSSI Kick and automatically refreshed monitoring. Establish actual supported 802.11k/v/r behavior; never equate compilation or RSSI disconnection with FT roaming.
3. Service WebUI coverage: complete lifecycle, validation, persistence, status and navigation for accepted enabled services, including outstanding IPsec/EoIP/USBIP/diagnostics work and existing ZeroTier/VPN integration.
4. WAN socket reassignment: finish authenticated selection and verify selected WAN/remaining LAN isolation and persistence.
5. Final configuration/image audit: preserve required features, verify optional commented selectors separately and keep WPS optional verification last. Deliver one user download ZIP containing firmware and its config. CAKE stays excluded.
6. Recoverable device acceptance: verify Linux 4.4.198 boot, WAN/LAN, both Wi-Fi bands under load, restored AmneziaWG, settings/services and restart persistence. User agreement on task order is not authorization to flash or disrupt the remote router.

## Preserve and port existing services — user instruction 2026-10-11

Treat the job as a port of the existing Padavan firmware, not a replacement
WebUI or a collection of newly invented daemons. Audit the enabled services,
conditional/disabled service selectors, resolver and strategy lists, menu
routes, translations, save/restore behavior and image contents against the
pinned base and the named Nilabsent donor. Reuse working donor implementations
when their source version and target dependencies are suitable; record version,
origin and data-list hashes. Never infer that a commented selector can build
until its package recipe and runtime integration are verified.

Retain the existing Administrator/Settings backup page and verify that the
compiled ROMFS contains its menu route, NVRAM reset/save/restore controls,
`/etc/storage` reset/backup/restore controls, commit setting and persistence
controls. The Padavan source deliberately hides destructive/backup actions
until `login_safe()` accepts the management session; preserve this gate and
test the page from safe LAN or HTTPS after the firmware is running. Missing
controls in an unsafe session must be diagnosed without weakening the gate.

DNS findings and the service-by-service source map are tracked in
`DNS-DOT-DOH-LOCALIZATION-AUDIT.md` and
`SERVICE-PORT-AND-SETTINGS-AUDIT.md`. DoT/DoH runtime behavior, provider lists,
time bootstrap and no-plaintext fallback require router verification. DNSCrypt
must remain disabled until its optional Nilabsent-derived port and maintained
resolver-list compatibility are proven. Tor and Zapret/Zapret2 remain Stage 2
work after WR1200JS device acceptance, as previously agreed; their lists and
source revisions must be preserved when that stage begins.

After this WR1200JS sequence, complete Mi Mini, then the local databases/offline project. Record build/image evidence separately from device acceptance; leave unverified items open.

## Authoritative development location — user confirmation 2026-10-03

All subsequent implementation, configuration, package, board-port and build
system work belongs in Andrzej1973/padavan-4.4.198, branch main. Preserve
Andrzej1973/youhua-wr1200js-nilab and its experimental/Padavan-4.4.198 branch
as a historical reference and control point; do not continue primary
development there. This changes the development location, not the accepted
firmware requirements or outstanding verification and preservation work.

## Second router and dual-image CI — user instruction 2026-10-03

Latest user confirmation: include this task in the project goal. The Mi Mini
profile must keep Samba/WINS and related tools, miniDLNA, Transmission/Web
Control and Aria/Web Control disabled, with commented selectors and clear
documentation for optional future builds. Preserve the full WR1200JS profile.
Deliver the second board port and a normal workflow producing two distinct
firmware images; the successful isolated radio compilation does not complete
this goal. Track this extension here alongside the existing active goal.

Confirmed as part of the overall project objective by the user: adapt the
Linux 4.4.198 firmware to Xiaomi Mi Mini alongside WR1200JS, prepare its reduced
documented config, and make one normal CI run produce both board images once
the second board port passes compilation and image checks. Completion requires
working board-specific build paths and two distinct verified image artifacts;
local config edits alone do not complete this requirement. Runtime validation
remains a separate step subject to device access and recovery constraints.

User approved a reduced MI-MINI profile excluding Samba/WINS and related tools,
miniDLNA, Transmission including Web Control, and Aria including Web Control.
Keep these selectors commented with explanations. This changes the second
router profile; it does not remove existing WR1200JS functionality.

User requests adapting this firmware/config to their second router linked at
https://4pda.to/forum/index.php?showtopic=686221 and producing two images in
each subsequent build. A reduced feature set is permitted for the second
device to enable initial testing. It currently runs Padavan, version unknown,
and has no Breed bootloader according to the user.

User confirms no physical access and Padavan 3.4 installed, with no Breed.
Exact model/revision and SSH access remain unconfirmed. User recalls a first
version; this is insufficient to select the board image.
Search results associate the topic with Xiaomi Mi WiFi Mini; this is not
proof of the user's hardware identity. Current pinned 4.4 README lists MT7621
devices and does not list Mi Mini. SOC_MT7620 exists in Kconfig, which alone
does not establish working drivers/board support.

After identification, inspect SoC, RAM/flash, radios, GPIO/EEPROM, partition
layout, current bootloader and supported recovery route. Port board support
and derive a separate documented reduced config from the central feature
policy. Keep independent build trees and distinct image names/artifacts,
ProductID/CRC/size checks and effective configs for both boards. A successful
second-router test must not be claimed to verify WR1200JS-specific hardware.
Do not flash either router as part of CI integration or replace its bootloader.
Dual-image CI has not yet been implemented.

## Updated delivery order — user instruction 2026-10-03

Stage 1: prioritize a coherent WR1200JS image and prompt testing on the actual router. Preserve the user's configuration and complete the necessary build/device readiness checks. Do not delay initial device testing for the packages listed below or other-board expansion.

Stage 2, after the WR1200JS firmware is ready: port CONFIG_FIRMWARE_INCLUDE_TOR, CONFIG_FIRMWARE_INCLUDE_TOR_GEOIP, CONFIG_FIRMWARE_INCLUDE_TOR_GEOIPV6, CONFIG_FIRMWARE_INCLUDE_ZAPRET and CONFIG_FIRMWARE_INCLUDE_ZAPRET2. Keep these documented but disabled in the stage-1 build config. Also migrate the remaining nilabsent router configurations to this firmware base, checking each board's hardware requirements individually.

These are deferred requirements, not removed from the project. Existing backup/source preservation requirements remain. Other required features are not silently removed by this staging decision.

## Optional storage/network packages — user instruction 2026-10-03

ADB is also optional, per the later user instruction on 2026-10-03. Keep
`# CONFIG_FIRMWARE_INCLUDE_ADB=y` in the central config. Before claiming it
works after uncommenting, port its source/build registration and required USB
libraries from the baseline, verify cross-compilation, ROMFS/ELF dependencies
and actual Android-device connection with user authorization. The pinned 4.4
user Makefile does not register ADB; ADBYBY is a different package. Current
ADB inclusion is not proven. This optional work must not enable ADB by default.

Preserve the following commented selectors in the central configuration. Do not
enable them in the default WR1200JS firmware:

```config
# CONFIG_FIRMWARE_INCLUDE_NFSC=y
# CONFIG_FIRMWARE_INCLUDE_NFSD=y
# CONFIG_FIRMWARE_INCLUDE_PARTED=y
# CONFIG_FIRMWARE_INCLUDE_SFTP=y
# CONFIG_FIRMWARE_INCLUDE_SMBD=y
# CONFIG_FIRMWARE_INCLUDE_WINS=y
```

Prepare supported build paths so a user can uncomment the required selector and
build a complete image. This includes dependencies, kernel options, ROMFS
packaging, startup/configuration integration and existing WebUI controls where
provided. Do not confuse inclusion in a build with enabling a service at boot.

Implementation and verification sequence:

1. Check effective config merging against the pinned 4.4 board template so each
   commented option remains disabled and uncommenting selects the intended code.
2. NFS client/server: verify NFSv3 kernel support, BusyBox mount support, RPC
   dependencies, nfs-utils server binaries and service configuration.
3. Parted: verify the included source, cross-build and GPT support, required
   libraries and ROMFS installation. Never test partition creation on user disks.
4. SFTP: preserve Dropbear SSH; verify the optional OpenSSH sftp-server build,
   OpenSSL 3.5 compatibility, installation path and Dropbear subsystem support.
5. SMB/WINS: verify Samba selection, smbd/nmbd packaging and WINS-only selection,
   service settings and dependencies; document the actual selected version.
6. Verify each optional build and relevant combinations using the real toolchain,
   inspect ELF dependencies and firmware size. A size failure must be reported;
   do not silently remove other required packages to make the image fit.
7. Verify runtime separately with an available device recovery route. Source
   presence and a successful compile do not establish working file services.

Initial source evidence: all six selectors already commented at project commit
b7e9d8dbc1553380ab2c4b0a275219153f223053. Pinned base c25283e9 has NFS/RPC,
Parted, OpenSSH SFTP and Samba build paths. Its recipes name nfs-utils 2.6.1,
Parted 3.6, OpenSSH 9.7p1 and Samba 3.6.25. Actual compatibility with our overlays,
compiler flags and OpenSSL 3.5 is not yet verified. USB storage and Dropbear are
already selected in the central config. No optional package was enabled here.

Final delivery must also include:

User instruction 2026-10-03 supersedes the previous end-only scheduling:
start repository creation and source preservation now, alongside the port.
Target: Andrzej1973/padavan-4.4.198, explicitly approved as Public. Preserve
history and existing configs. Provide a supported-board config catalogue,
one dispatch building multiple independent board images, and a final common
download index with per-board images/checksums/status. See
REPOSITORY-MIGRATION-PLAN.md for the implementation contract. Mi Mini must
complete its real board port before appearing as a successful firmware target.

1. A separate self-contained repository under the user's GitHub account.
2. Kernel, driver and package sources, configuration, patches, build rules,
   licenses and a manifest recording origins, revisions and checksums.
3. Required large source archives and toolchain preserved under the user's
   account, for example in Releases, with checksum verification. The final
   build must not require the original third-party repositories to remain online.
4. Build documentation, verified feature status and known limitations.
5. A complete local backup on this computer, including release assets required
   for building; a Git checkout alone is not sufficient.
6. Measure the actual backup size and report it before the user chooses a cloud
   storage destination. The user will transfer the backup to cloud storage later.
7. Verify manifest completeness and build from the preserved sources/assets.

These deliveries follow the main port. The separate Wi-Fi Hardware NAT
comparison image is also deferred until the final stage, as requested.
Repository creation, asset copying and local backup have not been performed yet.

## Wireless feature extension

User requests investigation and implementation where supported of 802.11k/v/r
roaming between access points, Band Steering and RSSI Kick. Include supported
implementation in the image but default each new function to disabled. Provide
WebUI enable, configuration and disable controls. Preserve existing wireless
settings. Do not substitute RSSI disconnection for verified FT roaming.
Validate driver, inter-AP coordination and real client behavior; FT tests require
two access points and a compatible client. These features are not implemented yet.

## Historical optional CAKE proposal — outside the active scope

User approved reconsidering CAKE and the proposed optional mode on 2026-10-02.
Include the backported sch_cake implementation and compatible tc/SQM control
where verified, disabled at runtime by default, with WebUI enable/configure/disable.
Preserve the existing configuration and acceleration when CAKE is disabled.
When enabled, prevent shaped traffic from bypassing queues through acceleration.
Verify kernel/module and tc compatibility, lifecycle cleanup and actual latency,
throughput and CPU load on WR1200JS. Do not promise 900/800 Mbps with CAKE.
Measure image size before proposing removal of any existing package. No package
removal has been approved. This approval does not imply CAKE is implemented.

## Package modernization

User requests evaluating newer package releases instead of preserving obsolete
versions unnecessarily. Prefer supported releases compatible with the board,
libc, compiler and existing settings; verify source checksums, cross-compilation,
ROMFS dependency closure and runtime behavior. Track versions explicitly.
Kernel 4.4 alone does not establish future package compatibility. Current
OpenSSL 3.5.7 port builds; evaluate newer 3.5 LTS maintenance releases next.

## Historical automatic CAKE/acceleration proposal — outside the active scope

User approved this extension in the side conversation on 2026-10-02.
Keep the existing implementation sequence. Only after CAKE/SQM and hardware
acceleration separately pass runtime checks on WR1200JS, implement and verify
an optional WebUI Auto mode as a final feature stage. Do not implement it before
those prerequisite checks establish that both modes work reliably.

Auto mode should use measured latency and traffic load to switch between
acceleration and CAKE, with hysteresis and minimum dwell times to avoid repeated
switching. Ensure accelerated traffic cannot bypass CAKE while shaping is active.
Preserve user acceleration preferences, provide manual modes and an Auto disable
control, and leave Auto disabled by default. Verify transition latency, existing
connections, failure recovery, CPU load and attainable throughput on the actual
router. Do not promise seamless transitions or 900/800 Mbps with CAKE.
This is a deferred requirement; no Auto implementation was performed here.

## Scheduler and memory-management evaluation

User requested this addition in the side conversation on 2026-10-02.
Inspect the effective Linux 3.4 baseline and Linux 4.4.198 configurations for
the scheduler, SMP/CPU topology, preemption and selected SLAB/SLUB/SLOB allocator.
Do not assume that SLUB first appeared in 4.4 or that the kernel version alone
guarantees better MIPS load balancing, lower memory overhead or higher throughput.

Compare both firmwares on the same WR1200JS with comparable settings and loads:
per-CPU utilization, interrupt/softirq distribution, latency under load,
throughput, available memory and slab usage. Include Wi-Fi and VPN workloads;
evaluate CAKE separately on the 4.4 candidate without treating it as a comparable
baseline feature unless it is also available on the baseline. Record firmware
revisions, acceleration mode and measurement conditions, and distinguish measured
results from expectations. Preserve existing router settings. Report missing
baseline measurements and avoid claiming an improvement without evidence.
These configuration checks and runtime comparisons have not been performed here.

## Priority clarification — user instruction 2026-10-03

Focus primary implementation and completion work on YOUHUA WR1200JS firmware. Continue Mi Mini only during spare time or WR1200JS build waits, when it does not delay WR1200JS completion. Mi Mini remains an accepted second-priority deliverable. All development remains in Andrzej1973/padavan-4.4.198, branch main.

## Final delivery: unchanged upstream router configurations — user instruction 2026-10-03

At the end of the project, include the original router/board configurations supplied by the pinned primary Padavan 4.4 source. Copy them byte-for-byte without adapting, normalizing, enabling packages or independently porting those boards. Record the upstream repository, exact commit and original paths; preserve applicable license notices. Present them as upstream reference configurations available for users to adapt in their own forks. Their presence does not establish compatibility with this project's added features or verified builds/runtime. Do not automatically enable them in the normal build matrix. This replaces the earlier requirement to adapt all remaining nilabsent router configurations: broader board adaptation is outside this project's required completion scope. Complete the agreed WR1200JS work, secondary Mi Mini work, source/local-backup preservation and final documentation before declaring the project complete.

## WAN port reassignment — user requirement 2026-10-03

Implement a WR1200JS WebUI option to replace a damaged physical WAN socket with one selected LAN socket. Provide a selector for the original WAN or LAN1–LAN4, Apply and Restore original WAN controls, and a clear indication that the selected socket is no longer available to the LAN. Keep the original WAN selected by default, including after a factory reset.

Reassign switch/VLAN membership and WAN link detection coherently; changing the existing `wan_src_phy` link-monitor setting alone is insufficient. Preserve IPoE/DHCP, WAN MAC, DNS and existing connection settings. Validate the actual board port mapping and IPTV/VLAN conflicts without silently resetting existing configuration. Account for firewall and hardware NAT updates and isolate the old WAN socket where supported.

Warn before applying a reassignment that the connection may be interrupted and the WAN cable must be connected to the selected socket. This requirement does not authorize changing ports on the user's current remote router.

Acceptance requires a successful firmware build plus device evidence for DHCP on the selected socket, LAN/WAN isolation, remaining LAN sockets, hardware acceleration, VLAN/IPTV compatibility where configured, reboot persistence and restoration of the original WAN assignment. Until these checks are complete, report this feature as pending, not operationally verified.

## Complete offline preservation and WSL 2 build — user requirement 2026-10-08

Preserve all project and upstream sources offline, including every selected and documented optional package, full pinned firmware/kernel/driver trees, donor trees, patches, submodules and nested downloads, generated-source prerequisites, toolchain archives and sources, build helpers, licenses, provenance and checksums. An online URL or a Git history copy alone is not an offline dependency archive.

Preserve the complete build environment as well: the required WSL 2 Linux distribution/version, host tools and offline-installable system packages or an exported prepared distribution, together with the pinned compiler and all build caches needed from a clean build directory. Inventory all recursive fetches, verify every retained dependency by checksum and report the local backup location and total size. Keep credentials and private router configuration out of public source archives.

Provide a documented WSL 2 command that builds the same firmware profile solely from the retained local files. Test with networking disabled from a clean build directory so implicit downloads cannot hide missing files. Compare the resulting image/configuration against the reference build, record any reproducibility differences and do not claim byte-identical output without a successful hash comparison. The offline kit must be transferable to another storage location and include a restore/verification procedure.

## WR1200JS completion before donor expansion — user instruction 2026-10-08

Finish the agreed YOUHUA WR1200JS Linux 4.4.198 firmware and its build/image/runtime acceptance before starting other router work or optional donor-driven migrations. Preserve the current configuration and required features; CAKE remains excluded. Required in-progress WR1200JS work remains in scope.

Retain the pinned donor audits and original reference configurations. When time and credits permit, return to the recorded candidates and choose improvements based on compatibility, measurable benefit and evidence. Auditing a donor does not authorize replacing the production toolchain, switching libc, enabling optional packages or expanding the build matrix. Do not let optional donor exploration delay delivery of the current WR1200JS firmware.

Keep verified findings, remaining checks and adoption decisions in docs/donor-audits. Source flags and successful compilation are separate from device runtime verification. Secondary Mi Mini and other accepted later work remain scheduled after the WR1200JS priority stage.


## Separate IoT Wi-Fi — user-approved WR1200JS deliverable, 2026-10-08

Add a third main use-case network alongside the existing primary and guest Wi-Fi; preserve both existing networks and their configuration. Schedule within the WR1200JS Wi-Fi/WebUI stage. The pinned ralink.c currently generates BssidNum=2 (AP plus GuestAP); a third network is not yet implemented or proven supported.

- Confirm effective MT7603E/MT7612E virtual-AP limits, interface allocation and compatibility with existing guest AP, Band Steering and optional roaming before claiming support.
- Provide a dedicated IoT WebUI section with enable switch, SSID, password, authenticated local QR, persistence and actual status. Default OFF after flashing; do not repurpose the guest network.
- Prefer 2.4 GHz, 20 MHz and WPA2-Personal/AES for compatibility. Keep WPS and Band Steering off for IoT by default. Preserve channel constraints shared by virtual APs on the same physical radio; do not imply independent RF channels.
- Wire the third BSS into driver profile generation, interface lifecycle, a separate bridge/subnet, DHCP and firewall. Block IoT access to the primary LAN and router administration by default while permitting the required DHCP/DNS and internet access.
- Provide explicit scoped access exceptions for a controller such as Home Assistant. Assess discovery/mDNS requirements separately; do not promise discovery or enable unrestricted inter-network access.
- Verify compilation, actual ROMFS inclusion, default/persistence behavior, three simultaneous SSIDs, DHCP, isolation, allowed exceptions and reconnection on the device. Test device-to-device isolation policy with the intended IoT use cases.

Status: approved planned work; runtime support unverified. No remote router changes or flashing are authorized by this planning update. WR1200JS remains the priority before secondary router work; CAKE remains excluded.

## Enhanced Connected Devices — homepage classification, 2026-10-09

User-approved deliverable: grouped connected-device list on the first page after login, categories Android/Windows/Apple/Smart TV/Unknown, evidence-based confidence and automatic refresh without manual reload. Preserve uncertainty and distinguish manufacturer from OS. Use bounded cached existing device/DHCP/radio data and browser classification; avoid continuous scans and cloud lookups. Provide visible stale/error status and automatic retry, pause polling in hidden tabs, and verify actual router overhead and connect/disconnect transitions. Full implementation contract: `ENHANCED-CONNECTED-DEVICES.md`. Planned; not yet implemented or runtime verified.

## Wi-Fi Roaming Monitor — observed steering/kick outcomes, 2026-10-09

User-approved homepage/device monitor showing actual client attachment changes between bands/APs and a bounded recent timeline. Collect authoritative associations separately from steering candidates; correlate real Band Steering/RSSI Kick action outcomes with later observed attachment without claiming causation from timing. Single-router monitoring cannot identify an external destination AP without participating AP telemetry. Read-only collection must work with steering disabled, preserve default settings, use bounded RAM history and automatic UI refresh, and avoid scans/flash churn. Full contract: `WIFI-ROAMING-MONITOR.md`. Planned; device behavior and overhead require runtime evidence.

Scheduling clarification, 2026-10-09: Enhanced Connected Devices and Wi-Fi Roaming Monitor follow current DNS/DHCP recovery integration/verification in the WR1200JS stage, before secondary-router expansion. Automatic visible-page refresh, retry/freshness indication and immediate refresh on return are mandatory; manual reload is not sufficient. Share bounded cached collection and measure CPU/RAM/network/forwarding impact before asserting low load.

## Mi Mini wireless repeater stability — 2026-10-09

User clarifies that Mi Mini will primarily extend WR1200JS over wireless, with no Ethernet uplink. Prior repeater mode lost its uplink; another mode described as MIPS was stable (exact UI mode unconfirmed, possibly WISP). Diagnose association/reassociation, AP-client coexistence, channel changes including DFS where supported, authentication and bridge/DHCP behavior before selecting a fix. Require verified 5 GHz uplink compatibility, automatic recovery after uplink interruption or either router reboot, sustained bidirectional load, and management reachability. Prefer repeater/bridge semantics where supported; explicitly document any WISP routing/NAT limitation. Do not promise throughput or seamless roaming without measurement. Keep main WR1200JS work first, lightweight Mi Mini configuration, and existing main/guest service behavior. Planned, not implemented or runtime verified.

Mi Mini UI clarification: select/scan a user-approved 5 GHz upstream SSID and configure its credentials separately from downstream AP credentials. Repeat on both 2.4 and 5 GHz where driver AP+client coexistence is verified. Provide shared downstream SSID/security/password control for both bands, with separate advanced radio controls. Shared credentials do not imply identical radio/channel settings: concurrent 5 GHz AP must respect upstream channel constraints. Never auto-join an arbitrary discovered network. Verify rescan/reconnect behavior and retain management access. Planned; driver and runtime support unverified.

Mi Mini profile clarification: derive a lightweight feature profile from WR1200JS while preserving Mi Mini-specific board/kernel/radio parameters. Wireless repeater remains primary, but retain selectable standalone router mode with WAN/DHCP/NAT/firewall and management access. Include shared dual-band Wi-Fi settings and evaluate Band Steering/RSSI Kick for its actual drivers, exposing controls only when supported and defaulting new steering features OFF. Preserve prior exclusions of heavy storage/download/media packages. Do not copy MT7621-only settings onto Mi Mini or assume matching radio capability. Validate image size and both repeater and router modes before marking the secondary profile supported.

Mi Mini driver research approved: after completing the primary WR1200JS stage, investigate OpenWrt sources for a suitable MT7620 integrated 2.4 GHz driver, including confirming whether the appropriate source is mt76 or another implementation. Evaluate Linux 4.4 compatibility, mac80211/cfg80211/backports dependencies, EEPROM/calibration and firmware requirements, AP-client coexistence and integration with Padavan configuration, lifecycle and WebUI. Do not assume a driver name establishes MT7620 support or that copying source creates a working port. Preserve lightweight profile and verify both radios, wireless repeater recovery and optional router mode before claiming support.

## Confirmed stage order — 2026-10-09

The user confirms that all preceding Mi Mini configuration, dependency, repeater stability, shared Wi-Fi settings and driver-research requirements belong to the project goal. Complete the primary YOUHUA WR1200JS firmware first, including its agreed acceptance checks, before starting Mi Mini implementation or driver migration. Mi Mini work is deferred until that stage is complete; build waits alone do not open the secondary stage. Retain the dependency review and driver research contract above. The spoken source/driver names “OpenVR” and “Nvidia” are unconfirmed; verify the intended source and actual MT7620 hardware compatibility before importing any driver.

## Runtime findings and corrective work — user confirmation 2026-10-11

This section updates the immediate WR1200JS sequence after the actual flashed
firmware test. The primary acceptance criterion is stable operation with
preserved internet and router management access. The earlier numbered sequence
does not require finishing IoT before fixing the observed DNS/access failures.

Evidence: [read-only runtime collection and DNS recovery](runtime/WR1200JS-2026-10-11.md).
The owner's screenshots additionally show mixed Ukrainian/English labels, a
Chinese navigation item and unclear service switches. Screenshots and raw logs
remain private; publish only sanitized findings. A green build is not device
acceptance, and the current test image is not yet qualified as stable.

Complete and record these checks:

1. **DNS and access recovery first.** Fix Stubby's missing lifecycle locking
   dependency in the image and verify actual start/stop/restart. Restore usable
   DoT/DoH provider lists, time bootstrap and functional Apply/disable controls.
   Detect legacy custom dnsmasq loopback forwarding that survives service
   toggles; provide a backed-up, explicit migration rather than overwriting
   custom rules. Keep DoT/DoH disabled during recovery. Verify ordinary DNS,
   optional encrypted DNS, WAN connectivity and AmneziaWG management access
   after restart. Any ordinary-DNS fallback must be an explicit user choice.
2. **Wi-Fi HNAT and driver diagnostics.** Investigate module-level wireless
   external-device registration in addition to RC/driver guards, record actual
   acceleration mode and prove Wi-Fi offload is disabled while retaining
   supported wired acceleration. Examine repeated HNAT drop and ADDBA messages;
   neither message alone proves a hang. Verify both radios under sustained
   traffic and reconnects, with logs and continued management access.
3. **ZRAM.** Repair the mismatch between enabled settings and absent active swap.
   Verify block-device initialization, actual /proc/swaps state, status display,
   enable/disable lifecycle and reboot persistence; report failure visibly.
4. **Coherent service WebUI.** Audit all enabled-service menu routes and pages.
   Complete Ukrainian and Russian translations, preserve English, remove
   unintended Chinese labels from the active localized UI, and group DNS, VPN,
   router access and system services clearly. Provide readable enabled/disabled
   labels separately from actual running/stopped/error status. Verify Apply,
   validation, persistence and actual daemon lifecycle for each affected page.
   Verify safe-session settings/storage backup, restore and flash-save controls;
   preserve authentication and login_safe restrictions. Verify AmneziaWG is
   identifiable and configurable separately from ordinary WireGuard.
5. **Complete IoT as an accepted deliverable.** Carry forward
   [the IoT implementation contract](IOT-WIFI-IMPLEMENTATION-CONTRACT.md):
   a separate third SSID, preferably 2.4 GHz, default OFF, with SSID/password,
   local QR, enable/disable and actual status; preserve main and guest networks.
   Verify driver/BSS lifecycle, isolated bridge/subnet, DHCP/DNS, WAN access,
   administration/LAN isolation and scoped controller exceptions. Exercise
   shutdown/recovery and simultaneous main/guest/IoT operation. The recovery
   test profile may continue to exclude IoT until these checks pass.
6. **Wireless usability and acceptance.** Finish shared dual-band configuration,
   QR, Band Steering and RSSI Kick, default new features OFF, and automatically
   refreshed connected-device/roaming monitoring. Verify observed behavior and
   bounded CPU/RAM use. Evaluate actual 802.11k/v/r support without treating
   source flags as proof of seamless roaming.
7. **Next test delivery.** Include verified corrections and translations, record
   remaining limitations, and deliver firmware plus its config. Test boot,
   WAN/LAN, DNS, Wi-Fi, VPN access, service controls and settings persistence
   before calling the image stable. Keep unfinished items open.

Continue remaining accepted WR1200JS features afterward, then Mi Mini, and
finally local databases and the offline WSL 2 project. CAKE remains excluded.

## Nilabsent upstream update integration — final-stage requirement, 2026-10-11

Use [nilabsent/padavan-ng](https://github.com/nilabsent/padavan-ng) as the
explicit donor for the complete WireGuard/AmneziaWG WebUI, client/server
configuration, import/export, local QR and translations. Preserve existing
tunnel settings during adaptation and verify each control against the 4.4 port.

After the main firmware is stable, implement automated upstream discovery:
compare the last recorded donor SHA with current upstream commits, retain
source links and changes locally, and prepare selected compatible updates in
a separate branch/PR with provenance and checks. Define an allowlist of ported
components; do not automatically merge the 3.4 kernel, drivers, toolchain or
unrelated files into the 4.4 tree. Resolve patch conflicts and verify build,
image and affected runtime behavior before accepting an update.

Subsequent firmware builds consume the accepted, pinned donor revision from
our repository/manifest. They must not silently build arbitrary upstream HEAD.
Provide an explicit optional candidate-update build and rollback to the last
accepted revision. Record imported donor changes and hashes, retain licenses,
and include accepted donor sources in the final offline archive. An upstream
outage must not prevent building a previously preserved version.

Latest inspected donor commits on 2026-10-11:
- [14e4fac1, 2026-10-04](https://github.com/nilabsent/padavan-ng/commit/14e4fac1ca24ab15278378d3e994db82fc9bcdda):
  changes the imported AmneziaWG default i1 template for ProtonVPN compatibility
  in trunk/user/wireguard/amneziawg.json. Candidate for the WebUI/import port;
  not yet verified or adopted in this firmware.
- [d2c58462, 2026-09-19](https://github.com/nilabsent/padavan-ng/commit/d2c5846299949c57a4e867284069900b561dd2a4):
  updates nfqws2 to 1.0.5.2 and corrects default interface detection in zapret.sh.
  Retain for the previously deferred package stage.
- [8be99123, 2026-09-06](https://github.com/nilabsent/padavan-ng/commit/8be99123a72880f67cd65e98dafea5f1dce8cc3e):
  updates AmneziaWG to 3.1.20260906. Runtime logs already report that version
  on WR1200JS; this does not prove complete WebUI parity.

This update mechanism is planned for the end of the project; it is not active.

## Screenshot-specific WebUI defects — user confirmation 2026-10-11

Retain these observations alongside the runtime report above. They are open
acceptance requirements, not completed fixes. Do not publish the original
screenshots, logs or private router settings.

- **ZeroTier:** the actual page mixes Ukrainian, English and Chinese. Translate
  all labels, list choices, help text and errors for Ukrainian/Russian while
  retaining English. Replace the instruction to manually reload status with
  bounded automatic refresh, freshness/error indication and retry. Reconcile
  router-access, LAN-access and legacy NAT controls against the actual firewall
  implementation so their interaction is explicit. Group Moon and routes under
  advanced controls. Verify Apply, daemon lifecycle, membership preservation,
  permissions and actual network connectivity. The screenshot only establishes
  a disabled/stopped UI state, not working connectivity.
- **WireGuard/AmneziaWG:** the installed page is only a simplified WireGuard
  client form. Full Nilabsent interface parity has NOT been ported. Carry
  forward the donor requirement: client/server management, AmneziaWG parameters,
  import/export, adding/removing peers, authenticated local QR, real status,
  startup and translations. Verify kernel/userspace compatibility and preserve
  the existing remote tunnel. An operational tunnel does not establish WebUI
  completeness; applying an empty legacy form must not erase unrelated settings.
- **Proxy services:** the screenshot shows Chinese proxy/DNS settings consistent
  with the Shadowsocks page; confirm the actual route and compiled components
  before porting. Translate labels, help and every option value. Inspect suitable
  Nilabsent implementations and verify proxy lifecycle, DNS routing, selected
  modes and clean restoration of ordinary DNS/internet when disabled. Keep the
  recovery profile's proxy services disabled until verified.
- **General service page:** mixed labels and ambiguous switches require readable
  enabled/disabled state plus separately reported running/stopped/error state.
  Every Apply control must be tested for validation, actual changes and
  persistence. Audit navigation and safe settings/storage backup/restore controls.
- **Wireless evidence:** screenshots repeat ADDBA response-policy warnings and
  HNAT drop messages. Correlate them with association/reconnect events, traffic
  and acceleration state; do not equate a warning with a proven kthread hang.
  Retain the runtime Wi-Fi HNAT verification requirement.
- **IoT remains required:** the DNS/access recovery work does not remove the
  separate IoT SSID, isolation, DHCP/DNS, local QR, WebUI lifecycle and
  simultaneous main/guest/IoT device acceptance already specified above.

Complete these in the WR1200JS stage before Mi Mini and offline preservation.
Source presence, visible buttons and successful compilation are not substitutes
for working device behavior. Main acceptance remains stability and preserved
management/internet access.

## Shared Wi-Fi asymmetric Apply defect — device report 2026-10-11

The owner reports that shared Wi-Fi settings propagate to both bands only when
applied from the 2.4 GHz page. Applying from the 5 GHz page does not update both
bands. Treat this as an open device-reported defect; its exact cause has not
yet been isolated.

When shared mode is enabled, SSID, password and security changes must update
both bands consistently from either page. Channel and channel width remain
per-radio settings. Verify the form submission, server-side validation/NVRAM
mapping and both radio restart paths. Do not merely mirror the displayed form.

Acceptance: test 2.4-to-5 and 5-to-2.4 changes, saved values and effective driver
settings, reopening both pages, restart persistence and separate mode. Preserve
guest/IoT separation and management access. Temporary workaround: apply shared
parameters from 2.4 GHz and verify the 5 GHz result. Screenshot log shows Band
Steering starting; it does not establish successful client steering.

## Connected-device map and refresh revision — user instruction 2026-10-11

Use the supplied Funbox screenshot as a layout reference: provide Map/List views,
grouping devices by main Wi-Fi (2.4/5 GHz), guest Wi-Fi, IoT Wi-Fi and wired LAN.
Show names, IP, connection location and available signal/status evidence with
the previously accepted classification/confidence. Display a physical LAN port
or external AP only when authoritative telemetry identifies it; otherwise show
unknown instead of guessing. USB peripherals, if presented, are a separate
section and are not assumed to be network clients.

Fetch current data on page entry and return to the visible page, add an explicit
Refresh button and last-update/error/stale indication. The user relaxes the
previous five-second refresh requirement: use a provisional 30-second visible
page interval, adjustable after overhead measurements. Pause polling in hidden
tabs, prevent overlapping requests and share bounded server-side snapshots.
Manual refresh is required alongside less frequent automatic refresh.
This supersedes earlier statements that manual refresh was insufficient as a
control or that five-second polling was mandatory; timely initial display
and honest freshness remain required.

Preserve the working stock client list while fixing source_unavailable.
Verify connect/disconnect and movement between actual attachment groups,
manual refresh, first entry, hidden-tab behavior and CPU/RAM overhead on the
router. The screenshot is an intended layout, not evidence of implemented
topology or working collection.

## Unified settings navigation — user approval 2026-10-11

The owner approves the preceding Wi-Fi layout proposal and requests a central
network settings page with related tabs, using the Funbox screenshots as layout
references. Record requirements without publishing screenshots containing Wi-Fi
credentials or QR codes.

- Provide one Wi-Fi overview listing primary, guest and IoT networks with
  explicit enable/state and configuration links. In shared mode use one form
  for 2.4/5 GHz SSID, password, security and SSID visibility plus local QR.
  In separate mode provide independent forms for each band.
- Keep advanced per-radio channel, width and transmit-power settings under
  Advanced. Preserve required underlying controls. Shared credentials do not
  automatically enable Band Steering; give it a separate control.
- Provide a central Network section with related tabs such as LAN/DHCP,
  NAT/port forwarding, DNS, UPnP, dynamic DNS, DMZ and time/NTP. Final grouping
  must follow the actual supported services and existing permission boundaries;
  avoid duplicate inconsistent editors. VPN/service pages may link from this
  overview while retaining their distinct settings and validation.
- DHCP view should combine DHCP configuration, static lease management and
  dynamic leases, with clear device names, addresses and save/apply behavior.
- Maintain coherent theme and Ukrainian/Russian/English localization across
  tabs, identify unsaved changes, and distinguish Save/Apply and service status.
  Reuse proven ported backends and existing authorization instead of replacing
  networking logic merely to change navigation.
- Verify navigation, direct routes, conditional service inclusion, validation,
  persistence and actual device behavior. The screenshot is a design reference,
  not evidence of implementation. This remains WR1200JS work and must preserve
  the existing stable-management-access priority.

## Model capability filtering and function help — user approval 2026-10-11

Gradually audit configuration selectors, compiled components and WebUI controls
against each board's actual hardware, driver version and integrated userspace
implementation. Create a shared per-model capability manifest used by build
selection, server-side validation and WebUI visibility; do not filter solely
by model name or hide a control while leaving unsupported settings applicable.

Distinguish unsupported, supported-but-runtime-unverified, and verified
capabilities, with source/revision evidence. Hide confirmed unsupported controls
and exclude their board-specific build features/dependencies where independent
of required components. Do not remove shared code needed by other boards.
For supported features, include the necessary implementation and expose suitable
controls, subject to existing optional package selectors and runtime defaults.
Support does not imply automatic runtime enablement: preserve WPS/IoT/steering
default-off and documented optional commented packages. Unknown support must
remain explicit rather than being claimed as functional or silently discarded.

Prioritize WR1200JS radio UI: validate advertised MU-MIMO, channel widths,
beamforming and 802.11k/v/r against its MT7603E/MT7612E drivers. A generic menu
option or chipset marketing capability alone does not prove that this image
implements it. Verify effective settings after Apply and retain management access.

For every exposed function provide localized EN/UK/RU help explaining purpose,
valid values/units, dependencies, default, expected tradeoffs and any restart
or connectivity interruption. Explain unsupported/experimental status where
applicable; use concise basic help with expandable technical details. Verify
capability-filtered pages, backend rejection of unsupported values, optional
feature combinations and actual board behavior.

Also replace the inherited firmware version suffix with project build identity
(number plus short commit SHA) while preserving accurate kernel/version details
and upstream attribution in the credits/licenses. Ensure UI, image naming and
diagnostic reports identify the same build. Implementation remains pending.
