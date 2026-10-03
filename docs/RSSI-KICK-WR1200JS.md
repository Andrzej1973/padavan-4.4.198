# WR1200JS RSSI Kick: source evidence and acceptance

Status: driver implementation located; firmware control integration and device behavior remain unverified.

## Pinned source

Base: vipshmily/padavan-4.4 at c25283e915a2a00a763774dd255b14aff997285e.
Paths below are relative to that source tree.

Both radio drivers register the private command `KickStaRssiLow` and set
`MBSSID[apidx].RssiLowForStaKickOut`:

- `trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2/ap/ap_cfg.c`: command around line 992, setter around 7705.
- `trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_cfg.c`: command around line 774, setter around 6734.

The setters accept zero to disable, or a negative RSSI threshold down to -100.
They convert to CHAR before validating, so firmware controls must validate the
full numeric input before passing it to the driver.

## Actual disconnect consumers

### 5 GHz / MT7612E / mt76x2

`mt76x2/ap/ap.c`, around line 1381, checks nonzero LastDataRssi samples against
the configured threshold. A count of at least three below-threshold samples
sets bDisconnectSta. The adjacent comment describes three of five samples.
The subsequent disconnect branch emits a wireless ageout event and sends a
deauthentication frame for an associated station.

This implementation depends on recorded data RSSI; do not assume an idle
client is checked in the same way as an active client.

### 2.4 GHz / MT7603E / mt76x3

`mt76x3/ap/ap.c`, around line 2288, compares RTMPAvgRssi with the configured
threshold and sets bDisconnectSta when the average is lower. It includes
RSSI kickout logging and optional diagnostic events.

These are source implementation findings, not a measurement of the disconnect
interval or proof of behavior on the physical WR1200JS.

## Existing firmware controls

`trunk/user/shared/defaults.c` contains defaults of zero for:

- wl_KickStaRssiLow / rt_KickStaRssiLow;
- wl_AssocReqRssiThres / rt_AssocReqRssiThres.

The inspected `trunk/user/rc/ralink.c` has only commented example output for
AssocReqRssiThres and KickStaRssiLow around lines 792–795.
The inspected Advanced_WAdvanced_Content.asp and Advanced_WAdvanced2g_Content.asp
under `trunk/user/www/n56u_ribbon_fixed/` contain no RSSI kick controls.

A matching NVRAM name alone does not establish that a threshold is applied.
Association rejection is a different function from disconnecting an existing
client; expose them with separate explanations if both are implemented.

## Remaining required work

1. Check prepared project overlays and all radio startup/restart paths.
2. Implement validated per-radio controls and apply thresholds consistently,
   preserving zero as the default.
3. Verify settings survive ordinary configuration reloads without silently
   enabling the feature.
4. Check compiled image and driver command support.
5. Perform a physical-client test: threshold, observed RSSI, disconnect event,
   and subsequent reconnection.
6. With multiple access points, observe client reassociation separately.
   RSSI Kick does not establish 802.11r fast transition support.

Start remote work with read-only inspection. Use a separate test client that
does not carry the remote management connection. No flash or reboot is
authorized by this verification item. If a suitable device/client test cannot
be performed, retain the explicit runtime-unverified status at delivery.
