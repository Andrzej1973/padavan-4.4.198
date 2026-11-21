# Staged one-shot OPEN admission

`driver-open-controller.c` is staged in the WR-only RC tree, without a bound
activation entry point. Its caller holds the serialized service/config owner
and excludes fatal-signal teardown; service guard alone does not provide that
shutdown fence. The caller owns network snapshot and recovery throughout.

Before OPEN, the controller requires exact temporary request values and three
ready gates, ra2 administratively DOWN, non-overlapping routes, owned bridge
address, DHCP/DNS protocol readiness and current-WAN policy observation. This
policy observation does not run firewall generation. Staged credentials are
not a loaded-driver key receipt; the existing driver OPEN performs that check.

Submission latches its phase before calling the tracked OPEN client. Even a
not-submitted or uncertain result cannot cause another OPEN on this context.
The object retains only nonsecret attempt identity. Strict driver completion,
post-OPEN policy/service observations and unchanged staged values are required
for CONFIRMED. That state is software acceptance, not RF/client acceptance.

Uncertainty retains the original identity for the separate recovery-only
receipt query and CLOSE. No recovery read changes phase or grants successful
ON. Startup rollback, shutdown dispatch, image and physical gates remain open.
