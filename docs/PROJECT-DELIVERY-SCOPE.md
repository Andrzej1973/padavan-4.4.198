# WR1200JS project delivery requirements

User UI palette request, 2026-10-17: enabled service toggle controls should
be green; disabled controls retain neutral grey. Preserve ON/OFF text and
loading/disabled feedback. Toggle color represents the selected setting;
actual service health remains a separate observed indicator. Apply through
the shared iToggle stylesheet for consistent controls across pages.

User UI clarification, 2026-10-19: keep mode 1 visibly marked as compatible,
mode 2 as LAN only, and permit the user to switch modes manually. Factory
default remains mode 2. Mode 1 is an explicit Wi-Fi offload trial; if Wi-Fi
stability worsens or router load rises, return to mode 2. The firmware must not
claim that mode 1 works until throughput, stability, and system load are
measured on the router. Do not infer acceleration from a saved setting; the
live WR1200JS read showed `hw_nat_mode=2` and a loaded `hw_nat` module, while
the kernel log reports the requested WAN↔LAN offload path.

User-approved extension, 2026-10-02.

Primary objective remains the Linux 4.4.198 port of YOUHUA WR1200JS,
preserving the user's configuration and required features, excluding CAKE
under the active thread objective reaffirmed on 2026-10-08. Earlier CAKE
proposals below are retained as history and are outside the current delivery.
Compilation alone does not establish a successful device port.

User instruction, 2026-10-14: consolidate and adopt the best suitable solutions
from previously reviewed donors. See [donor adoption plan](DONOR-ADOPTION-PLAN.md)
for decisions, integration order and evidence requirements. Prefer proven
target-compatible behavior over version numbers; existing exclusions and
explicitly deferred stages remain applicable.

## VPN scope replacement — owner instruction 2026-10-16

This supersedes earlier preservation/deferred-development requirements for these
protocols: remove PPTP, L2TP without IPsec, EoIP and OpenVPN from the WR1200JS
firmware and WebUI. Remove their private dependencies only after checking other
consumers. Preserve PPP/PPPoE for provider uplinks and shared libraries needed by
remaining services. OpenVPN must have no selector in the user profile; prevent
inheritance from the donor template. StrongSwan remains commented/excluded;
its development is cancelled rather than deferred to the final stage.

Retain configurable WireGuard and AmneziaWG in WebUI if both can be supported
correctly. Inspect the existing shared type=3/renamed-AmneziaWG implementation:
two compiled modules or labels do not prove independent working tunnels. If both
cannot be supported, retain AmneziaWG as the owner's authorized fallback.
ZeroTier is unaffected. Owner confirmation 2026-10-16: retain both enabled
SSREDIR and SSLOCAL selectors (mapped to the shared Shadowsocks package).
Package inclusion does not authorize enabling a live proxy or adding credentials.
Expose SSSERVER separately as a commented optional selector; retain client/server
role explanations in the generated guide. Verify both client binaries in ROMFS
and absence of ss-server when the server selector is disabled.
Keep old saved credentials/configuration files intact;
this change does not authorize changing or disconnecting the live router.
Acceptance: effective configuration plus absent ROMFS binaries/plugins/private
libraries, disabled kernel-only dependencies where unused, rejected legacy
backend actions, no misleading UI choices, updated model guide and target
BusyBox checks; actual retained tunnel routing requires device verification.

## Distinct WG/AWG tunnel profiles — owner request 2026-10-16

When an AmneziaWG tunnel already exists, creating a WireGuard tunnel must
give the new tunnel its own visible name/number (for example AWG1, WG1, WG2)
instead of silently replacing the existing profile. Preserve existing saved
settings and tunnel identity. Each profile needs its own protocol, name,
configuration, observed status, export/QR and scoped lifecycle actions.
Owner confirmed: profiles must run independently and simultaneously. Creating,
editing or stopping one must preserve other tunnels and management access.
Stored alternatives with only one active profile do not satisfy this request.

Confirmed handover scenario: keep the current AWG profile carrying remote
management, create and connect an independent WG profile, verify a new
management connection through WG, then explicitly stop AWG and finally delete
its profile. This is remote setup through AWG, not a requirement to nest the
WG data path inside AWG. WG endpoint routing and DNS dependencies must remain
functional after AWG is stopped. Stopping and deleting are distinct actions;
no automatic source-profile removal is authorized. The owner reports about
300 Mbit/s with WireGuard on this router's old 3.4 firmware versus about
150 Mbit/s on the current AWG connection; retain this as an owner-reported
benchmark reference, not a verified limit or performance promise for 4.4.

Historical baseline before independent-profile integration: one shared client role (wg0) and one shared server
role (wg1), not a multi-profile manager. The client additionally hard-codes
routing table 51, fwmark 51820, rule preferences 5181/5182, shared ipsets,
watchdog lock, network-list files and post-script. Independent concurrent
profiles require ownership and collision handling for these resources, DNS,
routes and firewall reconstruction as well as distinct interface names.
Renaming labels alone does not satisfy the request. Verify persistence,
per-profile QR contents and that editing/stopping one profile preserves the
other tunnel and management access before claiming support.

Implementation checkpoint, 2026-10-18: the independent manager and scoped
lifecycle are implemented alongside the retained legacy roles. WebUI supports
save-only creation, Up/Down/Delete, private export/QR, bounded pagination,
manual list refresh and explicit interface observations that expire to unknown.
Browser editing is now implemented with authenticated private export,
revision-bound POST and stopped-profile validation. Downloaded firmware #433
independently confirms the form, compiled endpoint, EN/UK/RU text and guide;
see evidence/WR1200JS-BUILD433.md. Build #441 passed the selected observer image
gates; its TRX page/handler markers and BusyBox identity were independently
checked in [build evidence](evidence/WR1200JS-BUILD441.md). That does not execute
the per-ID mutation lock path; MIPS concurrency/locking behavior remains to be
verified. Firmware #425 includes storage-directory permission repair, and #428
passed the shipped MIPS archive/restore/readback fixture. Physical concurrent
tunnels, recovery, reboot persistence and the WG-to-AWG management handover
remain unaccepted. See EXECUTION-ROLE.md for the current build/test checkpoint.
Preserve all delivery requirements below; these component results do not finish
the port.

