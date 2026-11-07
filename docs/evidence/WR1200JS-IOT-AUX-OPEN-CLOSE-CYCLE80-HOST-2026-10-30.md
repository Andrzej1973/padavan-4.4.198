# Actual auxiliary OPEN-to-CLOSE cycle80 — host composition evidence

prepare-aux-open-close-cycle-check.py composes actual APCLI/Monitor OPEN,
actual claim-only virtual-UP dispatcher case, actual owned ndo_stop/helper and
actual checked-DOWN fragment in one executable. Only the already-existing
main-radio READY/OWNED fixture is seeded. The auxiliary begins IDLE; its OWNED
record and open token must be created by the actual OPEN path. This closes the
previous coverage gap where auxiliary OWNED was seeded before testing CLOSE.

Strict GCC C11/O2/Wall/Wextra/Werror base/HNAT variants passed both families:
- OPEN creates count2, one module pin and auxiliary OWNED;
- CLOSE consumes ownership exactly once and returns count1/pin0;
- mark-removing after OPEN still permits the exact matching CLOSE;
- repeated CLOSE refuses without duplicate family/DOWN effects;
- a new normal OPEN-to-CLOSE uses a strictly newer token;
- family OPEN failure retains UNCERTAIN_OPEN/count/pin, and CLOSE cannot
  consume that uncertain ownership;
- family CLOSE failure retains CLOSING/count/pin, and another CLOSE or OPEN
  cannot replay family side effects or steal ownership.

The test generation reuses the actual-owned-close fixture, replacing only its
main test program and adding the actual UP case/OPEN bodies. Family ioctls,
HNAT, module reference operations, kernel locks and physical operations remain
mocked. Main radio startup/hardware readiness, asynchronous callbacks, native/
OS_ABL target ABI and actual device behavior are NOT established. First/last
auxiliary physical ownership and retained worker/continuation are still open.

Common suite now includes the two cycle variants. Full host replay running
session35118 at .iot-local-check/full79-cycle80-host-20261030. Fresh whole
candidate79 preparation running session58858 at
.iot-local-check/peer-retirement-chain79-20261030 from pinned overlay4.
Resume those same handles and compare final source bytes to tested incremental
owner-down79-20261030 when terminal. Do not restart on observation timeout.
Previous confirmed full replay78:80 variants; previous fresh source76:
69 preparers/584 files. These running jobs are source prep and host checks,
not a full firmware build. No router change, manual CI dispatch or publication.

Next implement exact-ticket continuation for proven unmutated DOWN failure,
without replaying successful family/HNAT effects; then completion-after-DOWN,
callback retirement and child/root/PCI receipts. Preserve uncertain failures
until separately reconciled rather than resetting flags to appear complete.
