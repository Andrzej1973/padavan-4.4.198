# WR1200JS build #535 — beamforming controls removed

Owner decision 2026-10-22: beamforming is not usable on this unit; exclude it
from the WebUI. Device not flashed.

## Build

- Run: 39822729930, build **#535**, head `abfd645`.
- Artifact: `WR1200JS_4.4.198.9-535_e8a8cf98.trx`, 12 842 033 bytes.
- SHA256: `72d98244bcaed35798bf2ac50a02f2feb3f67e623f0caa9a5932b62f01ffd81d`.

## ROMFS proof

Extracted `/www/Advanced_WAdvanced_Content.asp` (27 580 bytes):

| Token | Count |
| --- | --- |
| `txbf` | 0 |
| `row_txbf` | 0 |
| `mumimo` | 0 |
| `row_mumimo` | 0 |

`/www/vpncli.asp` still contains `wr_vpn_profile_rows` ×2, so the VPN profile
table is unaffected.

## What changed

- TXBF was already removed by the existing board capability policy
  (`has_5g_txbf = 0`, no `row_txbf`, no `wl_txbf` form variable, default off).
- MU-MIMO was the remaining beamforming-family control. `abfd645` removes
  `row_mumimo` and its visibility block and extends the final-image verifier.

## Why

Factory TXBF calibration regions `0x01A0` and `0x81A0` are 33/33 bytes `0xFF`
in this unit (confirmed against the upstream DTS factory layout), the kernel
build has `CONFIG_MT76X2_AP_TXBF_SUPPORT` disabled, and MT7612 here is a 2x2
Wave 1 radio without MU-MIMO. Showing either control would be misleading.

## Limits

Runtime page behaviour on the router is not verified: the device still runs
the 2026-10-18 build. Acceptance requires flashing this image (separate owner
approval) and following `docs/status/WR1200JS-RUNTIME-ACCEPTANCE-PLAN.md`.
