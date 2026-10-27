# Ljzkirito PPP patches and build selector: target-tree comparison — 2026-10-27

## Scope and provenance

- Donor: `Ljzkirito/openwrt-packages` at `e4f4d68e32130c6a5d9c318ca09ed8ed39bd9c06`, `ppp/patches/{207,330,340}*.patch`.
- Actual firmware base: `vipshmily/padavan-4.4` at pinned `c25283e915a2a00a763774dd255b14aff997285e` in `.github/workflows/build-padavan-4.4-wr1200js.yml`. Inspected `trunk/user/pppd/pppd/{lcp.c,sys-linux.c}` through the GitHub API at that commit. The repo does not vendor this full source tree.
- Board-selector donor: `Ljzkirito/Padavan-Build` at `910079d16d4ed9d284682412516a3079e16e250e`; compared with our `boards.json`, `tools/board-catalog.py` and `.github/workflows/build-multiple-boards.yml`.
- This is a source comparison. No target compilation, PPP link test or on-device route test was run.

## Patch-by-patch decision

| Donor patch | Actual pinned Padavan code | Decision |
| --- | --- | --- |
| `330-retain_foreign_default_routes.patch` | `cifdefaultroute()` already assigns `rt.rt_dev = ifname` before `SIOCDELRT`. | Already present. Do not apply again. The claimed route-ownership protection is source-level, not a new runtime result. |
| `207-lcp_mtu_max.patch` | `lcp_up()` already calculates `mtu = MIN(ho->neg_mru ? ho->mru : PPP_MRU, ao->mru)`, uses `netif_set_mtu(... MIN(mtu,mru))`, then passes `mtu` to `ppp_send_config()`. | Already present. Do not apply again. |
| `340-populate_default_gateway.patch` | `sifdefaultroute()` sets `rt.rt_dev = ifname` and `RTF_UP` but does **not** set `rt.rt_gateway` to the peer or `RTF_GATEWAY`. | Only potentially new PPP/PPPoE behavior. Defer implementation to the WAN stage, after IoT. First identify a real consumer that needs the peer gateway and compare route output before/after. Test `SIOCADDRT`, reconnect, multi-WAN/default-route ownership and rollback on a recoverable target; run a MIPS build and final-image checks. Do not change the live WAN based on this source comparison. |

The current device evidence in `DEVICE-READONLY-AUDIT-2026-10-14.md` records DHCP WAN (`eth3`), not PPPoE. Thus patch 340 has no demonstrated benefit for the currently observed uplink. It might matter for a future PPPoE provider or route consumer, but a source-level omission alone does not establish a defect.

## Board selector decision

Our repository already has explicit `workflow_dispatch` choices (`all-supported`, `wr1200js`), a `boards.json` catalog, validation of configuration paths and duplicate IDs, and a gate rejecting boards without a verified recipe. WR1200JS is enabled; Mi Mini and Mi 4 remain pending. The donor's broad model/toolchain selector does not supply a validated WR1200JS configuration or a safer board gate. No selector code is worth importing now. For a future board, add a tested recipe and image evidence to our catalog rather than copying donor choices or enabling pending boards.

## Acceptance boundary

No production code, workflow, firmware image or router settings changed. The comparison corrects the earlier list of three *candidates*: two are already integrated in the pinned source, and one remains conditional. Revisit patch 340 only if PPPoE/default-gateway consumers make its benefit concrete and the WAN-stage checks pass. Check component patch licensing/attribution before copying any code.
