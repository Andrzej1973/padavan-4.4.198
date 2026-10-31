# Claim-only virtual UP78 — dispatcher host evidence

Pinned prepare-virtual-up-claim-only.py checks all C source files for remaining
VIRTUAL_IF_UP calls before removing the legacy zero-owner fallback in the
actual CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP case. The inline compatibility helper
and request layout remain unchanged; its zero-owner request is now rejected.
NULL payload is rejected. Claimed main/auxiliary paths are preserved.
Scanning uses ASCII bytes because the vendor tree includes non-UTF8 sources;
the initial text scan failed decoding and produced no candidate. Corrected
preparation succeeded. This is a source inventory, not external binary ABI
compatibility proof; native/OS_ABL target modules still require compilation.

prepare-virtual-up-claim-only-check.py extracts the actual dispatcher case
and uses actual claim validators. Strict GCC C11/O2/Wall/Wextra/Werror base
and CONFIG_AP_SUPPORT fixtures passed: NULL/zero owner at counts0/1/max,
stale main generation, exact main physical-start claim, stale auxiliary epoch,
exact auxiliary claim and replay refusal. Kernel locks, physical open and
beacon functions are mocked. Test request fields match the source ordering
and int owner_operation; no target-size/alignment proof is claimed.
An intermediate AP fixture needed the vendor IN annotation defined; no
compiler warning/error was disabled.

Main chain and common host suite include78. Full host replay is RUNNING
session35851 at .iot-local-check/full78-host-composition-20261030; inspect its
terminal report before claiming a complete replay. Last full replay76 passed77
variants; fresh source76 is byte-verified (69 preparers/584 files). Fresh whole
source78 has not been prepared. Candidate78 is .iot-local-check/claim-up78-20261030.

Adjacent audit found another bypass: CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN still
has unclaimed arithmetic/decrement/last-close fallback. No C VIRTUAL_IF_DOWN
callers remain, only the legacy inline helper and case/enum definitions.
Next migrate/reject that unused API after direct consumer review, preserving
actual wr_iot_virtual_down_checked paths, then test complete OPEN-to-CLOSE
composition. Retained recovery, first/last auxiliary physical ownership and
callback/PCI lifetime remain open. No router mutation, firmware build, manual
workflow dispatch, commit or push this step.
