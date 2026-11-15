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

## OFF authentication and stored radio policy

Pinned SDK start_8021x_rt returns when get_enabled_radio_rt()==0 on this
non-RT3352 board. It otherwise may launch rtinicapd based on auth mode before
checking find_wlan_if_up. Therefore radio_on argument alone is insufficient
to omit authentication: stored radio policy must be captured and validated.
mlme_state_rt writes nvram_set_int("mlme_radio_rt",is_on); it does not commit
NVRAM. Preserve that state update separately from stored rt_radio_x and from
profile generation. Do not call a combined AP starter merely to obtain this
state write after physical RELEASE. Existing WAN planner already supports
radio_on=0 and suppresses reconnect while retaining MAN/WISP mismatch restart.

Runtime-source manifest now distinguishes radio_off_consumer_linked=true from
radio_off_entry_bound=false; source/preparation verifiers enforce both.

## Required OFF orchestration ordering

The terminal consumer is deliberately insufficient for full OFF completion.
Before releasing physical admission, capture immutable OFF follow-up policy
under the owning guard, including reload request, stored radio/auth state and
WAN selection. Existing WAN capture requires active admission, whereas dispatch
requires admission inactive; capturing only after take is invalid.

After exact RELEASE and terminal take, execute only reviewed OFF SDK effects
under fresh identity/policy checks: bridge detach, temporary mlme state, optional
profile/reload marker, conditional auth policy, Guest isolation, WAN and paired
IAPP sequencing. Each effect needs an attempt marker and uncertainty retention;
calling the combined stock restart would repeat physical operations. Pending
normal shutdown must suppress new follow-up submissions and finish owned cleanup.
Do not expose radio_off_entry_bound=true until this complete sequence and the
RC continuation/cancellation paths are composed and target-linked.

Standalone radio-off-policy-sdk.inc now captures reload, stored radio/auth
requirement and radio-OFF WAN plan under active admission and existing guard.
It requires router/mode0, repeats observations, refuses pending shutdown, drift,
invalid values and reconnect-on-OFF, and leaves output untouched on refusal.
The host ASan/UBSan fixture passed all stored-radio/auth/reload combinations
and refusal cases. This is observed-drift checking, not all-writer atomicity.
It is unregistered/unbound: no SDK mutation, daemon or WAN submission.

OFF policy adapter is now embedded by prepare-rc in the actual net_wifi helper
construction with explicit policy/admission headers. The registered test
evaluates the preparer's helper assignments and verifies exact adapter inclusion
before exercising its SDK actor fixture. Full target-link requires the policy
symbol from net_wifi.o. Policy/service/AUX host checks PASS; actual SDK MIPS
link still requires CI. This staging does not enable OFF orchestration.

The private OFF owner now has an explicit prepare operation retaining a validated
policy snapshot. It refuses foreign/busy/terminal owners and invalid reload,
retries read-only capture on refusal, caches one successful capture and rejects
a different reload without re-reading. Policy remains available after physical
terminal consumption until owner acknowledgement. Actual controller/session/
fence composition tests cover capture retry/cache/mismatch and no post-take
read; SDK reads injected. Capture is not automatically invoked by RC yet.
ABI43669741641 SUCCESS for7aae9e94 predates this prepare operation.

Private OFF step now captures policy before physical progress, advances at most
one actual controller step, then polls the exact result. Capture refusal blocks
AUX/Main progress; pending shutdown can progress physical cleanup without new
SDK effects. Exact read-only off_failed identity query permits already-refused
preparation to clean up even when policy capture is unavailable. Actual
composition covers a complete second transaction through this step API alone,
cached terminal/no replay and entropy failure without policy. Focused owner,
composition and exact take checks PASS. RC wait binding and SDK follow-up remain
open; this step reports physical outcome only. Target symbols required.

Private RC OFF admission now retains a static owner/reload and the actual
ppoll continuation prioritizes its guarded step before generic physical,
resume and ordinary continuation. A refused policy capture cannot fall through
to generic physical progress. Terminal owner remains retained, with no new
admission until future verified follow-up acknowledges it. The stock/UI OFF
entry is still unbound. Manifest records progress_bound independently.
Actual ppoll + OFF consumer composition, existing RC runtime and scheduler
ASan/UBSan checks PASS; SDK/physical actors injected. New check registered.
No device actions or target claim for this new binding.

RC wait now retains OFF priority after physical terminal result, until a future
verified follow-up consumer retires the private owner. Repeated bounded ticks
return cached result without repeating physical/policy operations; resume and
ordinary wait-loop continuation do not slip between STOP and SDK follow-up.
Actual RC/OFF fixture checks the terminal tick with both other lanes pending.
This is wait-loop exclusion only: notification-driven/public control admission
must also be audited before enabling the entrypoint. No public OFF binding.

Public OFF exclusion now has a process-only radio_off_owned field in shared RC
admission state. Signal handlers do not touch it; shutdown_end preserves it.
Private RC OFF admission sets it after claim, and refuses an existing exclusion.
Control-server dispatch refuses before shutdown_begin/mailbox claim; direct
activation_execute returns RECOVERY before guard/mode/resource work.
Actual backend/mailbox fixture proves the queued request can still dispatch
after explicit test-only exclusion clearing, and proves shutdown_end does not
clear exclusion. RC/OFF, runtime and scheduler checks PASS. Production clearing
remains reserved for the future verified SDK-follow-up retirement; no entry
activation, target or device claim. Deferred mailbox wake/replay after that
retirement remains required.

The private OFF owner now retains the exact physical RELEASE identity before
successful terminal consumption. off_read requires matching original OFF id/time,
local owner, successful terminal state, no guard/fence, completed nonbusy session
and completed quiesce; it clears output on refusal. Owner validates RELEASE wire
syntax before take and caches receipt independently of the retired physical owner.
Failure cleanup uses its exact failure query without requiring a success receipt.
Focused physical take/receipt, owner, actual composition and RC ppoll checks PASS.
This retained receipt is provenance for fresh follow-up validation, not a fresh
observation or authorization to mutate the replacement/current adapter.

A staged radio-off-current observer now acquires a fresh service guard after
physical admission ends, requires retained OFF exclusion/no pending shutdown,
checks the current backend CLOSED tuple against retained RELEASE twice, Main
administrative DOWN twice and stable nonzero ra0 ifindex. It has no mutating
operations. Host ASan/UBSan tests inject each tuple field drift, ifindex drift,
pending signal, guard/backend/Main failures and invalid RELEASE. Prepared C11
compilation PASS. ABI/target-link include its unit/symbol. Fresh backend query
availability after actual Main DOWN still needs target/device evidence; refusal
retains ownership and never grants a timed fallback. Not yet a complete follow-up
controller or runtime acceptance.
