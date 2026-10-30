# Auxiliary close candidates73/74: publication and paused handoff

Sol publishes only the four isolated preparer/test scripts named below.
They do not install production patches or enable IoT in a firmware image.
All other accumulated tracked/untracked changes remain local and preserved.
Project work is paused at the owner's request pending renewed limits.

## Published behavior

- prepare-aux-remove-close-guard.py: pinned APCLI/Monitor remove functions
  explicitly close and require registry IDLE before unregister/free. A failed
  ndo_stop must not be hidden by unregister. Partial failure retains allocation.
- prepare-aux-remove-close-check.py: extracts both actual remove bodies and
  actual registry close-phase helper. Host assertions cover mark refusal,
  close refusal before detach/free, and existing success ordering.
- prepare-aux-family-close-result.py: pinned APCLI/Monitor ndo_stop wrappers
  propagate family ioctl failure before HNAT deregistration, virtual DOWN and
  module pin release. No retry/replay policy is introduced.
- prepare-aux-family-close-result-check.py: extracts actual wrappers and checks
  family failure, DOWN failure and success, with/without HNAT.

The preparers require exact source hashes and a new separate output directory.
Use candidate73 as input to candidate74; their pinned inputs describe the
reviewed local source lineage. Raw vendor trees and generated binaries are
deliberately not part of this commit. This publication alone is not a complete
candidate generator or a production overlay.

## Verification

Strict host compilation used GCC -std=c11 -O2 -Wall -Wextra -Werror.
The actual-helper remove fixture and both family-close base/HNAT fixtures
passed; all three executables were rerun before publication. Four scripts
also passed Python AST parsing. RTNL, locks, ioctls, HNAT, free and virtual
DOWN operations are mocked: these are extracted control-flow tests, not
kernel concurrency, MIPS ABI, target module, firmware image or runtime proof.

## Resume here

Last fully reproduced local candidate is70:65 preparers/582 files identical
to its tested incremental tree,72 host variants plus a separate injected-exit
variant. Local main preparer includes73; full73/74 replay is still pending.
Neither successful remove nor IDLE proves callback retirement. Next implement
shared callback retirement evidence and retained-family retry/completion,
then root/final-work/physical PCI release receipts. APCLI/Monitor family
effects cannot simply reuse WDS retry stages. Do not blindly replay dev_close
after a failed ndo_stop: IFF_UP may already be clear.

Read local PROJECT_STATUS.md and CODEX_HANDOFF.md for preserved details before
resuming. Sol remains the single writer; no role transfer is implied. No router
change, flash, reboot, full firmware build or manual workflow dispatch occurred.
