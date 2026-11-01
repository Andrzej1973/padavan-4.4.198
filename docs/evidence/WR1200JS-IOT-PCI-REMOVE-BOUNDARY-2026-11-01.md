# PCI remove cannot refuse driver-core unbind

Pinned source: c25283e915a2a00a763774dd255b14aff997285e.

`drivers/pci/pci-driver.c:429` invokes the VOID driver remove callback.
After it returns, lines432-433 release platform IRQ routing and clear the
PCI driver pointer; line455 drops the PCI device reference. Independently,
`drivers/base/dd.c:683-689` calls the bus remove, then releases devres and
clears device driver/data. Physical removal can subsequently free PCI resources
in `drivers/pci/remove.c:44`. These are distinct paths; do not claim every
resource is freed on every ordinary unbind.

The candidate's early returns preserve its own memory/netdev references but
cannot veto these core actions. A module or netdev reference alone does not
prove PCI mappings, IRQ routing, callbacks or DMA remain usable afterward.
The new bounded pre-retirement retry improves a continuation opportunity;
it does not solve terminal detach when the retained operation still fails.

Required next implementation: separate ordinary radio/interface close (which
may refuse and remain attached) from unavoidable bus removal. Before returning
from bus remove, fence all new access, stop hardware/DMA/IRQ producers using
verified device-specific operations, join callbacks, and detach or quarantine
software owners without future hardware access. Preserve exact reference
accounting. Audit physical loss separately, where MMIO cannot be assumed safe.
Do not add unbounded waits, fake success, forced frees, kernel-core vetoes or
relax guards merely to pass removal. Prove ordering and failure paths against
actual source, target build and separately authorized device tests.

Status: source-confirmed production blocker, not an observed device crash.
No router changes or PCI unbind experiments were performed.
