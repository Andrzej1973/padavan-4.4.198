# IoT MT7603 candidate: PCI probe failure boundary (2026-10-25)

Source reviewed: isolated `.iot-local-check/aux-preclose-v38-20261025`.
No production driver, firmware image or router state was changed.

The probe error labels in `os/linux/pci_main_dev.c:377-401` are reached
before the successful return at line 371. `RtmpPhyNetDevInit` at
`os/linux/rt_main_dev.c:399-462` creates and initializes only the root
netdev; it does not create MBSS, WDS, AP-client or monitor netdevs. The
subsequent `wr_iot_netdev_attach_checked` at
`include/wr-iot-netdev-registration.inc:14-73` calls
`RtmpOSNetDevAttach`. Its failure branch releases the unpublished registry
record. `RtmpOSNetDevAttach` at `os/linux/rt_linux.c:1659-1744` maps a
nonzero `register_netdev` result to failure. The probe then frees the root
netdev and adapter through `err_out_free_netdev` and `err_out_free_radev`.

This trace does not show a **published child interface** on the ordinary
probe-failure route, so the checked child-removal result missing in PCI
`remove` is not directly applicable to that route. It does **not** prove
that partially initialized adapter resources, PCI callbacks, DMA or work
are quiescent at every allocation-failure point. `RTMPAllocAdapterBlock`
performs its own partial cleanup; its interaction with later initialization
still needs target fault-injection coverage.

The production release blocker remains the successful-probe `rt_pci_remove`
path: it ignores the `BOOLEAN` `RtmpPhyNetDevExit` result and frees the
adapter while a retained child or deferred owner may still exist. Next
implementation must provide a single retirement owner for that path, with
checked child completion and work/callback quiescence before adapter free.

## Recovery worker integration recheck, 2026-10-28

The earlier trace describes the candidate **before** a recovery worker is
bound. Once an adapter-owned work item is initialized before publication,
the attach-failure path must join it even though no child netdev was
published. In the reviewed PCI source, `wr_iot_netdev_attach_checked` fails
into `err_out_free_netdev`, then `err_out_free_radev` calls
`RTMPFreeAdapter` directly. It does not pass through `RtmpRaDevCtrlExit` or
normal `rt_pci_remove`. Thus a remove-only join would leave a second adapter
free path unprotected. The source preflight
`tools/iot/check-pci-probe-worker-unwind.py` currently reports both missing
adapter-owned work and missing synchronous join. A future worker binder must
initialize the work before any possible schedule, stop new scheduling and
join on this probe path, and join twice around root unregister on the normal
remove path. The checked close executor must resume the exact retained
ticket after `RTMPInfClose` rather than replay that void preclose call.