## Delivery order — user confirmation 2026-10-10

1. Finish YOUHUA WR1200JS first: complete the accepted firmware and WebUI work, verify the target build and image, then verify device behavior with the user. Compilation alone is insufficient. Preserve the central configuration and keep CAKE excluded.
2. Immediately after WR1200JS, complete Xiaomi Mi Mini with the reduced profile and stable 5 GHz wireless uplink/repeater requirements already recorded below.
3. After both router stages, finish the local source/reference databases and complete offline preservation and the verified WSL 2 offline build project.

Defer offline preservation and donor/database expansion until stage 3. Retain existing backups. This changes task order; it does not remove any accepted deliverable. Report concrete completed steps and maintain a short working checkpoint.

## WR1200JS execution sequence — user approval 2026-10-10

Complete these steps in order, carrying all existing acceptance requirements forward:

1. IoT Wi-Fi: finish activation/shutdown and recovery; integrate the third BSS, owned bridge, DHCP/DNS, isolation/firewall and scoped WAN NAT; add authenticated enable/SSID/credentials/subnet/status/local QR controls; verify simultaneous main/guest/IoT operation and isolation.
2. Wi-Fi and roaming: finish shared 2.4/5 GHz controls and QR, Band Steering, RSSI Kick and automatically refreshed monitoring. Establish actual supported 802.11k/v/r behavior; never equate compilation or RSSI disconnection with FT roaming.
3. Service WebUI coverage: complete lifecycle, validation, persistence, status and navigation for accepted enabled services, including USB/IP and diagnostics plus existing ZeroTier/VPN integration. Per the 2026-10-16 scope replacement, remove PPTP, standalone L2TP, EoIP and OpenVPN from WR1200JS firmware/WebUI; StrongSwan is cancelled/excluded, not pending work.
4. Optional HTOP and MTR diagnostics: keep both out of the required WR1200JS image. Their commented selectors may be enabled individually for a later diagnostic build, subject to the checks below. This is not a release gate.
5. WAN socket reassignment: finish authenticated selection and verify selected WAN/remaining LAN isolation and persistence.
6. Final configuration/image audit: preserve required features, verify optional commented selectors separately and keep WPS optional verification last. Deliver one user download ZIP containing firmware and its config. CAKE stays excluded.
7. Recoverable device acceptance: verify Linux 4.4.198 boot, WAN/LAN, both Wi-Fi bands under load, restored AmneziaWG, settings/services and restart persistence. User agreement on task order is not authorization to flash or disrupt the remote router.

### Optional HTOP and MTR diagnostics — owner decision 2026-10-26

HTOP and MTR are not required for router operation or Padavan Modern status
graphs. The standard WR1200JS image excludes them. Keep independent commented
`CONFIG_FIRMWARE_INCLUDE_HTOP=y` and `CONFIG_FIRMWARE_INCLUDE_MTR=y` selectors
in `configs.build/wr1200js.config` so an operator can request either package
without copying recipes into each board profile. Do not enable them by default
on WR1200JS or assume that another router has the same image headroom.

The pinned Padavan source has `trunk/user/htop` (3.3.0), `trunk/user/mtr`
(0.95) and `trunk/libs/libncurses` (6.5). Its user Makefile selects each
package with the corresponding selector, and its libs Makefile selects
ncurses for either one. A commented selector alone does not prove successful
target compilation or a working executable. If an optional build is requested,
check the effective config, MIPS build, ROMFS binaries and libraries, loader
dependencies, compressed image delta and flash headroom before flashing.
Review `mtr-packet` privileges and raw-socket behavior; neither tool needs a
boot service, continuous polling or a WebUI endpoint. Device operation remains
unverified until separately tested. Build #574 had both options disabled; no
target sizes or measured image delta are available yet.

## Preserve and port existing services — user instruction 2026-10-11

## Mandatory target BusyBox compatibility audit — user instruction 2026-10-16

Owner decision, 2026-10-28: retain the project's BusyBox 1.24.2 for the
WR1200JS delivery. Do not upgrade BusyBox merely to obtain newer applets.
The available `hexdump` already supports the observed PCI read command;
`od` is a separate optional applet question. This version decision does not
waive the exact-image command, dependency and service audit below. Revisit
the version only for a demonstrated compatibility/security need with its
own target regression evidence.

Audit every firmware service and every connected script, process and lifecycle
path against the exact BusyBox built for the target image. This is a delivery
requirement, not limited to the recently changed USB/IP/Stubby/ZeroTier code.
Record results per service in the existing service audit documents; retain
unverified failures as open work instead of declaring global compatibility.

Required coverage:

- Inventory all enabled services, boot/shutdown/restart/Apply handlers, scheduled
  jobs, hotplug hooks, firewall/DNS/network hooks, monitors, status collectors,
  backup/restore and storage scripts. Include optional/commented services when
  their supported build selectors are evaluated; do not silently enable them.
- Identify the exact image BusyBox version/source revision, effective .config,
  binary SHA256, installed applet links and runtime loader/library dependencies.
  Associate evidence with the firmware build/commit and router model.
- Map each command to its actual provider: shell builtin, BusyBox applet or
  standalone binary. Verify command detection, shell syntax/expansion, options,
  output formats, exit statuses, pipelines, redirection and error handling.
  Applet presence alone is insufficient: selected build features may change
  supported options, as with minimal od versus hexdump and the earlier
  command -v check in the router shell.
- Check process launch/daemonization, PID ownership, fork/exec/wait/reaping,
  signals, timeout handling, inherited descriptors, flock compatibility,
  concurrent lifecycle/settings operations and cleanup after interrupted or
  failed actions. Status must distinguish configured intent, observations,
  missing/unavailable data and actual service/connectivity acceptance.
