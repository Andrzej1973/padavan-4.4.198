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

## First isolated binding step

`tools/iot/prepare-mbss-checked-stop-candidate.py` copies a local v40 driver
tree into a new directory and replaces only `MBSS_VirtualIF_Close` with a
call to the checked begin/close functions. It refuses changed legacy anchors,
verifies every other copied source file byte-for-byte, and writes an explicit
manifest with recovery, PCI release, target compilation, production and
runtime all marked false. This is a v41 source experiment, not a release
candidate.

Local execution against freshly regenerated v40 from the tracked v39 tree
verified 58 copied source files and reproduced the same output hash as an
earlier local v40 tree. `python -m py_compile` passed, and the one-file diff
showed the callback replacement and forward declarations only. The output file
SHA-256 is `26478525a4f18fe45e9e97d92d355927c7abb04702a3978636268ee1a96fd20e`.
The preparer rejected the older v39 source before creating an output tree.
No MIPS compilation or fault-injected close test has run for this new binding.
Failure after `wr_iot_mbss_begin_close` retains the close ticket and module
pin. Failure in that admission call has no ticket and retains the open
reference. Linux may mark the interface down in either case, so both paths
need a real recovery owner before this binding may be installed.

The optional Actions input now accepts `v41` and prepares this binding after
the reviewed v40 overlay, then uses the existing isolated MIPS module build.
The manifest is kept beside the driver tree so only driver sources enter the
assembly. Workflow YAML parsed locally; the `v41` target job has not run.
Do not dispatch it while an existing build on the branch is still active.

## Admission-failure recovery contract, 2026-10-27

After #624 and its ABI run passed on published `2216583`, optional IoT-only
v41 run #625 (`40429949035`) was dispatched on that exact SHA. Its result is
pending. This target compilation cannot validate a recovery worker.

The host-only MBSS recovery owner now accepts an `OPEN_ACQUIRED` record while
another radio transition is busy, provided the caller already holds the
netdev and fences adapter release. Its action remains `NONE` until the busy
operation clears, then permits `BEGIN_CLOSE` with the still-owned reference.
The strict C11 host fixture compiled and exited successfully for this case.
This covers the state-machine handoff after a refused close admission; no
`work_struct`, `dev_hold`, scheduling, join or PCI callback binding exists yet.
