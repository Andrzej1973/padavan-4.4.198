# WR1200JS AP-startup command scope — source audit

Date: 2026-11-06.  This is a source-path audit of the checked candidate base
`tools/iot/candidates/aux-remove-close-v39`; it is not a target build, ROMFS,
firmware-image, or device-runtime result.

## Ordering that must remain closed

In `common/rtmp_init_inf.c`, the AP auto-channel path enables PCI interrupts
and `RTMPEnableRxTx()` before it calls `AP_AUTO_CH_SEL()` and before the later
`APStartUp()` call.  `RTMPEnableRxTx()` in `common/rtmp_init.c` enables DMA and
MAC Tx/Rx.  Thus an integration that merely releases configuration immediately
before `APStartUp()` would be too late for an auto-channel boot.

The candidate's outer IoT bootstrap gate must therefore stay closed until the
configuration owner has a safe, explicitly bounded release point that also
covers the auto-channel receive/transmit path.  This observation does not
change user channel settings and does not reject automatic channel selection.

## Current upstream protocol check

On 2026-11-06 the current `master` of `nilabsent/padavan-ng` (reported pushed
2026-11-01) was checked at
`trunk/proprietary/rt_wifi/rtpci/4.1.X.X/mt76x3/mcu/andes_mt.c`.  Its
`CmdEdcaParameterSet()` and `CmdSlotTimeSet()` use the same no-wait,
no-response, no-callback Andes initializers.  It supplies no newer ACK or
readback contract for either command.  Therefore this project continues to
retain their intents rather than manufacture a completion claim.

## APStartUp inventory

The following calls occur during `APStartUp()` and must not be treated as a
single firmware-ACK transaction:

| Area | Source path | Result of the audit |
| --- | --- | --- |
| EDCA | `ap/ap.c` -> `AsicSetEdcaParm()` -> `CmdEdcaParameterSet()` | Firmware command `0x27`; SDK route has no response/callback.  It is retained as an unconfirmed timing intent and blocks configuration finish. |
| Slot time | `APUpdateCapabilityAndErpIe()` -> `AsicSetSlotTime()` -> `CmdSlotTimeSet()` | Firmware command `0x28`; also no response/callback and retained as an unconfirmed timing intent. |
| RDG and WTBL RDG | `AsicSetRDG()` / `AsicWtblSetRDG()` | Direct MMIO reads/writes, not an Andes firmware command. |
| TXOP | `AsicUpdateTxOP()` -> `AsicSetWmmParam()` | WMM/EDCA programming; it must remain covered by the timing-intent boundary. |
| Ralink burst | `AsicSetRalinkBurstMode()` | MT HIF path reports unsupported and returns; no firmware command is sent. |
| Protection | `AsicUpdateProtect()` -> `RTEnqueueInternalCmd()` -> `MtCmdAsicUpdateProtect()` | Internal command-thread/MMIO work, distinct from an Andes ACK. |
| Preamble/rates | `MlmeSetTxPreamble()`, `MlmeUpdateTxRates()`, `MlmeUpdateHtTxRates()` | AP rate/state setup; audit does not infer a firmware receipt from these callers. |
| BSSID, beacon, sync, pre-TBTT | `AsicSetBssid()`, beacon generation, `AsicEnableBssSync()`, `AsicSetPreTbtt()` | Hardware/AP service setup, not evidence of MCU configuration completion. |
| Band Steering | `BndStrg_Init()` / `BndStrg_SetInfFlags()` | Happens near the end of startup and must be preserved; it is not a reason to advance the IoT gate. |

`APStartUp()` is also called by the auto-channel rescan command thread after
`APStop()`.  A first-open-only shortcut would therefore be insufficient.

## Consequence and next proof

No new gate opening, ACK claim, or normal-data promotion follows from this
audit.  The next implementation step is to bind configuration ownership and
failure/abandon handling into the real outer initialization path, then prove a
bounded checked-command budget and a release condition that is safe before the
auto-channel Rx/Tx transition.  Only after that can target compilation, final
image inspection, and separately authorized device testing establish stronger
evidence.