- Exercise dependent chains: WAN/LAN/VLAN and acceleration, firewall rebuilds,
  DNS/time/certificates and encrypted DNS startup/failure, VPN routing, USB and
  storage/mount/swap handling, persistence and recovery. Verify safe defaults,
  disabled states and preservation of existing settings and management access.
- Run script/CLI fixtures with the image's own BusyBox/shell and required target
  libraries under a suitable target emulator where possible. Mock destructive
  or hardware operations. Host Bash/GNU utilities and native C mocks remain
  useful supplementary checks, not evidence of target BusyBox compatibility.
- Verify the installed ROMFS paths and repeat applicable supervised runtime
  checks on the actual router. Hardware-dependent behavior, full interaction
  chains, reboot persistence and sustained stability remain unverified until
  physically observed. No audit instruction authorizes flashing, rebooting or
  disrupting the remote router without the existing separate agreement.

For each finding record the dependent service/path, exact command/options,
target configuration evidence, reproducer, fix and verification result. Review
the shared dependencies again when BusyBox configuration/version changes, and
run relevant regression gates in normal firmware CI. Do not solve missing
applets by unreviewed global feature switches or silently changing user settings.



### Follow-up: target BusyBox hexdump and version evidence — assigned to Sol

The WR1200JS live read-only PCI-config collection succeeded with the router's
BusyBox applet using `busybox hexdump -C -n 4096`; standalone `od` is absent.
This proves only that this command works on the currently running router image.
It does not identify the BusyBox version or prove that the corresponding
firmware build contains the same applet/options.

At the next suitable BusyBox/image audit step, Sol should: (1) identify the
exact BusyBox version and source revision used by the current WR1200JS firmware
build, (2) inspect its effective `.config`, ROMFS binary hash, applet links and
`hexdump` options, (3) verify whether `od` is omitted by configuration or is
otherwise unavailable, and (4) compare those image facts with the live router
output. Confirm whether the read-only helper's PCI dump command is portable to
that exact image and record a reproducible command/result. Keep the helper
allowlisted and read-only; do not add arbitrary remote command execution or
change router state. Do not reorder current delivery work: this is part of the
existing mandatory target BusyBox compatibility audit and must not displace the
open IoT lifecycle gate.

### Existing-service preservation contract

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
resolver-list compatibility are proven. Tor and Zapret2 remain Stage 2
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

Stage 2, after the WR1200JS firmware is ready: port CONFIG_FIRMWARE_INCLUDE_TOR, CONFIG_FIRMWARE_INCLUDE_TOR_GEOIP, CONFIG_FIRMWARE_INCLUDE_TOR_GEOIPV6 and CONFIG_FIRMWARE_INCLUDE_ZAPRET2. Keep these documented but disabled in the stage-1 build config. Also migrate the remaining nilabsent router configurations to this firmware base, checking each board's hardware requirements individually.

Updated user decision 2026-10-24: implement only Zapret2. The old
`CONFIG_FIRMWARE_INCLUDE_ZAPRET` selector (called Zapret 1 by the user) is
removed from board configs and is out of scope. When Stage 2 begins, enable
the Zapret2 selector in the WR1200JS build configuration and include its
actual kernel and userspace dependencies, service lifecycle, configuration,
strategy data and WebUI in the firmware. Verify the resulting image contents,
dependency closure and compressed image size against the flash limit. Do not
turn on only the selectors or claim support from a successful build alone.

Zapret2 preparation (2026-10-24): a pinned, complete upstream source snapshot,
per-file hashes, license and component/dependency inventory are recorded in
`third_party/bol-van/zapret2/`, `third_party/bol-van/zapret2-source-manifest.json`
and `docs/ZAPRET2-SOURCE-BASE.md`. This preserves sources for Stage 2; no
Padavan build rule, selector, ROMFS content or router service is enabled yet.

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

Project-wide rule, 2026-10-24: every router accepted into this project must include a real IoT network as a standard firmware capability alongside primary and guest Wi-Fi. Board/build configuration must not offer an option to omit IoT. This applies to WR1200JS, Mi Mini and every later board profile. A board is not release-ready until its own driver, network isolation, defaults, WebUI, image and device tests establish that capability. An unsupported board must remain pending rather than ship a cosmetic IoT control or silently omit the feature. The user-facing runtime enable switch is distinct from a build-time omission and remains available. Provisioning must never advertise an unprotected IoT SSID; enabling it by factory default requires safe distinct credentials and working isolation. The currently IoT-excluded test image is transitional and does not meet this release rule.

- Confirm effective MT7603E/MT7612E virtual-AP limits, interface allocation and compatibility with existing guest AP, Band Steering and optional roaming before claiming support.
- Provide a dedicated IoT WebUI section with enable switch, SSID, password, authenticated local QR, persistence and actual status. A released board must provision IoT by default; activate it at factory defaults only after distinct safe credentials and isolation are verified. During development, keep it OFF rather than broadcast an insecure network. Do not repurpose the guest network.
- Prefer 2.4 GHz, 20 MHz and WPA2-Personal/AES for compatibility. Keep WPS and Band Steering off for IoT by default. Preserve channel constraints shared by virtual APs on the same physical radio; do not imply independent RF channels.
- Wire the third BSS into driver profile generation, interface lifecycle, a separate bridge/subnet, DHCP and firewall. Block IoT access to the primary LAN and router administration by default while permitting the required DHCP/DNS and internet access.
- Provide explicit scoped access exceptions for a controller such as Home Assistant. Assess discovery/mDNS requirements separately; do not promise discovery or enable unrestricted inter-network access.
- Verify compilation, actual ROMFS inclusion, default/persistence behavior, three simultaneous SSIDs, DHCP, isolation, allowed exceptions and reconnection on the device. Test device-to-device isolation policy with the intended IoT use cases.

