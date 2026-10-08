# WR1200JS project delivery requirements

User-approved extension, 2026-10-02.

Primary objective remains the Linux 4.4.198 port of YOUHUA WR1200JS,
preserving the user's configuration and required features, excluding CAKE
under the active thread objective reaffirmed on 2026-10-08. Earlier CAKE
proposals below are retained as history and are outside the current delivery.
Compilation alone does not establish a successful device port.

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
