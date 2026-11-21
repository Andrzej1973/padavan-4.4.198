# Mi Mini port status

## Current owner priority — 2026-11-21

Mi Mini work is deferred until WR1200JS acceptance, including the four required
final variants. Do not continue source audits, implementation, builds, or device
work for Mi Mini during this stage, including while WR1200JS jobs are running.
The dated entries below preserve earlier findings and proposed next steps; they
are not authorization to resume Mi Mini work. Keep its board disabled until its
own image and mandatory IoT gates pass after the WR1200JS stage.

## RBUS stop located; failure propagation still open — 2026-11-07

Resolved the previous partial trace: common/mlme.c MlmeRadioOff uses
include/chip/mac_pci.h:439–440, calling RT28xxPciMlmeRadioOFF. Its explicit RBUS
branch in common/cmm_mac_pci.c:2373–2432 disables DMA and polls DMA/MAC idle.
There is no missing-stop conclusion. The bounded DMA loop can exhaust without
returning failure; MAC timeout logs and continues; the API is VOID. Before
accepting ring release, implement a checked stop/lifetime-retention contract
rather than simply adding a timeout. Exact evidence updated in the close-path
JSON. No source behavior changed; runtime remains unverified.


## RBUS close path remains under review — 2026-11-07

RTMPDrvClose waits indefinitely for DeQueueRunning, then runs MlmeHalt,
RtmpNetTaskExit, APShutdown and RtmpMgmtTaskExit. The later checked PCI radio-off
call is restricted to PCI/PCIE infType, so it cannot establish RBUS DMA idle.
IRQ release precedes ring reset/free, but APShutdown descendants and producer
exclusion still require review. Do not infer a DMA bug from this partial trace,
and do not add a timeout that continues into freeing live memory.
[Exact source/line evidence](evidence/MI-MINI-CLOSE-PATH-2026-11-07.json).
Potential future source step after WR1200JS acceptance: trace APShutdown/MAC
stop specifically for RBUS.


## Background detach ownership trace — 2026-11-07

Pinned nilabsent d2c5846: rbus_main_dev.c detach calls RtmpPhyNetDevExit,
then RtmpRaDevCtrlExit, then RtmpOSNetDevFree. rt_main_dev.c:741–781 removes
APCLI/WDS/MBSS under their feature guards and unregisters the primary netdev.
rt_linux.c:1700–1709 unregisters netdev then releases its netdev_ops;
common/rtmp_init.c RtmpRaDevCtrlExit calls RTMPFreeAdapter. rt_linux.c:1585–1611
frees private netdev metadata and finally free_netdev. The candidate clears
rt2880_dev after that path. Do not add another adapter free after CtrlExit.
This source trace does not yet prove timer/task/IRQ/DMA quiescence: continue
through registered close callback and concrete RTMPFreeAdapter implementation.
No detach code changed; no runtime acceptance claimed.


## MMIO admission implementation — 2026-11-07

Candidate platform probe rejects missing/wrong-sized/wrong-base WMAC resources
before mapping or vendor attach. Host ASan/UBSan tests execute its actual probe
with injected resource/IRQ/map/attach outcomes. Bundle hash and lightweight CI
fixture updated; no target/device acceptance, DTS instantiation or clock/reset
support implied. This was a local host-only candidate step, not board build
admission or authorization for further Mi Mini work. Next, after the deferred
stage resumes: review clock/reset/pinctrl/Factory binding and DT.


## Background DT resource review — 2026-11-07

Exact OpenWrt reference606ee33b8a049244759de735a48e98b00ec8ad5c identifies
WMAC MMIO0x10180000/0x40000 and CPU interrupt6; EEPROM cells at Factory0/0x8000.
These are source references, not device evidence or a ready vendor4.4 DTS.
Current adapter acquires mapped MMIO+IRQ but no clock/reset/pinctrl ownership;
Factory binding expects case-sensitive `Factory` whereas reference DTS uses
`factory`. Reference modern clock/NVMEM bindings are not pinned4.4 bindings.
Reference firmware0x50000/0xf80000 preserves tail partitions and must not be
adopted as the owner's Padavan partition map. CPU IRQ6 must be resolved through
DT irq domain, not assumed to be global Linux IRQ6. Next: resolve these adapter
and binding contracts before creating/enabling a bootable board DT.
[Exact source/blob evidence](evidence/MI-MINI-DT-RESOURCE-REFERENCE-2026-11-07.json).


