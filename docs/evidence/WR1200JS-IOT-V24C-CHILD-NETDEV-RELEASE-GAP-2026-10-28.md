# IoT v24c child netdev release gap — 2026-10-28

Source review only, in isolated
`.iot-local-check/mt7603-pci-recovery-drain-v24c-20261028`.

The checked registration path publishes typed records through
`wr_iot_registry_add_family` in `os/linux/rt_main_dev.c` via
`netdev-registration.inc`. The AP-client, WDS, MBSS and monitor remove loops
all call `RtmpOSNetDevDetach` followed by `RtmpOSNetDevFree`. In this tree,
`RtmpOSNetDevDetach` invokes `unregister_netdevice`; `RtmpOSNetDevFree`
invokes `free_netdev` for Linux 4.4. The four family remove loops do not
call `wr_iot_registry_kernel_done`, `wr_iot_registry_vendor_done` or
`wr_iot_registry_release` after unregister. The only release in the attach
bridge handles a failed registration or publication, not normal removal.

Consequently, a successful family remove can leave a published registry
record pointing at an already freed netdev. The adapter release gate would
reject such a record, but it is not bound to the vendor PCI path. Reporting
family completion from the wrapper alone would therefore be false proof.

The next implementation must retain the exact device and generation through
detach, prove checked close and callback quiescence, record kernel/vendor
completion under the shared lock, and release the registry slot **before**
freeing the netdev. If any proof fails after unregister, the path needs a
retry/finalization owner; a second unregister or a silent free is unsafe.
Apply this per family before binding `wr_iot_children` and PCI release.

No driver installation, target compile, image build or device test was done.
