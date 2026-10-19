# WR1200JS Transmit Beamforming capability — 2026-10-18

## Additional read-only router evidence — 2026-10-19

Access: Windows OpenSSH to `ASUS@192.168.20.1`. The commands below only read
router state; no radio, NVRAM, Factory, firmware, or service change was made.

- `/proc/mtd`: `mtd2` is the 64 KiB `Factory` partition (`00010000` size,
  `00010000` erase size). Other entries were `mtd0 Bootloader`, `mtd1 Config`,
  `mtd3 firmware`, `mtd4 kernel`, `mtd5 rootfs`, `mtd6 Storage`, `mtd7 ALL`.
- `/proc/bus/pci/devices`: Wi-Fi entries include `14c3:7603` (`mt7603_drv`)
  and `14c3:7662` (`rtpci`). Loaded modules include `mt76x3_ap` and
  `mt76x2_ap`.
- `ifconfig -a`: 5 GHz `rai0` and 2.4 GHz `ra0` were both `UP RUNNING` and
  carrying traffic. One 5 GHz snapshot: `rai0` RX 801578 packets, TX 4155891.
- `iwpriv rai0` lists `set`, `show`, `get_site_survey`, `get_mac_table`,
  `e2p`, `bbp`, `mac`, `rf`, `get_ba_table`, and `stat`. Bare `iwpriv rai0 show`
  exited successfully without output. No `e2p`, `bbp`, `mac`, `rf`, or `set`
  operation was issued.
- `iwpriv rai0 stat`: temperature 39; average RSSI -52; TX success 4381090;
  TX retry 3101152 (`PER=41.4%`); ACK failure after retry 685
  (`PLR=0.01%`); RX success 806823; RX CRC 232941 (`PER=22.4%`);
  RX PHY error 194; RX PLCP error 431813; last TX rate MCS9, 2SS, 80M,
  SGI, VHT. This snapshot is not a TXBF activity counter or a diagnosis of
  the retry cause.
- Filtered `dmesg`: `NVM is EFUSE mode`, `Load EEPROM buffer from efuse,
  and change to BIN buffer mode`, `mt76x2_calibration(channel = 42)`, and
  temperature/TX-ALC EEPROM information appeared repeatedly. No line matched
  `txbf`, `beamform`, `implicit`, `explicit`, `ETxBf`, `ITxBf`,
  `BeamformerCap`, or `BeamformeeCap`. The observed calibration line does not
  identify TXBF calibration. eFuse-backed NVM remains a possible research
  lead, not proof that TXBF-specific data exists there.
- The module is at
  `/lib/modules/4.4.198/kernel/drivers/net/wireless/mediatek/mt76x2_ap/mt76x2_ap.ko`.
  `/usr/bin/strings` exists (also a
  BusyBox applet). It finds `ETxBf=%d, ITxBf=%d`, `ITxBf=%d`, `ETxBf=%d`,
  `SU BeamformerCap=%d`, `SU BeamformeeCap=%d`, `MU BeamformerCap=%d`, and
  `MU BeamformeeCap=%d`. These are format strings in a binary, not runtime
  values. The earlier `strings unavailable` result was erroneous because this
  router's shell reports `command: not found` for `command -v`.
- `nvram show` filtered for TXBF: `wl_txbf=1`, `wl_txbf_en=0`. The generated
  5 GHz profile `/etc/Wireless/iNIC/iNIC_ap.dat` contains `ITxBfEn=0`,
  `ETxBfEnCond=0`, and `ITxBfEnCond=0`. Thus the saved user switch requests
  TXBF, but the board gate and applied profile disable it. The presence of
  TXBF-related strings in the module does not override the effective kernel
  config or this profile state.

**Decision:** The source permits an experimental rebuild with
`CONFIG_MT76X2_AP_TXBF_SUPPORT=y`. These observations are insufficient to
claim that this would produce working TXBF on this WR1200JS. The current RC
Factory gate would still generate zero TXBF profile values. Research whether
the driver supports an independently calibrated explicit-BF path or a
documented device-specific calibration procedure before any attempt to change
the gate or expose a working switch. The owner received this router from China
already running an older Padavan image and has no earlier Factory dump.

## Source review: calibration and explicit BF — 2026-10-19

Reviewed pinned source archive `padavan-4.4-c25283e-git-exact.tar` at
`trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2/`:

- `common/cmm_txbf_cal.c` has `ITxBFGetEEPROM` and `ITxBFSetEEPROM` for
  per-channel phase, LNA and divider data. On MT76x2, a wholly uninitialized
  phase area (`0xffff`) is rejected. `ITxBFSetEEPROM` can call
  `RT28xx_EEPROM_WRITE16`; the divider calibration path can save results to
  eFuse. These are manufacturing/calibration functions, not a proven safe
  read-only or automatic runtime recovery procedure for this board.
- `common/cmm_txbf.c` has `rtmp_chk_itxbf_calibration`, which calls
  `ITxBFGetEEPROM` on MT76x2 5 GHz, and separate explicit BF capability,
  client feedback and sounding paths (`clientSupportsVHTETxBF`,
  `setVHTETxBFCap`, `eTxBFProbing`). Their presence does not establish that
  explicit BF operates correctly on this uncalibrated WR1200JS.
- `common/cmm_profile.c` parses `ITxBfEn` and `ETxBfEnCond` under
  `TXBF_SUPPORT` and the hardware-capability gate. The current RC path writes
  both as zero because `wl_txbf_en=0`.