## Background source check — 2026-11-07

Fresh nilabsent master c29b12da69b1593a6e8cf65cd43767fc99bb6386 has the same
RT2860 radio subtree SHA ee88f6d0b37bab21bbc2ec34eb7c49480e297818 as pinned
d2c5846299949c57a4e867284069900b561dd2a4. A radio donor rebase is not needed
merely because master advanced; other board/package files can still differ.
The platform adapter requires `xiaomi,mi-mini-mt7620-radio`, but pinned kernel
DTS has no such node and the installer explicitly leaves DTS unchanged.
A linked probe/attach symbol is therefore insufficient to instantiate the
radio. Next board step: review DT resources, IRQ/reset/clock/Factory binding
and image integration; do not invent numeric resources from another board.
[Exact evidence](evidence/MI-MINI-RADIO-DONOR-AND-DT-2026-11-07.json).


## Historical scope and schedule — owner clarification 2026-11-07

The owner means the entire [audit and plan](MI-MINI-AUDIT-2026-11-07.md),
not just enabling LPRD. The 2026-11-07 spare-interval schedule was superseded
on 2026-11-17; Mi Mini work now waits until WR1200JS acceptance.
The completed audit is the source inventory and plan, not board acceptance.
LPRD's local profile change remains a separate recorded change.

| Phase | Current state / next action |
| --- | --- |
| Hardware/source audit | Report complete; verify exact R1CM revision, bootloader, MTD and current donor sources before dependent work |
| Board and image port | Existing isolated radio/kernel candidate only; complete Ethernet, DTS/platform, GPIO, USB, both radios and safe image layout |
| Router and mandatory IoT | Not accepted; prove routing, DHCP/DNS, isolation, main/guest/IoT, lifecycle and image inclusion for this board |
| Manual repeater/WISP | Plan recorded; verify each uplink and AP coexistence before automatic selection |
| Automatic dual-band uplink | Not implemented by adopting this plan; add link/gateway/loss/RSSI metrics, priorities, hysteresis, dwell/backoff and recovery |
| USB/Ethernet printing | Reuse p910nd and existing controls, optional LPRD included locally; implement LAN policy and direct network-printer inventory, then verify actual printers |
| WebUI and safe mode changes | Extend existing authenticated pages in the approved style; preserve Router mode, configuration and management access with rollback |
| Release/device acceptance | Open; target modules, full image/ROMFS/size/SHA256 and separately authorized runtime tests remain required |

Future next action after WR1200JS acceptance: review the existing board/radio
candidate against fresh donor sources and close its board/image gaps; do not
start with a new printer server or claim the port enabled in the build catalog.
Use the same checkout, single writer and CI queues.

## Printing and execution priority — 2026-11-07

Owner-approved candidate profile change: include LPRD in addition to the
existing USB RAW/p910nd route; leave U2EC excluded. See
[the current dependency decision](MI-MINI-DEPENDENCY-REVIEW.md).
No image/target/device or printing acceptance is established by this selector.
Keep `boards.json` disabled until the complete board/image and mandatory IoT
gates pass. The earlier background-work timing is superseded: resume Mi Mini
implementation only after WR1200JS acceptance. Reuse existing printer controls,
enforce LAN/approved-VPN access, preserve Router mode, and implement manual WISP
before automatic stability-based uplink selection.

## Supplied MI-MINI config — 2026-10-03

## Isolated radio CI record — 2026-10-26

Two diagnostic Mi Mini radio/kernel candidate runs succeeded; the later run
linked an isolated MIPS `vmlinux`. Neither built firmware nor tested the router.
Both diagnostic artifacts are no longer available through GitHub's artifact
API. Run IDs, exact commits and verification limits are preserved in
[the CI evidence record](evidence/MI-MINI-RADIO-PROBE-CI-2026-10-26.md).

## Additional local references — 2026-10-18

User-found stock images, bootloader and Factory-like dumps have been preserved
outside Git with verified SHA256 copies. See
[analysis and usage limits](MI-MINI-USER-FILES-2026-10-18.md).
The supplied board.h matches the pinned board; the EEPROM patch is not approved
for incorporation. This reference import does not establish runtime acceptance.

