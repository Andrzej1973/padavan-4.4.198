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

## Saved policy differs from physical UP

The first implementation incorrectly called the general live mode reader.
Pinned SDK `is_radio_on_rt()` reports live interface UP (and MLME in its optional
branch), whereas `get_enabled_radio_rt()` reads saved `radio_x`. After physical
OFF all interfaces are DOWN; the live reader therefore returns radio0 even
when saved ON policy is selected. The prior injected mode actors returned1
and did not cover that adapter boundary.

Admission and generation now call the separate guarded
`wr_iot_rc_radio_on_mode_read`, which reads saved policy only. The general live
reader and post-UP AUX checks remain unchanged. This does not grant readiness:
fresh physical DOWN is still required before generation, then exact new Main
identity before network progression. The actual RC adapter/restore composition
fixture reproduces live0/saved1 and completes the new host chain, while saved0
refuses before fence acquisition. See WR1200JS-ON-LIVE-VS-SAVED-MODE evidence.
Target and device verification remain separate; public OFF/ON is still unbound.
