# Private OFF-to-ON profile generation

`radio-on-generation.c` exclusively borrows a captured ON admission, retaining
its busy flag throughout generation, verification and rollback. This blocks
capture-only cancellation. The desired request is copied before invoking the
profile checker, and wiped on failed admission. The existing SDK generator and
snapshot/journal/scanner/restore helpers perform the actual file operations.
Reload0 skips the generator; reload1 attempts generation once. Successful output
must match the owned file generation and the copied desired credentials. Partial
failure and invalid output enter checked restoration. Foreign file replacement
retains the baseline instead of overwriting another writer. Repeated calls do
not regenerate. Abort before Main UP enters the same restoration path.

The focused host fixture uses the actual admission, signal fence, profile file,
journal and scanner, with SDK generator and mode/physical DOWN actors. C11
-Werror ASan/UBSan checks passed on 2026-11-15 for reload0/1, mismatched desired
request and credential wiping, partial/invalid output restoration, foreign inode
retention, repeat verification and explicit abort. Pending shutdown retains the
owner without generation. Test-only teardown is explicitly distinct from a
production retirement path; TemporaryDirectory removes scratch on exit.

This module issues no Main UP, does not consume the OFF receipt, and provides no
post-UP rollback or final guard retirement. Pending shutdown cleanup requires
integration with the outer controller; this component alone retains it. Its
source is not yet staged into the target or bound to RC. The complete reversible
physical OFF/ON entry remains unbound. Host results are not MIPS/image/device
acceptance. ACK protection and ordinary ra2 lifecycle remain unchanged.
