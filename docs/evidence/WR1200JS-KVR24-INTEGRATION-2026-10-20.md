# WR1200JS 2.4-GHz k/v/r integration — 2026-10-20

Owner confirmed implementation of 802.11k/v/r on 2.4 GHz, not merely removing
the old switches. The live #474 audit remains historical evidence: it has all
four saved KVR flags on but omits the MT7603E k/r/WNM code at compile time.
This change requests the existing driver implementation in the next image.

## Source and integration

Pinned source revision c25283e915a2a00a763774dd255b14aff997285e:
- mt76x3_ap/Kconfig declares the three bool options depending on
  MT7603E_RLT_AP_SUPPORT, already selected as a module for WR1200JS.
- mt76x3_ap/Makefile selects FT common objects plus ap_ftkd.o for DOT11R,
  RRM objects plus required scan defines for DOT11K, and wnm.o with
  CONFIG_DOT11V_WNM for WNM. scan.o is part of the common objects already.
- cmm_profile.c calls the parameter readers under the corresponding guards.
- rrm.c reads RRMEnable and implements neighbor reports; wnm.c reads
  WNMEnable into per-BSS WNMBTMEnable and implements PeerWNMAction/BTM.
- ft.c reads FtSupport/FtRic/FtOtd and supports per-BSS FtMdId/FtR0khId.

WR1200JS now requests CONFIG_MT7603E_DOT11R_FT_SUPPORT,
CONFIG_MT7603E_DOT11K_RRM_SUPPORT and CONFIG_MT7603E_WNM_SUPPORT as y.
The previous duplicate/shadowing-record repair in RC remains necessary.
Existing HTTP fields rt_HT_80211KV and rt_HT_80211R, Wi-Fi restart dispatch,
and factory defaults 0 are retained. No live NVRAM or router state is changed.
Existing saved value 1 may activate newly compiled code after a future approved
firmware upgrade; do not confuse factory-off with resetting restored settings.

## Image gate

verify-wifi-kvr-image.py requires exact effective config selections, a MIPS
relocatable driver both in the build and final ROMFS, and defined executable
symbols for RRM parameter parsing/neighbor handling, WNM parsing/action/init,
and FT parsing/authentication/association. It also requires one unambiguous
RRM/WNM generator record, the shipped 2.4-GHz form, compiled HTTP key presence,
Wi-Fi2 restart registration and unique factory-off defaults. CI invokes it
after the actual firmware build and uploads wr1200js-kvr-image JSON.

Local verification: Python AST, requested config, omission of each option and
duplicate-option rejection passed. The existing native C generator regression
passes both getter variants. No local driver/firmware compilation or new
image execution is claimed; compiler/link errors in the newly enabled vendor
code, dependency closure and firmware size still require CI confirmation.

## Acceptance still open

This is the first integration step, not a statement that k/v/r is operational.
Observe advertised capability IEs, neighbor-report response, BTM exchange and
client behavior after an explicitly approved update. Full FT acceptance needs
compatible clients, a second AP, matching mobility-domain/key-holder setup and
verified key distribution. The current generator exposes only coarse enable
flags, not full mobility-domain/key-holder management; review the vendor FT
initialization/transport and existing daemon requirements before declaring
inter-AP roaming supported. Do not equate Band Steering or RSSI Kick with FT.

5-GHz WNM source/build inclusion remains a separate open requirement; selecting
the MT7603E options does not enable it. Per-board manifest now marks 2.4-GHz
next-build status runtime-unverified with build verification pending. The live
#474 report and its unsupported-current-image conclusion are not overwritten.
