# WR1200JS Band Steering integration

Required: include functioning steering support in firmware, with factory runtime
settings disabled and user controls in the WebUI. This is an unfinished port.

Base: vipshmily/padavan-4.4 at c25283e915a2a00a763774dd255b14aff997285e.

## Source findings

- WR board kernel config disables CONFIG_MT7603E_BAND_STEERING_7603 and
  CONFIG_RT_BAND_STEERING.
- Driver Makefile.rlt_wifi_ap conditionally compiles ap_band_steering.o.
- Both mt76x2 and mt76x3 ap/ap_band_steering.c emit wireless events to a
  userspace daemon. The mt76x3 implementation tracks DaemonPid, receives driver
  messages and includes daemon-killed handling.
- No band-steering daemon path was found in the pinned trunk/user file list.
  This search result does not prove no compatible daemon exists elsewhere.
- Headers are include/band_steering.h and include/band_steering_def.h for each
  driver. Compare message structures, IDs, packing and ioctls before selecting
  or adapting a userspace implementation.
- Existing WebUI capabilities advertise 5 GHz steering for MT7612, while
  2.4 GHz MT7603 is excluded. Configuration generation for BandSteering is
  targeted at newer chips; these controls are not operational proof for WR.

## Required implementation and evidence

1. Find and preserve a compatible daemon source and its license.
2. Audit both driver protocols; implement compatibility where required.
3. Compile both driver features and daemon with target toolchain.
4. Complete coherent per-router UI, configuration and lifecycle handling.
5. Preserve wl_band_steering=0 and rt_band_steering=0 factory defaults.
6. Verify compiled image, command/event exchange and startup/restart behavior.
7. Test dual-band client behavior with appropriate SSID/security configuration.

Do not replace coordinated steering with RSSI Kick or simply show an enabled
UI control. No physical router changes or device runtime verification have
been performed for this feature.
