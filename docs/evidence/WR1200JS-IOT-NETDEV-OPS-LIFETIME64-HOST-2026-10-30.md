# Private netdev_ops lifetime64

Pinned `prepare-netdev-ops-lifetime.py` creates
`.iot-local-check/netdev-ops-lifetime64-20261030` from62. It changes six files:
rt_linux.c, pci_main_dev.c, ap_mbss.c, ap_apcli.c, ap_wds.c and
sniffer_radiotap.c. The kernel source semantics audit63 is not a transform.

The inspected driver assigns dynamically allocated, private per-netdev ops in
RtmpOSNetDevCreate. Detach now unregisters without freeing those ops. The common
RtmpOSNetDevFree releases ops and clears the pointer before free_netdev. All
reviewed duplicate failure-path frees were removed, including allocation/name,
MBSS, AP-client, WDS, Monitor and PCI probe paths. Unregistered device creation
failures also use the same owner; NULL ops require no allocation release.

Registered callers must complete the returned RTNL unlock/ref drain before
Free. This prerequisite is not enforced for arbitrary external callers by a
new status API in this step. Existing audited family removal call sites place
Free after RtmpOSNetDevProtect(0). WDS retains its allocation and ops while its
vendor callback recovery remains incomplete. Per-entry vendor/raw callbacks
and adapter release still require their own proofs.

`prepare-netdev-ops-lifetime-check.py` extracts actual Create/Detach/Protect/Free
functions. Strict GCC C11/O2/Wall/Wextra/Werror tests passed:

- Ops remain allocated during Detach and modeled RTNL-unlock/ref draining.
- Final Free releases ops once, clears its pointer and frees the device.
- Unregistered failure with allocated ops and a NULL-ops failure clean up once.
- Actual Create device-allocation, ops-allocation and name-allocation failures,
  plus successful Create followed by Free, preserve expected ownership counts.
- Source assertions find no old duplicate ops frees in the other five files.

The first expanded fixture compilation missed the synthetic INT typedef; it
was corrected and the final fixture compiled/executed successfully. Driver
source was not changed to accommodate that fixture issue.

Three selected suite checks passed in `netdev-ops-lifetime64-targeted/result.json`:
ops lifetime plus preceding PCI work-join/snapshot regressions. The exact
kernel/RTNL source verifier63 also passed against64. Actual kernel reference
counting, allocation primitives and callbacks remain modeled, not runtime tested.
No MIPS module/OS_ABL link/firmware build, physical device changes or acceptance.
Step64 is in the chain; fresh full59–64 replay remains pending. Latest full58.
No dispatch, commit or push. Next vendor callback/reference retirement and
family completion, cold probe ownership and full candidate regression.
