# Fallible adapter-free result59 — local preparation only

Pinned preparer `prepare-adapter-free-result.py` creates
`.iot-local-check/adapter-free-result59-20261030` from full58. It changes the
native declaration, OS_ABL function-pointer field and RTMPFreeAdapter definition
from VOID to BOOLEAN. The two existing early exits return FALSE; the terminal
path returns TRUE after adapter/cookie free without dereferencing freed state.
The existing ops assignment remains consistent with the new signature.

All three direct free calls and both controller-exit calls now propagate
refusal: controller returns FALSE; PCI probe returns -EBUSY; PCI/SDIO remove
and SDIO probe stop before their following outer resource operations. This
full-source inventory includes optional SDIO, not an assertion it is enabled
for WR1200JS. It is not yet a recoverable probe-failure retention mechanism.

`prepare-adapter-free-result-check.py` extracts the actual controller body,
ABI field/assignment/macro and four exact caller guards. Both native and
`-DTEST_ABL` synthetic host variants passed GCC C11/O2/Wall/Wextra/Werror.
Refused free stops subsequent modeled unmap/IRQ/cookie actions; success allows
them. The actual free body is source-checked but replaced with a stub during
execution. This is not target ABI/link or complete PCI/SDIO control-flow proof.

The test explicitly observes that existing controller destructors still run
before free is called. A release claim before those destructors is NOT bound.
The source audit now observes zero bare unchecked direct calls and propagated
free result, but continues reporting release unaccepted. Existing early free
failure branches may follow partial lock destruction; blindly retrying them
is unsafe. No retry/recovery guarantee is claimed.

Next: pre-destructor retirement claim and admission fence; distinguish cold
probe unwind from initialized teardown; prove peer/task/callback/registry/DMA
retirement and propagate retained ownership safely. All affected native and
OS_ABL modules require a coherent target rebuild; mixed-module hot replacement
is unsupported. Stage59 is in the preparer chain, not freshly replayed in full.
Latest full replay58. No target/firmware build, router changes, dispatch, commit
or push in this step.
