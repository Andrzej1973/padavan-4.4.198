# IoT beacon/TIM producer lifetime — host contract, 2026-10-27

The isolated candidate is not ready for the firmware image. In its
`ap/ap_connect.c`, `APUpdateBeaconFrame` takes `BeaconPkt` near the start of
the function and performs a long frame build before its final hardware
kickout. In `ap/ap_nps.c`, `RT28xx_UpdateTimToAsic` takes `TimPkt` before
`BcnRingLock`. `MBSS_Close` revokes beacon intent under that lock, but it does
not wait for a producer already using either pointer. A simultaneous zero DMA
and TxS snapshot therefore does not prove that buffer deinit is safe.

`tools/iot/beacon-producer-gate.h` now models the required per-BSS contract:
admit a generation before packet-pointer access, revoke admission under the
same lock used for final submission, wait outside that lock for active
producers to finish or cancel, and reject reopen until the old generation
drains. `tools/iot/check-beacon-producer-gate.c` covers a close racing with
preparation, blocked late submit, blocked early reuse and generation checks.

Verified locally: GCC strict C11 (`-Wall -Wextra -Werror -pedantic`) syntax
and executable test passed. This is a host-only model. The candidate kernel
does **not** yet contain the producer pin, drain wait, or the deferred
recovery/PCI release gate. The model also does not prove DMA, TxS or hardware
late-report quiescence. No driver, image or router state was changed.

Next binding step: wrap all beacon and TIM producer entry paths so every
return releases the pin; put begin/revoke/final-submit checks under the
appropriate shared lock; drain before `wdev_bcn_buf_deinit` and TIM teardown;
then verify lock ordering, callback lifetime and the PCI remove failure path
with an isolated MIPS compile and targeted fault tests before any image gate.
