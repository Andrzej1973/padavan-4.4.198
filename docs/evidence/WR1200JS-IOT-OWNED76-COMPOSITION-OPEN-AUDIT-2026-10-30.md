# Candidate76 composition and remaining OPEN bypass

Adapted the legacy physical-close fixture to omit old auxiliary endpoints
only when BOTH actual endpoints delegate to the owned helper. The common
suite separately composes the actual new wrappers/helper/DOWN (base/HNAT).
Mixed endpoint implementations explicitly fail fixture generation. Nine
targeted variants passed, including legacy native/ABL, shared close bodies,
removing-target admission and the new owned endpoints. No fake replacement
endpoint implementation is used to claim the new behavior.

Main preparer now includes76 after75. Full76 host composition is running
via exec session46448 at .iot-local-check/full76-host-composition-20261030.
Fresh whole-chain preparation is running via session70190 at
.iot-local-check/peer-retirement-chain76-20261030, from the same pinned
full-driver-overlay4-20261029 source as full70. Both handles must be checked
before claiming terminal success; do not restart after an observation timeout.

OPEN source audit found the only two remaining C calls to unclaimed
VIRTUAL_IF_UP in ap/ap_apcli_inf.c and os/linux/rt_profile.c. The inline
legacy helper fills the owner identity with zeroes. In common/cmm_cfg.c,
CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP still has a zero-owner fallback with vendor
count increment/first physical open outside the new ownership protocol.
These are unbound OPEN paths, not merely missing test cases. Their family
OPEN ioctl results are also ignored by the old wrappers.

Next bind APCLI/Monitor OPEN with exact published generation, AUX_OPEN ticket
and VIRTUAL_IF_UP_CLAIM; check family OPEN result; publish OWNED only after
both calls and radio finish/accepted checks. Preserve uncertain acquired pins
on post-attempt failure: failed ndo_open is not guaranteed an ndo_stop. Retire
or reject the unclaimed dispatcher fallback only after confirming every real
caller is migrated, including native/OS_ABL layouts. First physical auxiliary
open remains separate until its startup owner/recovery is implemented.

Host checks still mock kernel, ioctl, HNAT and module behavior. Callback,
last-close, recovery, target/image/device acceptance remain open. No router
change, firmware build, manual workflow dispatch, commit or push this step.

## Completed host composition

Session46448 completed exit0. Full result records77 passed host variants,
full_suite=true, target_compiled=false and runtime_verified=false. Source
preparation session70190 remains live (last observed at wds-outer); resume it.
