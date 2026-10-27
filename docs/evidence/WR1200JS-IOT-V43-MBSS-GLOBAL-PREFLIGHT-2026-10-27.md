# WR1200JS IoT v43: MBSS global preflight candidate — 2026-10-27

Source: local isolated v42 driver prepared from pinned Padavan
`c25283e915a2a00a763774dd255b14aff997285e`.

`tools/iot/prepare-mbss-global-preflight.py` creates a **new isolated**
candidate tree. It injects a check at the start of `MBSS_Remove()`, before the
first beacon or child netdev is freed. Under the shared transition lock, the
check requires radio retirement, no registration in progress, no active TX,
matching non-null child netdev count and published MBSS registry count, every
acquired MBSS at checked DOWN stage 4, and a PCI work-joined receipt. The
receipt is initialized false and has **no producer** yet; the candidate cannot
pass real PCI removal until a reviewed owner binds that receipt.

Verification performed locally:

1. The preparation script succeeded against the isolated v42 tree and wrote a
   manifest with hashes of the five changed/generated driver files. The
   resulting source places declarations before the new preflight call.
2. `check-mbss-global-preflight.c` compiled and executed with host GCC C11,
   `-Wall -Wextra -Werror -pedantic`. It rejects live/closing references,
   incomplete checked DOWN, mismatched counts, unjoined work, in-flight
   registration/TX, non-retiring radio and unknown ownership.
3. `prepare-mbss-global-preflight-check.py` extracted the **generated driver
   source** into an injected host fixture. That fixture compiled and ran with
   the same strict flags. With two BSS, an open or incompletely closed second
   BSS causes `MBSS_Remove()` to fail before *any* remove, beacon deinit,
   detach or free call; both closed BSS pass the injected success path.

Limits: this is not installed in the ordinary image, not MIPS-compiled, and
not exercised on the router. The preflight cannot make an already-started
removal failure atomic, and it does not solve `rt_pci_remove()` ignoring child
exit failure before freeing adapter/MMIO. The PCI owner must set the work
receipt only after all close/recovery owners join outside locks and RTNL,
then handle every terminal failure without unsafe free. It must also fence
the pre-registration construction window before treating the netdev count as
stable. Only after those bindings, target compilation and fault injection can
this become a production release gate.

## Construction-window follow-up

The source review found `MBSS_Init()` stores `wdev.if_dev` before its call to
`wr_iot_netdev_attach_checked()` increments the existing registration counter.
The isolated candidate now acquires a construction lease under
`wr_iot_transition_lock` before that first store, increments the same
registration-inflight count and releases it on every normal/early exit. The
lease refuses retirement/PM overlap and concurrent MBSS construction. The
preflight also rejects an active lease. The generated source contains the
begin call at `MBSS_Init` entry and the end call at its common exit.

The host helper fixture verifies lease acquisition, duplicate refusal,
retirement overlap refusal, count release and wakeup. The generated-source
fixture still verifies only the preflight and `MBSS_Remove()` body; it does
not execute the full vendor `MBSS_Init()`. Both strict host fixtures passed.
No target compile or device test establishes this follow-up yet.
