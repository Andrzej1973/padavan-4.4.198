# IoT PCI drain queued-callback gate, isolated v24c — 2026-10-28

Source inspection found a release hazard in v24b: the drain contract returned
`COMPLETE` as soon as `deferred_owners == 0`, even if the delayed reaper still
had another queued/running instance holding the adapter pointer. The v24c
contract requires both zero deferred owners and no next reaper instance.
When a next instance exists, it is joined in another bounded round; an
exhausted loop returns `STALLED` and does not authorize release.

The isolated composition is
`.iot-local-check/mt7603-pci-recovery-drain-v24c-20261028` with its 69-file
SHA-256 manifest. It is derived from the verified v23b source using the
reviewed preparation script and updated `pci-retirement-owner.h`.

Checks actually run on Windows:

- GCC C11 `-Wall -Wextra -Werror` host fixtures
  `check-pci-retirement-owner.c` and `check-pci-recovery-drain.c`: pass,
  including a queued callback after the owner count reaches zero and a
  bounded self-rearm case.
- `check-pci-recovery-drain-candidate.py`: pass, 69/69 hashes and
  retire/drain/stop/join source order.
- `check-main-readiness-verify-candidate.py`: pass; PCI release gate
  explicitly remains unbound.
- `check-virtual-if-call-coverage.py`: pass for five caller families and
  checked registration paths.
- `git diff --check` on the three edited source/fixture files: pass.

These are host/source checks only. The workqueue and hardware behavior are
mocked; no target MIPS compilation, firmware image or router runtime test
was performed. The one-shot PCI remove callback still has no independent
finalizer if an owner remains stalled after the bounded drain. Keep v24c
nonproduction and do not install it in the firmware until that lifetime path
and the PCI release gate are resolved.
