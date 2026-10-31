# IoT PCI recovery drain, isolated v24b — 2026-10-28

The isolated candidate `.iot-local-check/mt7603-pci-recovery-drain-v24b-20261028`
was composed from verified v23b; its 69-file manifest records the output
hashes. It adds the host PCI retirement contract to the driver candidate,
initializes its owner in adapter setup, and starts a bounded recovery drain
in `rt_pci_remove` after fencing radio admission but before requesting stop.
The drain joins one delayed-reaper instance at a time, joins main work,
reaps a completed owner, and checks for another pending or running reaper.
It records `DRAINED` only after the deferred-owner count reaches zero.

Checks performed on Windows:

- Strict C11 `check-pci-recovery-drain.c`: pass for completion after a second
  instance, no next instance, and bounded self-rearm.
- `check-main-readiness-verify-candidate.py`: pass; explicitly reports PCI
  release gate unbound.
- `check-virtual-if-call-coverage.py`: pass for the five caller families and
  checked netdev attach paths.
- `check-pci-recovery-drain-candidate.py`: pass for all 69 hashes and the
  reviewed retire → drain → stop → join source order.
- Local Windows command discovery found no MIPS GCC on PATH. `wsl.exe`
  exists, but `wsl --list --quiet` exited 1 and displayed usage rather than
  an installed distribution list. No usable local target compiler was
  established by these checks.
- No MIPS target compile, complete firmware build, image or device test.

The [upstream Linux 4.4.198 workqueue source](https://raw.githubusercontent.com/gregkh/linux/v4.4.198/kernel/workqueue.c)
shows that `flush_delayed_work` covers only the last queued instance. The
candidate uses a bounded per-instance loop for that reason. This is not
verification of any vendor modifications to the target kernel.

**Unresolved release blocker:** if the owner remains after the bounded drain,
the PCI remove callback still returns with live adapter/netdev ownership and
no independent finalizer. An uncertain stage-1 preclose must not be replayed.
The candidate therefore remains nonproduction; `production_installed=false`
and `pci_release_gate_bound=false`. Do not flash or advertise IoT readiness.