## Original supplied profile

Preserved unchanged as mi-mini.source.config, SHA256
2b20dd63a39ebe46eb402b71cf018c91eb63aeff13cc5045f1a928f55516c9e3.

File selects XIAOMI / MT7620 / MI-MINI. Matches pinned nilabsent board
trunk/configs/boards/XIAOMI/MI-MINI, d2c5846299949c57a4e867284069900b561dd2a4.
This establishes the supplied profile's target, not the remote router identity.
Board sources report 128 MiB RAM, one USB port, no gigabit LAN/WAN, integrated
2.4GHz radio and MT7612E second radio. EEPROM offsets and 3.4 driver selectors
must be translated against actual 4.4 drivers and MTD layout, not copied blindly.

QUIC=y while OPENSSL_35 is commented despite the file's documented prerequisite.
Resolve in the derived profile against actual build recipes. ZRAM=y is a module
inclusion request, not evidence the service is enabled at runtime.

Large enabled functions include Samba, miniDLNA, Transmission and its web UI.
The approved storage/media exclusions are applied below. Camera and printer
services remain selected; no additional removal was authorized in this step. Determine
the actual remote-access tunnel requirements before omitting VPN support:
both WireGuard and AmneziaWG selectors in this supplied file are commented.

User approved excluding Samba, miniDLNA, Transmission and Aria from the second
router profile. Derived mi-mini.config now comments SMBD, WINS, SMBD_SYSLOG,
TESTPARM, MINIDLNA, TRANSMISSION, TRANSMISSION_WEB_CONTROL, ARIA and
ARIA_WEB_CONTROL. Original supplied profile remains the reference copy.
Other packages have not been implicitly excluded by this instruction.

Current WR1200JS 4.4 workflow remains unchanged; no MI-MINI image compiled.

Pinned vipshmily4.4 board directory inspected on2026-10-03: no MI-MINI board
profile. DTS directory contains mt7620a.dtsi and mt7620a_eval.dts but no
mi-mini.dts. config.arch has non-MT7621 tuning fallback24kec. These are useful
porting components, not a complete board port. Need actual MT7620 SoC/ethernet/
radio support, board DTS and kernel template before admitting MI-MINI to CI.

## Driver and DTS audit, 2026-10-03

Located vendor Ethernet at drivers/net/ethernet/raeth. raether.c OF match table
names mt7623-eth, mt7622-raeth and mt7621-eth, with no MT7620 match. The switch
ioctl_mt762x.c retains MT7620-specific branches, including CONFIG_RALINK_MT7620.
Platform Kconfig exposes SOC_MT7620 instead; leftover switch branches do not
prove they are selected or correctly integrated. Must inspect/register the
actual MT7620 Ethernet path rather than treating switch comments as support.

prepare-mi-mini-profile.py now creates the reduced profile from the untouched
source, validates target identity and rejects duplicate/missing selectors.
Executed on supplied source: precisely four active lines changed (SMBD,
MINIDLNA, TRANSMISSION, TRANSMISSION_WEB_CONTROL); Aria and other related flags
were already commented and remain so. All other original lines preserved.

Pinned 4.4 arch/mips/ralink/Kconfig exposes SOC_MT7620, but this does not
provide the board peripherals. mt7620a_eval.dts describes only an evaluation
board, 32MiB memory and UART bootargs. mt7620a.dtsi contains CPU/sysc/intc/memc/
UART nodes; no Ethernet, SPI flash, PCIe or USB nodes are defined there.
It cannot serve as a complete Mi Mini device description unchanged.

The MediaTek vendor wireless Kconfig offers first-radio MT7602E/MT7603E/
MT7615E/MT7622/MT7626/MT7915 and second-radio MT7612E. It has no first-radio
MT7620/RT2860 selector matching the nilabsent MI-MINI integrated 2.4GHz radio.
MT7602E is not a valid substitute merely because names are similar. Need an
actual MT7620 integrated radio driver port or a supported alternative with
Padavan control-plane integration. MT7612E second-radio support is present.

Next source search: locate Ethernet implementation under actual vendor path,
then inspect potential MT7620 Linux4.4 donors for integrated radio and platform
support. Do not publish a nominal dual-image workflow that silently loses2.4GHz.