Status: approved planned work; runtime support unverified. No remote router changes or flashing are authorized by this planning update. WR1200JS remains the priority before secondary router work; CAKE remains excluded.

Wi-Fi bridge help localization follow-up, 2026-10-18: the 5 GHz Bridge page
shows the inherited `AP_Relay` link and `AP_Relay_1` explanation in English
under the Ukrainian locale. The inherited-dictionary preparation now supplies
English, Ukrainian and Russian values for both keys and validates their final
image values. This is a source correction; it still needs a new image build and
browser review. See [bridge-help localization evidence](evidence/WR1200JS-BRIDGE-HELP-LOCALIZATION-2026-10-18.md).

Advanced Wi-Fi localization follow-up, 2026-10-18: the 5 GHz advanced page
shows 802.11KV and 802.11R labels without Ukrainian dictionary entries. The
inherited-dictionary transform now supplies EN/UK/RU values for both. Existing
source entries also localize AMSDU and MU-MIMO help via `help_wl.js` dictionary
references. TXBF was removed from the WR1200JS page because the configured
driver disables it; see the capability result below. New image and router-
browser verification of the retained help remain pending; see
[advanced Wi-Fi help evidence](evidence/WR1200JS-WIFI-ADVANCED-HELP-LOCALIZATION-2026-10-18.md).

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
   external-device registration in addition to RC/driver guards. Keep factory
   mode 2 (LAN only), allow a manual mode 1 compatibility trial, and provide
   clear guidance to return to mode 2 if Wi-Fi stability or router load worsens.
   Measure actual acceleration, throughput, load, and both radios under
   sustained traffic and reconnects, with logs and continued management access.
   Examine repeated HNAT drop and ADDBA messages; neither alone proves a hang.
3. **ZRAM.** Repair the mismatch between enabled settings and absent active swap.
   Verify block-device initialization, actual /proc/swaps state, status display,
   enable/disable lifecycle and reboot persistence; report failure visibly.
   Read-only SSH on 2026-10-18 now confirms `zram_enable=1`, initialized
   `/dev/zram0`, and 30,912 KiB active swap. Enable/disable and reboot
   persistence remain unverified; see
   [ZRAM runtime check](evidence/WR1200JS-ZRAM-RUNTIME-2026-10-18.md).
