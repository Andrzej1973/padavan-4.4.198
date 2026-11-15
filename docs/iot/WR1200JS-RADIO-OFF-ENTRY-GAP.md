# Physical radio OFF entry integration gap — 2026-11-15

Scope: source audit of 6c786921; no device action or acceptance.

The existing private restart entry accepts radio_on=1 only. Extending it to
radio_on=0 is not a one-line predicate change.

| Boundary | Current source | Required work |
| --- | --- | --- |
| Intent | restart-entry.c initializes {restart=1,radio_on=1,reload} | Define OFF intent and SDK side effects separately from ON resume |
| Physical progress | rc-physical-stop.c stops polling after result is published | Install an explicit process-owned terminal consumer; otherwise owner remains allocated |
| Consumption | wr_iot_rc_physical_take clears the retained context exactly once | Consume only the matching private OFF transaction, never another caller's result |
| Scheduler | restart-scheduler.c requires restart && radio_on | OFF cannot be handed to the existing ON scheduler |
| Signal replay | non-restart physical_step ends fence before assigning physical.result | Before enabling OFF entry, test pending shutdown and prove cleanup/publication ordering; do not infer it from ON resume cleanup |
| Legacy fallback | prepare-rc.py calls wr_iot_quiesce before stop_8021x/profile generation; rc-backend.c refuses ACTIVE/STOP/OFF | Preserve refusal and isolation; a failed private entry must not bypass it |

Implementation acceptance: a private OFF owner with exact intent correlation;
nonblocking completion through RC wait; one terminal take; no ON scheduler,
profile regeneration or accidental reopen; pending SIGTERM/SIGQUIT, failed mask
restore, repeated OFF, new ON after completed OFF, and foreign-result refusal.
Existing saved configuration must survive. Inspect the pinned SDK OFF branch
for required LED/auth/IAPP/WAN behavior before selecting those side effects.

The current full host suite remains separate evidence. Its success cannot
prove this not-yet-bound OFF entry. The radio_on=0 refusal remains in place.

## Pinned SDK OFF behavior confirmed

Inspected trunk/user/rc/net_wifi.c directly in the retained exact c25283e
archive without extraction. restart_wifi_rt(0,reload) calls stop_8021x_rt,
stop_wifi_all_rt; reload additionally generates the profile and sets temporary
reload_svc_rt=1. start_wifi_ap_rt(0) detaches Main/Guest from br0 and calls
mlme_state_rt(0). start_wifi_wds_rt(0) detaches all four WDS interfaces;
start_wifi_apcli_rt(0) detaches APCLI. No interface-UP branch is selected.
The subsequent auth starter, Guest isolation and IAPP restart remain calls
whose OFF-specific behavior must be traced before replacing them.

check_apcli_wan(0,0) skips AP mode; in router mode it still invokes
full_restart_wan when MAN and configured WISP bands differ. It does not
invoke try_wan_reconnect for radio OFF. Therefore physical descriptor drain
alone does not preserve the SDK OFF network/configuration semantics.

ABI43667886374 completed success for6c786921. Local full-suite session62243
and its log disappeared before terminal observation: local full result is
UNVERIFIED, not PASS. Do not infer its exit status from absence.

## STOP terminal ordering correction

Non-restart/refused physical completion now uses fence_end_cleanup: terminal
result publication, volatile desired-settings wipe and guard release occur
while admission remains active, before deferred shutdown replay. Failed mask
restore retains the original guard/context and unpublished result. Session
receipt/intent remain for one terminal take. The actual RC/session/fence
fixture asserts publication and wipe inside its real SIGTERM handler.
Focused RC physical, pre-ARM shutdown and fence fault checks passed with
ASan/UBSan. OFF entry consumer and SDK side effects remain unimplemented;
this correction does not enable radio OFF or prove target/device behavior.
Temporary test directories removed by their fixtures; no scratch retained.

The registered check-physical-stop-mask-failure.py additionally injects a
failed SIG_SETMASK into the actual STOP/session/fence fixture. It verifies
retained password/guard/unpublished result, no terminal take before cleanup,
same-fence successful retry without another driver call, and publication/wipe
visible in the real deferred SIGTERM handler. ASan/UBSan PASS; no target claim.

## Exact private OFF terminal take

The physical owner now retains the original private OFF envelope identity
independently of the quiesce receipt (an already-OFF receipt may use an older
identity). wr_iot_rc_physical_take_off requires exact id/time, local process
ownership and a non-restart OFF intent before consuming terminal success or
failure once. Pending/foreign/malformed/restart calls leave the owner intact.
The registered ASan/UBSan fixture passed real controller/session/fence with
injected transport. This is the terminal consumption primitive only; RC OFF
pump and SDK side effects are still not bound. No image/device claim.

Standalone radio-off-owner now retains only private id/time and process owner,
claims physical OFF once, polls the exact terminal take, caches success/failure
and requires one acknowledgement before reuse. It never drives physical steps
or repeats admission from poll. Reentrant/foreign/pending/refused/cached-terminal
ASan/UBSan fixture passed with injected physical actor. Not registered/staged
or RC-bound yet: real controller composition, SDK follow-up and shutdown policy
remain required before enabling radio OFF. Temporary fixture removed.

The OFF owner and actual-controller composition checks are now registered in
the physical-stop suite (therefore future ABI). Composition includes actual
physical owner, session and fence, with mocked backend/transport: pending poll,
foreign identity retention, one Main DOWN, exact RELEASE consumption, cached
terminal receipt, entropy-preparation failure consumption. ASan/UBSan PASS.
Consumer remains unbound to RC wait and SDK OFF follow-up. Source fixtures
removed their temporary directories; no retained scratch.

OFF owner is now staged by prepare-runtime with its header and WR-only object.
The prepared-source verifier checks exact source/header and board selection.
ABI includes its MIPS translation unit; full experimental target-link requires
begin/poll/take and exact physical take symbols. Actual transformed source
compiles under strict host C11 (-Werror); POSIX declarations explicitly enabled.
Prepared-source, OFF actor and actual composition checks PASS. No RC wait
activation or SDK OFF follow-up is implied; target results still required.
