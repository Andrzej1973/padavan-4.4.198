# WR1200JS Wi-Fi capability policy checkpoint — 2026-10-20

The live #474 audit found wl_txbf=1 while wl_txbf_en=0, generated TXBF values
zero, and CONFIG_MT76X2_AP_TXBF_SUPPORT disabled. The previously local TXBF
policy is now prepared for publication: hide the unsupported control, remove
its accepted HTTP variable, keep defaults off and check the exact kernel config
and final ROMFS. It does not change the live router or remove shared driver code.

Source validation used the pinned source revision
c25283e915a2a00a763774dd255b14aff997285e: real web_ex.c, variables.c, defaults.c,
and Advanced_WAdvanced_Content.asp plus the repository WR1200JS board config.
The preparation script had incorrectly looked for the source ASP directly under
trunk/user/www. It now uses the actual n56u_ribbon_fixed subdirectory. Applying
it to the pinned-source fixture passed.

A simulated final ROMFS assembled from that transformed page passed the image
policy checker. Negative variants separately exposing row_txbf, accepting the
HTTP field, and enabling the kernel option were all rejected. These are local
source/fixture results, not a newly compiled or installed firmware result.
Normal CI now prepares the policy before the build and checks final ROMFS with
an uploaded wr1200js-wifi-capabilities report. That CI result remains pending.

## KVR source evidence and remaining work

The same manifest now records current-build 2.4-GHz K/R/WNM exclusions and
5-GHz k/r runtime-unverified status. These additional entries explicitly set
policy_enforced=false: only TXBF is enforced by this transform. Do not claim
that the KVR controls have been corrected merely because the manifest exists.

The live kernel and WR1200JS board config agree on disabled
CONFIG_MT7603E_DOT11K_RRM_SUPPORT, CONFIG_MT7603E_WNM_SUPPORT and
CONFIG_MT7603E_DOT11R_FT_SUPPORT. Pinned mt76x3_ap/Makefile selects the RRM,
WNM and FT object groups only when those options are enabled. Saved flags cannot
activate absent object code. A future source extension is not ruled out.

For 5 GHz, CONFIG_RT_DOT11K_RRM and CONFIG_RT_DOT11R_FT select RRM/FT objects
and defines in mt76x2_ap/Makefile. WNM source files exist, but this Makefile has
no wnm.o selection or WNM define; the operational 802.11v path is unproven.
Runtime management-frame inspection and compatible client acceptance remain
necessary for k/r as well. Full FT acceptance needs an appropriate second AP,
matching mobility-domain/key configuration and a compatible client.

The next KVR implementation must reconcile controls and actual per-band code,
backend acceptance and generated records. Preserve saved data and other boards;
do not equate dropping a client or an active Band Steering daemon with FT.
Duplicate KVR generator records were corrected separately in d424db5.
