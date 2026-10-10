# RSSI monitor read integration contract

Status: implementation pending. Existing candidate records and kernel snapshot wrappers do not provide a userspace query or a complete WebUI RSSI monitor.

## Required driver query

- Read-only, explicitly versioned private query; verify command-number availability against both actual driver dispatch tables before assigning it.
- Require administrator capability in the kernel handler. HTTP access remains behind the existing router authentication boundary.
- Use fixed-width fields and explicit byte encoding. Never expose native C structure padding or kernel addresses.
- Validate version, input size, reserved fields, radio, cursor and requested capacity before acquiring the observer lock. Limit each response to 64 records.
- Copy records and sequence/overwrite metadata into a bounded kernel buffer under the observer lock. Release the lock before encoding or copying to userspace. Never acquire the station-table lock from the observer lock.
- Querying never consumes records, changes kick thresholds or changes driver decisions. Invalid requests leave observation state unchanged.
- Adapter lifetime must remain valid for the whole query. Verify actual ioctl dispatch and teardown synchronization before installing the handler.

## Restart and history semantics

A cursor alone cannot identify an adapter instance: after restart its sequence may become smaller or overlap a previous instance. Export and validate an adapter-instance session as well as radio and sequence. Session mismatch must be explicit; the collector starts a new history segment and retains a gap indicator. Do not infer continuity from matching MAC addresses.

The collector must report overwritten records, unavailable queries, session changes and rejected responses separately from client events. Collection is bounded and read-only; no scans or additional driver daemon are required.

## Event meaning and acceptance

Keep RSSI decision, allocation failure, frame submission and matched station-entry clearing separate. Entry clearing does not prove reception of the deauthentication frame, reconnection or a roam. Passive association observations remain separate evidence.

Required tests cover malformed/oversized input, privilege rejection, recycled station identity, cursor/session mismatch, ring overwrite, repeated reads without consumption, concurrent append/read and adapter teardown. Compile the complete handler in both real driver modules, verify image inclusion, then test on the actual router with a separate client. Current firmware boot and RSSI runtime behavior remain unverified.

## Pinned Linux dispatch evidence

Source `c25283e915a2a00a763774dd255b14aff997285e`, `trunk/linux-4.4.x/net/wireless/wext-core.c`: `wext_ioctl_dispatch` acquires RTNL around `wireless_process_ioctl`; the latter can call `netdev_ops->ndo_do_ioctl` after checking device presence. `wext_permission_check` requires `CAP_NET_ADMIN` for set commands and selected encoding reads, rather than every read. The new RSSI handler therefore requires its own explicit administrator check. RTNL coverage of this entry point alone does not prove all MediaTek adapter release paths are synchronized; that driver lifetime audit remains pending.

## PCI removal audit

For both `mt76x2` and `mt76x3`, pinned `os/linux/pci_main_dev.c` calls `RtmpPhyNetDevExit` before `RtmpRaDevCtrlExit`; the latter in `common/rtmp_init.c` ends with `RTMPFreeAdapter`. `RtmpPhyNetDevExit` removes APCLI, WDS and MBSSID interfaces and unregisters the root interface. In the inspected `ap/ap_apcli.c`, `ap/ap_wds.c` and `ap/ap_mbss.c`, each existing virtual interface is detached between `RtmpOSNetDevProtect(1)` and `(0)` before freeing it. In `os/linux/rt_linux.c`, protection maps to RTNL and detach calls `unregister_netdevice`.

These findings establish the inspected PCI remove ordering relative to synchronous WEXT ioctl dispatch. The new query must finish copying before returning and must not retain adapter pointers or schedule asynchronous reads. Alternate bus, registration-error and configuration-dependent removal paths still require checking against the actual WR1200JS module configuration before production integration.
