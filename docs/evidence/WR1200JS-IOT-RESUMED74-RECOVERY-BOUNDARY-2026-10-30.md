# Resumed integration74 and recovery boundary — 2026-10-30

Published HEAD13ce368 is verified locally after resume. No staged changes
were carried over. Added candidate74 family-close transform to the main
preparer and registered base/HNAT wrapper checks in the common host suite.
Nine targeted variants passed: child failure propagation, native/ABL legacy
close bridge, actual auxiliary remove/helper, and family-close result guards.
Full replay is running at .iot-local-check/full74-host-resumed-20261030 via
session42924. Read its terminal result before claiming a full replay pass.

Recovery review confirms aux-close-recovery-owner.h intentionally accepts
WDS only. Existing strict recovery-owner and family-stage model tests passed
again. They are models; no deferred auxiliary worker is bound by this step.
ApCli_Close has2 lexical MlmeEnqueue calls; Monitor_Close writes RX filters.
Each function has one TRUE and one FALSE return, but success does not prove
queued MLME or hardware callback quiescence. Never turn ioctl success into
a final callback-retirement receipt.

Next required implementation: acquire/retain exact generation/serial owner
before family side effects; record family result separately from DOWN; permit
only proven same-ticket continuation after successful family close; reconcile
uncertain partial failure without replay. Pin adapter/netdev/module lifetime
through the continuation, bind stop/join at PCI teardown, then publish child
completion only after actual callback retirement. Existing WDS stages cannot
be copied to APCLI/Monitor unchanged. Physical/target/image/runtime acceptance
still open. All local work preserved; Sol remains sole writer.

No router state change, firmware build, new commit/push or manual dispatch.

## Terminal full replay result

Session42924 completed exit0. result.json records76 passed host variants,
full_suite=true, target_compiled=false, runtime_verified=false and
lifecycle_accepted=false. The earlier running status is historical. This
verifies incremental candidate74 control flow under mocks. Fresh whole-chain
source preparation through74 remains pending; no production acceptance.
