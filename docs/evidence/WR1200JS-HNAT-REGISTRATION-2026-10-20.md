# HNAT Wi-Fi registration source trace — 2026-10-20

Status: source evidence only; no router writes or packet-path change.
Pinned donor revision: `c25283e915a2a00a763774dd255b14aff997285e`
in `vipshmily/padavan-4.4`. Paths below are under
`trunk/linux-4.4.x/drivers/net/`.

## Radio command and hook effects

Both `wireless/mediatek/mt76x2/ap/ap_cfg.c:1775` and
`wireless/mediatek/mt76x3/ap/ap_cfg.c:12065` implement
`set_hnat_register`, exposed as `hw_nat_register` only under
`CONFIG_RA_HW_NAT_WIFI_NEW_ARCH`. The handler parses the integer and walks
all populated `wdev_list` slots, not only the main interface used to send
`iwpriv`. With both hook pointers present and CONFIG_RA_NAT_NONE absent,
nonzero calls the register hook and zero calls unregister for each wdev.
It returns TRUE even if the hooks are absent: command success alone does
not prove registration changed. Neither handler checks hook outcome; the
hook signatures return void.

In `ethernet/raeth/mtk_hnat/hnat_nf_hook.c:1533`, registration adds or
reattaches an external-device entry and holds the device in wifi_hook_if.
At :1579 unregistration removes wifi_hook_if membership, releases that
reference and calls extif_put_dev. The latter (:138) clears the ext_if
entry's device pointer and releases its reference; the named slot remains.
Consequently get_index_from_dev (:80) returns zero for that device after
successful removal, and get_dev_from_index (:93) cannot resolve its old
act_dp through the cleared slot.

Unregistration itself does not call foe_clear_all_bind_entries.
NETDEV_GOING_DOWN (:229) does call it, but a mode change on an interface
that stays UP does not itself establish that this notifier ran. Conversely,
NETDEV_UP (:223) calls extif_set_dev, which can reattach a cleared named
slot independently of the radio's explicit registration command. This is
a concrete lifecycle gap to examine, not proof that it caused the retained
981 drops in firmware #474. Existing bound entries, notifier order and
source-to-live-image identity remain unverified.

## Next acceptance work

Trace mode-change ordering against interface UP/DOWN and module unload/load;
verify the exact transformed source of the shipped module; then design a
scoped correction covering stale FOE entries and device reference lifetime.
Do not merely suppress the warning or remove IS_EXT based on this trace.
Keep the owner's manual mode1 Wi-Fi trial and mode2 factory policy.
No full firmware compilation was started locally. Existing CI #498 remains
independent; its outcome cannot validate HNAT runtime behavior.

## Pinned source SHA256

- `mt76x2-ap-ap_cfg.c`: `d0a288c7a7401213cfd9bcd5fcfb09945627b6fe1e25b892c9a73561691454b4`
- `mt76x3-ap-ap_cfg.c`: `a53b9df978299c68e3aafd4a1f5a7b50d7e52844c34a73dec427aba7b23ba905`
- `raeth-hnat_nf_hook.c`: `977cbcadfe7bacd540133aa47e4379666f1d3207eaf875723e9ada0f7c1ec49c`

## RC ordering and FOE cleanup boundary

Pinned `trunk/user/rc/net_wifi.c:36` executes ifconfig first, then sends
hw_nat_register on an UP request when hw_nat is loaded. The repository
preparation changes the register value to mode==1. Thus the normal managed
UP path follows NETDEV_UP reattachment with the explicit mode policy; the
mere existence of NETDEV_UP reattachment is not proof of a persistent bypass.
The helper does not condition this command on a successful ifconfig result.

`reload_nat_modules` in pinned `trunk/user/rc/net.c` compares
is_hwnat_loaded() with is_hwnat_allow(), may unload the module before its
registration block, and then loads it when needed. The current preparation
reapplies both radio registrations even when the module was already loaded.
The exact meanings of the two shared helpers and transformed live #474 RC
remain to be checked before classifying a mode transition as unload/reload.

Importantly, module removal is different from the radio unregister command:
`ethernet/raeth/mtk_hnat/hnat.c:570` calls hnat_disable_hook (:391), which
invalidates bound FOE entries and clears the HNAT cache. Therefore the earlier
observation that radio unregister has no FOE flush must NOT be generalized
to every mode transition. A proven module unload has a cleanup path.
`foe_clear_all_bind_entries` in hnat_nf_hook.c:181 also invalidates ALL bound
entries and temporarily selects CPU forwarding, rather than selectively
clearing one Wi-Fi device. Adding it unconditionally to each radio/wdev
unregister would have broader performance effects and is not justified by
this evidence.

No tests were added or run for this source-reading step. Existing earlier
predicate experiment evidence remains bounded to its own 64 cases.
- `pinned-net.c` SHA256: `668c4d716f241e7c383d8717ab49a62b060ca8a684b6778ef94c65ba4c247a3d`
- `pinned-net_wifi.c` SHA256: `98bbe9cfca0af35be4ddb82742022b90cc51c2f7b34834e627ee6c5f2187dc69`
- `pinned-hnat.c` SHA256: `4a332f42226572965aaf679144bea5ae24b03811510b1aec97d131c9e1297afc`
