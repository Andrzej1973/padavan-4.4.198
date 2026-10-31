# Kernel4.4.198 netdev retirement — pinned source evidence

Read the existing local exact-source archive recorded in `sources.lock.json`:
`../firmware-source-backup/padavan-4.4-c25283e-git-exact.tar`, donor revision
`c25283e915a2a00a763774dd255b14aff997285e`. No network fetch or full source
extraction was needed. The archive Makefile reports VERSION4/PATCHLEVEL4/
SUBLEVEL198. Three files were copied into a new scratch directory with exact
member names and SHA256 in `kernel-netdev-retirement63-20261030/manifest.json`.
The entire archive hash was not remeasured in this step.

`check-kernel-netdev-retirement.py` verifies those exact file hashes and source
ordering against candidate62. It passed and wrote
`.iot-local-check/kernel-netdev-retirement63-proof.json`.

Confirmed code path:

1. `net/core/dev.c:7429`, unregister_netdevice_queue: rollback then net_set_todo.
2. `net/core/rtnetlink.c:79`, rtnl_unlock: calls netdev_run_todo before returning.
3. `net/core/dev.c:7094`, netdev_run_todo: unlocks RTNL, drains RCU callbacks,
   executes final unregister notification, then waits netdev references.
4. `net/core/dev.c:7020`, netdev_wait_allrefs: loops until accounted references
   reach zero, potentially waiting indefinitely. It cannot be replaced by an
   arbitrary sleep or timeout receipt.
5. NETREG_UNREGISTERED is assigned before wait_allrefs; checking that state
   alone is not proof that the wait completed.
6. Driver RtmpOSNetDevProtect(0) calls rtnl_unlock. In the inspected WDS path,
   its return follows Detach and precedes the retained registry receipt.

This supports a kernel-accounted-reference completion receipt at that exact
returned-unlock seam. It does not establish vendor raw-pointer ownership,
arbitrary driver work/timers, hardware reports or DMA retirement. No redundant
generic callback counter should be introduced merely to reproduce what this
kernel already waits for. Actual vendor paths must still be audited/joined.

An initial checker matched an earlier Protect(0) in the close-refusal branch;
the checker now identifies the unlock specifically after the actual Detach.
No driver failure or kernel execution occurred in that initial checker run.

Additional lifetime issue to resolve: RtmpOSNetDevDetach frees its dynamically
allocated netdev_ops before the subsequent returned RTNL unlock/reference drain.
The later seam proof cannot justify that earlier allocation release. Review
deferred ops ownership and all creation/probe/free paths together to avoid
double free; this audit alone does not prove an actual use-after-free occurred.

Next preserve allocation until the proved kernel seam and separately bind
vendor callback/report retirement before family completion and adapter release.
No driver/kernel source change, target/firmware build, runtime acceptance,
router changes, dispatch, commit or push in this step. Latest full replay58.
