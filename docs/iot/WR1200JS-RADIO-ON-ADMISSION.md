# Private OFF-to-ON admission preparation

The standalone radio-on-admission component captures the current profile under
an outer signal fence and the service guard, using the exact successful OFF
RELEASE receipt retained by RC. It checks router/radio/AP mode, fresh physical
DOWN, profile policy, and post-capture file identity. Refusal after fence claim
retains the owner and snapshot. Capture-only cancellation releases credentials
and exclusion before deferred shutdown replay; a generated or journalled profile
cannot use this cancellation path.

Host C11 -Werror with ASan/UBSan passed on 2026-11-15: actual profile capture,
actual signal fence and cancellation; injected receipt, mode, DOWN and policy.
Cases include actual deferred SIGTERM replay after cleanup, failed unmask retaining
the snapshot until retry, stale receipt, mode drift, post-capture foreign profile replacement,
no-overwrite cancellation and refusal to cancel generated state. The existing
OFF/resume DOWN observer fixture also passed. Temporary test trees were removed
by TemporaryDirectory; no retained scratch outputs.

This is preparation only. No Main UP, profile generation, receipt consumption,
RC binding, target compilation or device acceptance is
provided by this component. Public physical OFF entry remains unbound until the
complete reversible OFF-to-ON lifecycle is integrated and verified. Ordinary ra2
toggling and MCU ACK protection are unchanged.

The preparer now stages this module and header for WR1200JS only, the ABI workflow
selects its MIPS translation unit, and the target-link verifier requires both
admission symbols and the active-admission DOWN observer. Manifest fields keep
linked preparation distinct from an unbound radio-on entry. Host preparation
compiles the separate staged translation unit with C11 -Werror. Target results
for this change remain pending publication and CI.
