# Current MBSS admission and close fixtures

The generated candidate changed after the older host fixtures: BSS observation
and vendor-count reconciliation are now distinct; begin-close captures MBSS
family, generation and prior radio state; ticket retirement wakes waiters.
The fixtures now model those interfaces explicitly instead of bypassing
count ownership or finishing an already retired ticket twice.

Admission models successful virtual-UP count acquisition and independent
BSS readback. A reset during raw UP exposed a READY phase with readiness
invalidated; `virtual-open-claim.h` now demotes that phase to UNVERIFIED while
retaining the interface reference for checked recovery. Failed BSS readback
is also checked without treating the owned reference as proof of readiness.

Full source candidate `.iot-local-check/full-queue-20261029e` was regenerated.
Admission compiled and passed against its final generated headers. The
MT_MAC/PCI open-close fixture has an owned MAIN record matching its initial
count, plus the separate MBSS record. Pending/fault DMA and TxS observations
retain ownership; successful IoT close preserves the MAIN record/count.
The last-close fixture models the current ticket-wait wake, checks one wake
on success and no additional wake on failure.

Actual checks: strict optimized host GCC C11 compilation and execution passed
for admission, last-close, MT_MAC/PCI open-close and its
CONFIG_RA_HW_NAT_WIFI_NEW_ARCH variant. Targeted diff check passed. These are
injected hardware/OS fixtures; they do not prove HWNAT traffic, hardware BSS
readback, late TxS report retirement, MIPS compilation or live-device behavior.
No firmware image or router state was changed.