4. **Coherent service WebUI.** Audit all enabled-service menu routes and pages.
   Complete Ukrainian and Russian translations, preserve English, remove
   unintended Chinese labels from the active localized UI, and group DNS, VPN,
   router access and system services clearly. Provide readable enabled/disabled
   labels separately from actual running/stopped/error status. Verify Apply,
   validation, persistence and actual daemon lifecycle for each affected page.
   Verify safe-session settings/storage backup, restore and flash-save controls;
   preserve authentication and login_safe restrictions. Verify AmneziaWG is
   identifiable and configurable separately from ordinary WireGuard.
   Progress 2026-10-14: the ZeroTier page is translated for EN/UK/RU in source
   and its manual reload is replaced by a bounded refresh; see
   [ZeroTier page localization](evidence/ZEROTIER-PAGE-LOCALIZATION-2026-10-14.md).
   Screenshot report 2026-10-18 confirms Chinese text is still visible on the
   Shadowsocks page. The source localization step now maps main client settings,
   node subscription controls, static node-editor fields, process-limit labels
   and rule headings to EN/UK/RU keys. This step is wired into source
   preparation. The source transform now covers the Chinese visible labels
   and messages inventoried in the saved Shadowsocks page, including dynamic
   node feedback, import prompts/results, editor actions and help text. A
   final-image gate now checks all Shadowsocks dictionary values and rejects
   remaining CJK page text; the transform and gate passed on an isolated
   fixture based on build #410, but no new final image has run through it.
   The cited checkpoint's remaining-Chinese note is historical and has been
   rechecked against the available build #410 ROMFS: its `EN.dict`, `UK.dict`
   and `RU.dict` contain no CJK characters. SmartDNS and SQM are also disabled
   in the current WR1200JS profile, so their pages are not part of the active
   localized UI. Do not count those inactive pages as current defects; if either
   selector is enabled later, add page-specific localization and image checks.
   The Shadowsocks transform still needs a new final-image run and browser
   review. See [localization checkpoint](evidence/SHADOWSOCKS-LOCALIZATION-2026-10-18.md).
   A 2026-10-19 in-memory regression test for inherited EN/UK/RU dictionaries
   exposed and fixed a bug that removed existing help keys when replacing
   stale translations. The local fixture passes; a new final image and browser
   review remain pending. See
   [localized help test evidence](evidence/WR1200JS-LOCALIZED-INHERITED-HELP-TEST-2026-10-19.md).
   Screenshot follow-up 2026-10-18: Cron, Watchdog and Network discovery
   plus Telnet links now target their existing service-control anchors; the
   source verifier requires those routes. Read-only SSH on 2026-10-18 confirmed
   the currently served page still has all four old unanchored links while the
   targets exist; exact build number is unavailable from device NVRAM. The
   source correction is not installed. Final-ROMFS and browser behavior remain
   unverified. The same SSH sample found KMS/SSH processes present and disabled
   iPerf3/Cron/LLTD/ASUS Discovery processes absent, matching their saved flags.
   `watchdog_cpu=1` while `rt_timer_wdg` is absent; the separate `watchdog`
   process is not evidence that this module is loaded. See
   [service runtime check](runtime/WR1200JS-2026-10-18-SERVICE-NAV.md).
   `/dev/watchdog` and `watchdog0` exist as a separate built-in path, but no
   readable timer-state attribute was available. The EN/UK/RU help now
   distinguishes that built-in driver from the optional module; this wording
   change still needs final-ROMFS verification.
   Build #478 also passed final-ROMFS checks for the settings backup/restore
   route, `login_safe()` gate, NVRAM and `/etc/storage` action rows/handlers,
   and EN/UK/RU labels. This is packaging evidence only; upload/restore, flash
   commit and recovery remain unverified on the router. See
   [service audit evidence](evidence/WR1200JS-BUILD458-SERVICE-AUDIT.md).
   A 2026-10-19 Node fixture now executes the inherited ROMFS handlers in an
   inert browser harness and checks guarded visibility, restore confirmation,
   backup download names, upload validation and CGI destinations. It passed
   locally against the available build #410 ROMFS page and is wired into the
   next build; CGI behavior and live-device recovery remain open. See
   [backup/restore behavior evidence](evidence/WR1200JS-SETTINGS-BACKUP-BEHAVIOR-2026-10-19.md).
   Extending that fixture to flash-save feedback reproduced invalid timer IDs
   on the unmodified #410 page/header. Local commit `931f1e4` repairs callbacks
   and accepts success only for the numeric backend result zero; the expanded
   VM fixture passes on transformed #410 and pinned source files. This local
   correction is published in PR #2 and awaits new image verification and browser/runtime
   acceptance; it performs no live flash or restore operation.
   Inspection of the #488 exact-image BusyBox report found that QoS and SFE
   had no entrypoint assertions. The SFE gate now checks `/sbin/rc`, the four
   Shortcut FE modules and BusyBox `modprobe`, with negative synthetic cases;
   local source checks pass. A new image must still run the gate, and this does
   not establish SFE activation or offload. The QoS gate now checks `tc`, the
   effective IMQ/IFB core symbols and every selected qdisc/classifier/action
   module against final ROMFS, with negative synthetic cases. A new image must
   still run the gate; it does not establish applied QoS rules or throughput.
   The pinned iproute2 recipe installed `tc` only with SQM, although this
   profile selects QoS and excludes SQM. Source preparation now installs the
   already-built `/bin/tc` for QoS OR SQM; GNU Make selection checks pass.
   The image gate additionally requires executable MIPS `tc`, its ELF/library
   closure and `tc -V` under target QEMU. This correction awaits a new image;
   usable QoS policy controls, lifecycle and physical acceptance remain open.
   See [SFE image gate evidence](evidence/WR1200JS-SFE-IMAGE-GATE-2026-10-19.md)
   and [QoS image gate evidence](evidence/WR1200JS-QOS-IMAGE-GATE-2026-10-19.md).
   Subsequent build #490 passed these image gates and inherited EN/UK/RU
   dictionary verification. The independently downloaded report confirms
   executable MIPS tc/library closure/version, 15 QoS modules and four SFE
   modules. Its runtime and whole-service-audit flags remain false. See
   [build #490 evidence](evidence/WR1200JS-BUILD490-SERVICE-AUDIT.md).
   Build #502 completed successfully and passed the current service navigation,
   Shadowsocks localization, settings backup/restore, target BusyBox, Stubby,
   iPerf3, KMS/Watchdog and StrongSwan exclusion image gates. Build #500's
   MT76X3 `FT_IGTK_ID` compile error was fixed by the PMF guard in `560ee18`;
   builds #501 and #502 passed afterward. This remains CI/image evidence, not
   router runtime acceptance; see
   [build #502 service audit](evidence/WR1200JS-BUILD502-SERVICE-AUDIT.md).
   Build #504 also completed successfully for PR head `9c1e9b1`. Its image
   gates passed service navigation, inherited EN/UK/RU dictionaries, Stubby
   packaging and an authenticated DoT lookup under QEMU, DoH packaging, the
   target BusyBox service audit, and the served-WebUI route audit. Its log also
   confirms the backup/restore page, Administration route, secure-session gate,
   EN/UK/RU labels and synthetic browser behavior. These remain CI/image checks;
   no router runtime or physical browser acceptance is established. See
   [build #504 service audit](evidence/WR1200JS-BUILD504-SERVICE-AUDIT.md).
   The unsupported-VPN selector source at `35d70be` is newer than and absent
   from #504. Firmware build #505 tested that commit and failed at the later
   VPN-pruning transform before compilation. Commit `25ca366`, pushed to
   `codex/wr1200js-service-webui`, makes that transform tolerate prior
   PPTP/L2TP removal while requiring removal of OpenVPN. Its focused in-memory
   fixture passes; post-fix CI and final-ROMFS results remain unconfirmed. See
   [build #505 failure and correction status](evidence/WR1200JS-BUILD505-FAILURE.md).
   The same branch now includes `e806465`, which extends the iPerf3 final-image
   gate to its executable, lifecycle/Apply wiring and ELF dependency closure.
   Local syntax and diff checks passed; the new image gate and on-router
   behavior remain unverified. See
   [iPerf3 image-gate evidence](evidence/WR1200JS-IPERF3-IMAGE-LIFECYCLE-GATE-2026-10-21.md).
   Firmware builds #506–#508 then failed in the same pre-compilation VPN
   pruning step: the current Classic pages already use a value-based OpenVPN
   capability hook, while the transform required an obsolete index hook.
   The transform now accepts one existing value-based hook or upgrades one
   legacy index hook, and rejects missing/duplicate hooks. Local source checks
   passed; the formerly fatal preparation step passed in builds #509–#511.
   All three later failed in the QEMU combined-dnsmasq validation: the image
   `dnsmasq --test` exited 5 with `failed to seed the random number generator:
   Success`. The pinned dnsmasq source reads 176 bytes from `/dev/urandom`;
   the test now constructs a temporary QEMU sysroot overlay with host-CSPRNG
   seed bytes and a guest-visible config path, without changing ROMFS. Local
   syntax/whitespace checks pass; QEMU rerun and final-image verification are
   pending. Builds #509–#511 produced no verified image (`images: []`,
   `missing-or-ambiguous`). See
   [#506–#511 failure evidence](evidence/WR1200JS-BUILD506-507-VPN-HOOK-2026-10-21.md)
   and [QEMU seed-path correction](evidence/WR1200JS-QEMU-DNSMASQ-SEED-FIX-2026-10-21.md).
   The System group also lacked direct links to selected KMS activation and
   ASUS Info Discovery controls. Local source navigation now adds both, keeps
   KMS capability-gated and distinguishes LLTD from ASUS discovery. An older
   ROMFS confirms the three control anchors; new-image and device browser
   behavior remain pending. See
   [system-service navigation evidence](evidence/WR1200JS-SERVICE-NAV-SYSTEM-LINKS-2026-10-21.md).
   The separate source-level Service runtime checks #247 passed selected SSH,
   iPerf3, Privoxy, Cron, LLTD/ASUS/KMS/Watchdog, VPN-profile and USB/IP
   fixtures; mocked operations do not prove device runtime. See
   [run #247 evidence](evidence/WR1200JS-SERVICE-STATE-CHECKS-247.md).
   Read-only SSH later succeeded on 2026-10-21. KMS flag/process agree as
   enabled/running; LLTD and ASUS Info Discovery flags/processes agree as
   disabled/stopped. The live service page still has generic, unanchored System
   links and lacks separate KMS/ASUS links, so the navigation correction is
   not installed. NVRAM has no build number; exact installed build is unknown.
   No router state changed. See
   [read-only service check](evidence/WR1200JS-SERVICE-READONLY-CHECK-2026-10-21.md).
   The inherited VPN client/server selectors also exposed PPTP and standalone
   L2TP despite their exclusion from the WR1200JS profile. Source preparation
   now removes those choices and fixes the OpenVPN capability check to target
   its option value; the next final image/browser review remains pending. See
   [unsupported VPN UI evidence](evidence/WR1200JS-UNSUPPORTED-VPN-UI-2026-10-20.md).
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
  Progress 2026-10-14: labels, options, help and errors are translated in source
  for EN/UK/RU, and the manual reload is replaced by a bounded 30 s visible-tab
  refresh with freshness, error text and retry
  ([evidence](evidence/ZEROTIER-PAGE-LOCALIZATION-2026-10-14.md)); build 271
  compiled that page and its status handler and re-verified the shipped image
  strings. Moon, static routes and the legacy NAT switch are now grouped under
  one collapsed advanced section, the Moon header is translated and the single
  Apply control was moved out of the group so it stays reachable
  ([evidence](evidence/ZEROTIER-ADVANCED-CONTROLS-2026-10-14.md)); the legacy
  NAT help states that it only masquerades overlay IPv4 sources toward the LAN
  while LAN access is on. Still open: verifying Apply, lifecycle, membership,
  permissions and connectivity on the device.
- **WireGuard/AmneziaWG:** the installed page is only a simplified WireGuard
  client form. Full Nilabsent interface parity has NOT been ported. Carry
  forward the donor requirement: client/server management, AmneziaWG parameters,
  import/export, adding/removing peers, authenticated local QR, real status,
  startup and translations. Verify kernel/userspace compatibility and preserve
  the existing remote tunnel. An operational tunnel does not establish WebUI
  completeness; applying an empty legacy form must not erase unrelated settings.
  Screenshot follow-up 2026-10-18: the legacy ZeroTier/WireGuard submenu still
  labels the WireGuard destination `WIREGUAED` and points to the empty legacy
  form. Source navigation now labels it WireGuard/AmneziaWG profiles, links it
  to the actual protocol-selecting `vpncli.asp` page, and exposes the shared
  service navigation on the old form so users can return to the profile page.
  This corrects the route and label; it does not finish full profile CRUD or
  physical-device acceptance. See
  [VPN submenu correction](evidence/VPN-LEGACY-SUBMENU-2026-10-18.md).
  The local final-ROMFS gate now checks this legacy submenu target and rejects
  the retired `Advanced_wireguard.asp` route and stale active-tab styling; its
  fixture passes locally. It also requires exactly one localized submenu key,
  matching upstream httpd's first-match dictionary lookup. The fixture rejects
  stale-first and duplicate entries. Pinned upstream `EN.footer` contains two
  stale copies of this key; preparation now replaces the first and removes the
  rest so the image gate can pass without changing lookup semantics. Build #478
  predates these source/gate changes, so new CI/image and router-browser checks
  remain pending.
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
- In shared mode, generate one QR from the common SSID, security type and
  password. Scanning it joins that Wi-Fi network; a client associates with one
  radio band at a time and chooses 2.4 or 5 GHz based on its capabilities and
  network conditions. Do not describe this as two simultaneous connections.
  When credentials differ by band, show a separate QR for each network.
  Owner runtime report, 2026-10-18: after forgetting the saved Wi-Fi network on
  a phone, scanning the router QR joined the phone to Wi-Fi while shared
  settings were configured. The installed firmware build and associated band
  were not recorded; this confirms QR-based joining, not simultaneous use of
  both bands or a specific band-selection behavior.
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

WR1200JS Transmit Beamforming is classified unsupported for the current image:
the board kernel config and saved effective config both disable
`CONFIG_MT76X2_AP_TXBF_SUPPORT`, while generic WebUI capability detection had
exposed the control from chipset ID alone. The board capability transform now
removes its WebUI row and HTTP form variable and sets `wl_txbf` off. CI checks
the effective kernel config and final ROMFS. This is build/source evidence;
the owner also reports that on the running router the control returns to Off
after Apply and logs subsequently show it disabled. This confirms the enabled
setting does not persist, though it does not isolate the rejection point in
the backend/driver path. See
[TXBF capability evidence](evidence/WR1200JS-TXBF-CAPABILITY-2026-10-18.md).

For every exposed function provide localized EN/UK/RU help explaining purpose,
valid values/units, dependencies, default, expected tradeoffs and any restart
or connectivity interruption. Explain unsupported/experimental status where
applicable; use concise basic help with expandable technical details. Verify
capability-filtered pages, backend rejection of unsupported values, optional
feature combinations and actual board behavior.

### Inherited contextual-help localization follow-up — 2026-10-18

The user reported that hover help, including the LAN/DNS fields shown in the
supplied screenshot, remains English when the interface is Russian or Ukrainian.
An available image-dictionary audit found 149 `_itemdesc` keys, with 10 missing
from RU and 15 missing from UK; missing keys cause the English fallback. The
same audit found 10 RU and 15 UK missing `_itemname` entries. The existing
`overlay/padavan-4.4/scripts/localize-inherited-dicts.py` source-preparation and
image-verification step now supplies the missing DNS, LAN and Wi-Fi text in
EN/UK/RU. This is a source change only until CI includes it and the owner checks
the installed pages; the audit used the available build #433 dictionary snapshot.

Also replace the inherited firmware version suffix with project build identity
(number plus short commit SHA) while preserving accurate kernel/version details
and upstream attribution in the credits/licenses. Ensure UI, image naming and
diagnostic reports identify the same build. Implementation remains pending.

## Per-router setup guide in final ZIP — user requirement 2026-10-11

For each completed, verified router profile, provide a UTF-8 plain-text setup
guide in the final user download ZIP alongside its firmware and build config.
This explicitly extends the earlier two-file TRX/config packaging requirement;
retain one user-facing download archive and exclude unrelated diagnostics.
Reference-only upstream boards must not receive invented verified instructions.

Write model-specific instructions for a 100 Mbps internet connection and for
a 1 Gbps connection where hardware supports it. Explain actual WAN/LAN port
limits, practical Wi-Fi limits and software/VPN processing constraints; a
gigabit subscription does not make a 100 Mbps port or wireless repeater gigabit.
Give clearly separated steps for WAN type, LAN/DHCP, Wi-Fi bands/security/channel
width, supported acceleration, DNS and required service controls. Adapt to
router/repeater use where verified and keep optional services distinct from
necessary setup. Preserve safe defaults and avoid blanket tuning advice.

Use verified firmware UI names, identify model and build, document settings
backup/restore and recovery prerequisites, and explain which Apply actions
interrupt connectivity. Cover maintaining SSH/VPN management access without
embedding private credentials. Record known limitations and unverified features;
do not promise performance without measurements. Start with Ukrainian guidance
and provide English alongside it for public users; share no private settings.
Name the document SETUP_<board>.txt (or a clearly identified language variant).

Generate/package the guide from the maintained model-specific source and verify
the final ZIP contains the correct firmware, config and matching instructions.
Prepare final wording when that board's firmware and controls are ready; keep
WR1200JS first, Mi Mini second, offline preservation last.

## Unified Services navigation — physical UI feedback, 2026-10-17

User confirmed the installed build still scatters services across Administration,
Shadowsocks and tunneling pages. This is an unfinished delivery requirement.
Provide one visible Services entry and a horizontal, wrapping navigation row:
DNS (Stubby/DoT, DoH and supported DNS tools), VPN (WG/AWG profiles, ZeroTier),
Proxy (Shadowsocks, Privoxy, WPAD), Access (HTTP/HTTPS, SSH, Telnet),
Diagnostics (iPerf3 and available diagnostic tools), System (Cron, watchdog,
discovery and other enabled system services). Keep model/build capability gates;
link only supported pages and retain existing authenticated Apply/lifecycle paths.

Each service must have a readable localized name, purpose/help, configured
on/off separately from observed running/stopped/error/unknown state, and a direct
settings link. A navigation row must appear consistently on service pages, with
an active-tab indicator, without requiring visits to unrelated router sections.
The user screenshot showed the six groups wrapping to three rows; the CSS
two-column breakpoint was lowered to 760 px so wider router views retain the
intended three-column/two-row layout. This needs browser verification in the
next image; see [service navigation layout adjustment](evidence/WR1200JS-SERVICE-NAV-LAYOUT-2026-10-18.md).
Do not classify KMS activation under terminal access. Existing VPN management
access must survive the UI reorganization. Navigation-only mockups/links do not
complete this requirement: verify destinations, forms, actual status and browser
layout on the physical router. No live services or tunnel settings were changed
while recording this feedback.

### Compact full-page navigation — owner feedback, 2026-10-18

Clarification from the owner: apply this to both sets. First, make the Stubby,
DoH and Privoxy service links compact and open their full settings pages in a
separate browsing context. Second, replace the three large homepage observation
panels (connected devices, Wi-Fi history/Band Steering actions, and RSSI Kick
driver events) with compact controls; each opens its complete read-only view in
a separate browsing context so the router homepage remains compact. Keep the
normal browser Back control and provide an obvious route back to the homepage.
Use full-page navigation rather than embedding these full views into an
oversized homepage panel. No live device changes are authorized by this UI
feedback.

Follow-up owner feedback, 2026-10-18: every service page opened separately must
show a clear return link to Administration → Services, while retaining normal
browser Back behavior. Each standalone homepage observation view must show a
Back control (use browser history when available, otherwise return to the
homepage) and a direct Home link. Put service state, observation timestamps,
refresh controls and their explanatory text on a light-blue information panel;
do not leave these additions as ungrouped gray text on white. The shared
enabled-toggle treatment remains green ON and neutral OFF, with observed
service health shown separately.

Navigation capability audit, 2026-10-18: the source parser previously
counted commented optional selectors such as `# CONFIG_FIRMWARE_INCLUDE_EOIP=y`
as enabled. It now excludes comments, and the final-ROMFS verifier requires
each page's navigation to exactly match the active build selectors. Local
pre-compilation checks cover commented `=y`, active `=n`/`=y`, and service
return navigation. The local fixture passes; a new firmware image and browser
review are still required. See [navigation evidence](evidence/WR1200JS-SERVICE-NAV-LAYOUT-2026-10-18.md).

## Classic IoT navigation — owner confirmation 2026-10-20

Add this requirement to the existing IoT deliverable without changing the
approved execution order. Continue points 4–8 in their current sequence;
Classic navigation work does not move IoT ahead of service WebUI or other
already ordered work. Preserve the prepared local files and all unrelated
uncommitted changes.

IoT must work with Classic as the only installed theme. Add matching
2.4 GHz / 5 GHz / IoT controls to the network map, paired Wi-Fi pages and
relevant shared shortcuts, with active highlighting and return paths.
Preserve Classic styling, responsiveness, existing Apply handling and main
network behavior. Reuse real ASP/CGI/NVRAM and IoT mechanisms; do not create
a new theme or duplicate configuration logic.

Owner decision, 2026-10-26: use the convenient button and tab behavior of
[Nilabsent Padavan NG](https://github.com/nilabsent/padavan-ng) as a usability
reference for Classic IoT. The three destinations must be equally discoverable
and use existing Classic button/tab classes, active highlighting and clear
return paths; changing a tab must not save or apply settings. Retain the
matching Wi-Fi section when switching 2.4/5 GHz. Do not copy Nilabsent's
visual styling or introduce its configuration writer. Complete controls and
status become usable only when the real authenticated IoT backend is bound.

Prepared navigation is partial and is not included in production builds.
Production activation, authenticated settings/Apply, isolated bridge,
DHCP/DNS, firewall, status and device acceptance remain in the existing IoT
stage. Evidence: `evidence/WR1200JS-IOT-CLASSIC-NAVIGATION-2026-10-20.md`.
No full firmware compilation or router changes are part of this checkpoint.

## Padavan Modern Ukrainian dashboard reference — owner addition 2026-10-21

Add the user's Ukrainian neon dashboard image as an additional reference for
the future Padavan Modern homepage. Keep the current execution order: finish
and verify IoT first, then finalize the Modern homepage design, then create
the Modern title/home page. Padavan Classic remains unchanged. This reference
does not authorize implementing the pictured secondary pages or changing
production logic now; see `WEBUI-MODERN-HOME-SCOPE.md` for the full visual and
data-truth requirements.

The dashboard reference calls for compact navigation and header controls,
2.4 GHz / 5 GHz / IoT selection, WAN/Wi-Fi/IoT and system-status cards,
traffic/CPU charts, and quick links to services actually available in the
WR1200JS build. Show only observed values; use `Н/Д` where a hardware sensor
is unavailable, and label local preview values as DEMO. Treat the small
secondary-page thumbnails as future design references, not permission to
implement those pages in this stage.

## Окремий етап: самодостатній репозиторій після прошивок — 2026-10-23

Окремий погоджений пункт роботи після завершення й приймання прошивки
WR1200JS, а потім етапу Mi Mini згідно з чинним порядком доставки вище.
Поточний порядок IoT, WebUI та решти прошивкових робіт не змінюється.

- Впорядкувати структуру за принципом повного дерева джерел, як у padavan-ng,
  зберігши правила Sol/DeepSeek, історію Git і напрацювання всіх акаунтів.
- Зібрати у нашому репозиторії точні вихідні коди ядра, драйверів, RC, WebUI,
  пакетів, патчів та рецепти/джерела toolchain, включно з транзитивними
  залежностями. Збережені архіви перевірити за ревізіями й контрольними сумами.
- Усунути обов'язкове отримання джерел зі сторонніх репозиторіїв під час
  збірки. Посилання на походження, авторство та ліцензії залишити: це
  атрибуція, а не зовнішня залежність збірки.
- Для великих файлів заздалегідь визначити зберігання з урахуванням лімітів
  GitHub; власні Release-архіви не вважати виконанням вимоги «все в дереві»
  без окремого погодження. Не переписувати історію й не видаляти резервні копії.
- Підготувати й перевірити середовище Ubuntu 24.04 та відтворюваний локальний
  рецепт складання. Docker/WSL вважати робочими лише після фактичної перевірки.
- Як можливий зразок інтерфейсу збирання розглянути Prometheus lekswrt:
  перевірений каталог моделей, показ ревізій, стану toolchain і результатів
  образу. Для Windows 10 спочатку перевірити WSL 2 + Ubuntu 24.04, а потім
  окремо вирішити потребу в контейнері. Скрипт збирання не має виконувати
  прошивання, мережеві завантаження чи зміну роутера. Аудит і обмеження:
  `docs/donor-audits/LEKSWRT-PROMETHEUS-2026-10-27.md`.
- Критерій завершення: повний інвентар джерел і ліцензій, відсутність
  незадокументованих зовнішніх завантажень, успішна збірка із заздалегідь
  підготовленого локального середовища без мережі та перевірка отриманого образу.
  Залежності самої Ubuntu/контейнерної бази також описати й підготувати до
  офлайн-запуску. Не заявляти про побітову відтворюваність без порівняння образів.

Статус: заплановано, не виконано. Цей запис не запускає міграцію або збірку.

## Останній етап проєкту: Linux 4.4.198 → 4.4.302 для всіх роутерів — 2026-10-24

Міграція ядра закріплена в самому кінці загального плану. Черговість:
завершити WR1200JS, виконати погоджені роботи для Xiaomi Mi Mini, закінчити
решту погоджених етапів і впорядкувати повне дерево джерел; лише потім — цей
можливий фінальний етап. Після Mi Mini та решти робіт окремо вирішити, чи
переходити на Linux 4.4.302. Якщо перехід буде схвалено, він охоплює кожен
роутер, який на той час доданий до проєкту, а не лише WR1200JS і Mi Mini. Для
кожної плати потрібні власні перевірка драйверів, конфігурацій і патчів,
збірка образу та приймання на пристрої; успіх на одній платі не підтверджує
сумісність решти. До початку цього останнього етапу ядро залишається на
4.4.198.

Початковий технічний аналіз WR1200JS і контрольований порядок дослідження:
`docs/KERNEL-4.4.302-MIGRATION-PLAN.md`. Перед виконанням розширити його
інвентарем і планом приймання для кожної фактично доданої плати. Зараз
міграцію не розпочато; образ 4.4.302 не збирали і роутери не прошивали.
