# Supplied MI-MINI config — 2026-10-03

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