Conclusion: the source supports building a TXBF-capable driver and contains
calibration routines, but no validated device-safe procedure or confirmed
calibration-independent explicit-BF route was established. Do not run
calibration/write ioctls, force the Factory gate, or call the feature working
without a separate controlled plan and runtime measurements.

## Live router follow-up — 2026-10-19

Read-only Windows OpenSSH session to `ASUS@192.168.20.1`; no NVRAM, radio,
service, firmware or firewall changes. Router reported Linux 4.4.198 built
2026-10-18 14:19 UTC. Observations:

- `nvram get wl_txbf` returned `1`. The owner is correct: the saved setting is
  currently **on**. A switch or NVRAM value alone does not prove TXBF packets.
- `/sys/class/net/rai0/operstate` returned `up`; `/proc/modules` lists
  `mt76x2_ap`, the 5 GHz AP driver, loaded.
- The live `/proc/config.gz` reports
  `# CONFIG_MT76X2_AP_TXBF_SUPPORT is not set`. This is evidence from the
  running kernel, independent of the saved build #410 config.
- `iwpriv rai0 show txbf` returned `Invalid argument`; this command is not a
  supported readout of actual TXBF operation on this driver. No TXBF or
  beamforming lines were found in the sampled `dmesg` output. Neither absence
  is used as the main support test.

Conclusion for the installed image: the saved `wl_txbf=1` does not make the
disabled `CONFIG_MT76X2_AP_TXBF_SUPPORT` driver path available. Actual
beamformed frame exchange was not measured, so the observation proves the
kernel build limitation and misleading saved state, not per-client radio
behavior. The earlier owner report below described a different observed UI
session in which Apply returned the switch to Off; it is not the current
router state. Capability manifest `unsupported` remains appropriate for this
installed WR1200JS image. Re-evaluate after any kernel/driver change.

## Can enabling the kernel option make TXBF work? — 2026-10-19

The pinned MT76x2 AP Kconfig does offer `MT76X2_AP_TXBF_SUPPORT` for MT7612E.
When enabled, its Makefile compiles `cmm_txbf.o` and `cmm_txbf_cal.o` and
defines `TXBF_SUPPORT` and `VHT_TXBF_SUPPORT`. The driver reads
`ETxBfEnCond` from the radio profile and, when enabled, writes TXBF control
registers. So a build with the option set to `y` is technically possible.

There is a separate board-specific gate. Pinned `trunk/user/rc/common_ex.c`
checks 33 factory bytes at `OFFSET_TXBF_PARA` and, conditionally, another 33
bytes at `0x81A0`; an all-`FF` region sets `wl_txbf_en=0`. For WR1200JS the
first offset is `0x01A0` (`ralink_priv.h`). Pinned `trunk/user/rc/ralink.c`
requires both `wl_txbf>0` and `wl_txbf_en==1` before it writes
`ITxBfEn=1`, `ETxBfEnCond=1`, and `ITxBfEnCond=1` into the 5 GHz profile.

Read-only SSH check of **this router's** `/dev/mtd2ro` (`Factory`, 64 KiB):

| Factory offset | Bytes read | `FF` bytes |
|---|---:|---:|
| `0x01A0` | 33 | 33 |
| `0x81A0` | 33 | 33 |

Only byte counts were recorded; no factory contents were copied or changed.
The live `nvram get wl_txbf_en` returned `0`, consistent with the source gate.
Thus enabling the kernel option alone cannot yield working TXBF on this
device: RC will still write zero to the radio profile. Bypassing the factory
gate or copying calibration bytes from another unit would be an unvalidated
radio change. No such change or firmware build was made. To revisit this,
obtain authentic TXBF calibration data for this exact unit or a documented
vendor calibration procedure, then inspect the data and validate a candidate
build and on-device behavior before exposing the feature as working.

## Finding

The current WR1200JS image does not enable the MT76x2 AP transmit beamforming
driver option. The board kernel config explicitly contains
`# CONFIG_MT76X2_AP_TXBF_SUPPORT is not set`; saved build #410's effective
kernel config has the same setting. The 5 GHz WebUI had nevertheless exposed
`wl_txbf` because generic capability generation reported TXBF for the MT7612
chip ID. The inherited defaults also set `wl_txbf` to `1`.

## Change recorded in source

The WR1200JS capability manifest marks 5 GHz Transmit Beamforming
`unsupported`. Its build preparation disables the generic capability, removes
the control and its HTTP form variable, and sets the default to `0`. The final
image verifier checks the effective kernel config, final ROMFS page, HTTP
variable table and default. Other boards' shared feature implementation is not
removed.

## Evidence boundary

This establishes that the current configured image does not build in the
MT76x2 AP TXBF option and that the prior WebUI control was misleading. It does
not establish actual radio behavior with TXBF enabled. The owner reports a
direct WebUI observation on the running router: after enabling the control and
pressing Apply, the switch returns to Off, and the logs subsequently show it
disabled. This confirms that the requested enabled setting does not persist on
the running firmware; it does not by itself distinguish driver rejection from
HTTP validation or another apply-path behavior. At the time of that initial
review, the sandboxed SSH command resolved to a denied shim. Subsequent
approved, read-only SSH checks are recorded above. No firmware was built or
flashed during this investigation.
