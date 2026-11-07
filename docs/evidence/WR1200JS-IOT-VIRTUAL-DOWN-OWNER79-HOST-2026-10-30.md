# Reject unclaimed legacy DOWN79 — host evidence

Source audit of candidate78 found no C VIRTUAL_IF_DOWN calls and no direct C
CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN consumers other than its dispatcher case.
The remaining inline compatibility helper sends an unclaimed request.
Pinned prepare-virtual-down-owner-only.py replaces the old count decrement/
last physical-close fallback with explicit failure. Command enum/request layout
and wr_iot_virtual_down_checked remain unchanged. External prebuilt/native/
OS_ABL modules require matching target build; this is not an ABI acceptance.

The actual rejected case passed strict GCC C11/O2/Wall/Wextra/Werror assertions
with counts0/1/2/max, NULL/non-NULL request and no physical callback invocation.
The legacy bridge fixture now expects rejected compatibility DOWN to preserve
count; it still tests actual physical close and native/ABL bridge results.
11 targeted variants passed: legacy bridge, shared close bodies, actual owned
APCLI/Monitor+DOWN base/HNAT, claim-only UP base/AP, and rejected legacy DOWN.
These use mocked kernel/driver primitives, not hardware or concurrency proof.

Separate full78 replay session35851 completed exit0:80 variants passed,
full_suite=true, target_compiled=false, runtime_verified=false. Evidence
.iot-local-check/full78-host-composition-20261030/result.json.
Candidate79 is .iot-local-check/owner-down79-20261030; main preparer/suite include
it. Fresh full79 source preparation and full replay remain pending. Last
fresh whole source76 has69 preparers/584 byte-identical files. All current
check sessions are terminal; no verified wait remains.

Next compose actual APCLI/Monitor OPEN, real claim-only dispatcher and owned
CLOSE/DOWN in one host cycle. The auxiliary OWNED record must be created by
OPEN, not seeded as a shortcut. Then bind same-ticket deferred continuation,
callback retirement and final child/root/PCI receipts. First/last physical
auxiliary ownership remains incomplete. No production installation, firmware
build, router change, workflow dispatch, commit or push in this step.
