# WR1200JS IoT v40 close and PCI release gate — 2026-10-26

This is a source-level audit of the isolated v40 candidate. No production
driver, firmware image or router state was changed by this audit.

## Evidence boundary

Optional Actions run #622 (`40387415111`) compiled `mt76x3_ap.ko` for MIPS.
Its `target-compile-result.json` records `target_compiled: true`,
`production_installed: false`, and `runtime_verified: false` on
`b2ec88960a545e67509d5e64b9f78ef580311054`. A compiled, unbound helper
does not establish that Linux calls it or that adapter removal is safe.

## Verified source path

- The v40 preparer copies `tools/iot/mbss-close-checked.inc` into the isolated
  driver, but does not replace the `MBSS_VirtualIF_Close` netdev hook.
  `ap/ap_mbss_inf.c` still assigns that hook and its body still calls the
  legacy `CMD_RTPRIV_IOCTL_MBSS_CLOSE` and `VIRTUAL_IF_DOWN`, discards their
  results and returns zero. `wr_iot_mbss_begin_close` and
  `wr_iot_mbss_close_checked` are present, but not reached from this hook.
- `ap/ap_mbss.c:MBSS_Remove` starts beacon-buffer teardown after removal
  admission, without a proved completed checked close. Subsequent netdev
  detach/free cannot serve as the close result: Linux 4.4 may clear `IFF_UP`
  after an unsuccessful `ndo_stop`, so a second `dev_close` need not call it.
- `os/linux/rt_main_dev.c:RtmpPhyNetDevExit` propagates a failed child removal
  as `FALSE`. `os/linux/pci_main_dev.c:rt_pci_remove` ignores that result and
  then calls `RtmpRaDevCtrlExit` and frees the root netdev. This can release
  an adapter while a child or deferred owner still references it.

## Required binding and verification before image inclusion

1. Bind the checked MBSS close to the actual netdev stop path. Retain the
   exact ticket, netdev and module reference on uncertain or incomplete close;
   do not interpret the `ndo_stop` return value as a kernel-enforced veto.
2. Add an owner that resumes or terminates retained close work even after the
   netdev becomes down. Prove completion and callback/DMA quiescence before
   beacon-buffer teardown and netdev free.
3. Propagate checked teardown for every child family and make PCI removal
   fence admission, join workers, reconcile retained owners and prove the
   adapter-release predicate before `RtmpRaDevCtrlExit`. Audit the separate
   probe-error unwind. A `void` PCI callback cannot safely be repaired merely
   by returning early on failure.
4. Exercise failed and delayed close, reset, driver unload and probe-unwind
   paths in host fault tests, then compile the full target module, inspect
   image inclusion and test main/guest/IoT together on hardware under the
   agreed recovery plan.

Until these checks pass, #622 is evidence of isolated compilation only. It
does not authorize installation of v40 in the released WR1200JS image.
