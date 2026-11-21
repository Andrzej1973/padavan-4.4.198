# Claimed APCLI/Monitor OPEN77 and fresh76 source verification

Fresh preparation session70190 completed exit0:69 preparers/584 files.
Independent hashes and manifest match incremental aux-owned76b-20261030
byte-for-byte. Receipt .iot-local-check/full76-comparison77.json. Full76
host replay77 variants therefore applies to identical fresh source bytes.
No target compilation, image or runtime evidence is implied.

Pinned prepare-aux-family-open-owner.py changes the two real APCLI/Monitor
OPEN wrappers. They reserve exact published generation/AUX_OPEN ticket before
virtual UP, call VIRTUAL_IF_UP_CLAIM, check family ioctl result, finish the radio
ticket and publish OWNED only after all required success/readiness checks.
HNAT registration and APCLI carrier behavior occur only on accepted ownership.
Preflight refusals release the provisional module pin; after an UP attempt,
uncertain failure retains pin/record because failed ndo_open has no guaranteed
ndo_stop. First physical auxiliary open is deliberately refused until separate
startup/recovery binding exists, matching the reviewed WDS boundary.

After UP returns, the wrapper rechecks record/ticket/epoch and reset/PM/retire
intent before invoking family OPEN outside the spinlock. Late reset observed
there skips family ioctl. This is not an atomic exclusion of future requests;
the retained ticket and final readiness check cover late invalidation. No
claim of hardware/callback quiescence follows from family ioctl success.

The extractor now takes only each actual OPEN function, excluding intervening
CLOSE helper declarations. Existing fixture counters were updated consistently;
an intermediate failure came from an obsolete counter-reset anchor, corrected
without relaxing assertions. Candidate aux-open77b-20261030 passed strict GCC
actual three-family OPEN tests plus5 targeted composition variants, including
existing WDS open, owned close and removing admission. Assertions cover success,
UP refusal, family refusal, post-UP reset without family call, configured-WDS
failure and retained uncertain pins. Kernel, dispatcher/MMIO and family ioctl
operations remain mocked; full native/OS_ABL binary ABI is uncompiled.

After77, source search finds no VIRTUAL_IF_UP C caller, only its legacy inline
header definition. Dispatcher zero-owner fallback STILL EXISTS and must be
removed/rejected after complete direct CMD/ABI caller review. It is not proven
safe merely because the source wrapper callers were migrated. Next close that
bypass, check complete OPEN-to-CLOSE composition and retained recovery/lifetime.
Main preparer includes77; fresh full77 preparation/replay has not run. No router
mutation, firmware build, workflow dispatch, commit or push this step.
