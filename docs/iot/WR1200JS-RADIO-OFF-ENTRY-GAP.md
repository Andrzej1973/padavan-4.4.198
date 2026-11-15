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

## Source correction: ordinary CLOSED cannot observe physical DOWN

Source tracing disproved the proposed radio-off-current observer. The ordinary
ra2 CLOSED_CONFIG path calls mbss-closed-probe.h and mbss-close-receipt.h, whose
preflight explicitly requires WR_RADIO_READY/main_ready and original epoch.
Physical Main close instead retires to WR_RADIO_DOWN with an advanced epoch.
The observer's mock admitted an impossible combination. Commit ee81df7 was
reverted before publication; no fallback or READY relaxation was introduced.

Existing main-open-recovery-owner.h already provides the appropriate read-only
wr_iot_main_recovery_release_current predicate for DOWN, exact Main registration,
last software release, epoch/serial and zero vendor count. New origin_main_down
composes it with the cached physical origin. A host C11 ASan/UBSan fixture passes
exact DOWN and refuses READY/epoch/registration/count drift. This predicate
requires a dedicated Linux read-only terminal-observation binding before RC use;
ordinary CLOSED and a historical terminal reply cannot substitute for it.

Standalone physical-stop-terminal-down.inc implements read-only post-RELEASE
QUERY observation with exact cached PID/nonce/tuple, current Main DOWN origin,
exact idle Main registration, historical ra2 registration, zero live/pending
physical pins and idle/closed peer state. Disjoint MacTab/transition lock reads
run under caller RTNL and adapter lifetime. No holds/puts, workers or firmware
commands are issued. It returns COMPLETE only for the current software DOWN.
Actual ARM/Main-completion/RELEASE composition passed ASan/UBSan, including
no adapter mutation and no reference replay; foreign nonce, epoch drift,
Main reopened and peer poison refuse. The idle Main lookup uses exact
device/generation, not find_owned (which excludes completed IDLE records).
No handler/ioctl route is installed yet; target and device acceptance open.
Temporary test directories removed by their fixtures.

Post-RELEASE QUERY is now routed by the experimental physical transaction
handler when no physical lifetime is active. It uses the same WPSQ QUERY
syntax and returns COMPLETE only after the exact terminal/current-DOWN
observation; ordinary in-flight QUERY and durable RELEASE/CANCEL replies retain
their paths. The deferred installer stages the new fragment before handler and
hashes it in the existing manifest. Actual handler composition and installer
refusal tests PASS; new origin/terminal tests registered in host suite. Existing
ioctl wrapper retains privilege/RTNL/Main checks. Full driver target build and
physical runtime remain separate; RC follow-up client is not yet bound.

RC radio-off-observe now uses the fixed existing ra0 transport to send QUERY
only for a retained RELEASE identity. Under a fresh guard it requires Main DOWN,
stable ifindex, exact typed COMPLETE, retained OFF exclusion and no active/pending
shutdown. It validates response identity independently and never submits ARM,
DOWN, CANCEL or RELEASE. Registered host tests cover every tuple field, nonce,
ifindex/Main/owner/pending drift and uncertain/not-submitted transport. Prepared
C11/-Werror compilation PASS; staged for MIPS ABI and full target symbol checks.
ABI43671213212 SUCCESS forfa1d4d0 predates this query/receipt package. Observer
is not yet connected to SDK OFF mutations; physical runtime remains unverified.

Standalone radio-off-state-sdk.inc implements the SDK RAM-only OFF state
effect separately from the combined AP lifecycle: conditional reload_svc_rt
event then mlme_state_rt(0), fixed-key readback and fresh physical DOWN before
and after. Guard/mode/stored-radio mismatches refuse before writes. Caller must
record one attempt; partial/post-observation failure is uncertainty, never retry
permission. Host ASan/UBSan checks PASS. No flash commit or RF command. Adapter
is not staged/called yet; profile generation, bridge detach, services/WAN/IAPP
and final retirement still need complete orchestration.

RAM OFF-state adapter is now embedded in the actual prepare-rc helper construction
with observer/state headers. Registered fixture verifies exact embedded source
and exercises SDK actors; existing ON radio-state and OFF policy checks PASS.
Full experimental target link requires the off-state symbol from net_wifi.o.
Existing radio-profile-state.h provides baseline capture and journalled generator
operations suitable for a separate OFF profile owner, but restart-generation's
origin path explicitly requires radio_on=1 and must not be reused for OFF.
Profile validation/retirement and rollback for OFF remain to be bound before
calling the RAM-state adapter from the final lifecycle. No device action.

Standalone radio-off-profile now owns the real baseline/journal after exact OFF
terminal receipt. It captures before generation, skips generator for reload0,
attempts it once otherwise, validates cold third-BSS content using current saved
SSID/key and existing scanner, and retains baseline through VERIFIED. Partial
or invalid output enters guarded restoration; foreign inode/journal uncertainty
retains without overwrite or generator replay. Baseline restoration returns -1
with context retained, not completed OFF acceptance. Temporary credential copies
in radio-off-profile-check are wiped; no requested enable setting is changed.
Actual profile snapshot/journal/scanner/restore host ASan/UBSan checks PASS for
reload0 inode preservation, normal generation, partial failure, invalid successful
output and foreign inode. SDK generator and physical observation are injected.
Not staged/RC-bound yet; final baseline retirement/rollback cleanup remains open.
Fixture-only cleanup frees retained RAM after asserting non-retirement.

OFF profile owner/check modules are now staged by prepare-runtime, verified
against exact source/header content and board Make selection, included in
MIPS ABI and required full target symbols. Prepared separate C11/-Werror
translation units PASS after explicitly enabling GNU filesystem declarations
before system headers. Registered profile recovery test PASS.
ABI43672264696 SUCCESS forad895ce5 predates the RAM-state/profile package.
OFF profile owner still retains baseline and is not a full lifecycle consumer;
SDK bridge/services/WAN/IAPP, final retirement and device acceptance remain open.

radio-off-followup now composes the actual OFF profile owner then the SDK RAM
adapter. It retains immutable policy/RELEASE copies and refuses drift in the
linked OFF owner. Each tick advances one phase; pending shutdown holds work.
Generated profile verification precedes one marked RAM attempt. Restored profile
or uncertain RAM writes retain baseline/ownership without replay. Success here
means NETWORK_PENDING (unfinished), never completed OFF. Actual journal/scanner
plus SDK RAM adapter host ASan/UBSan fixture PASS; SDK writes and DOWN query
remain actors. Modules staged for MIPS ABI/target symbol checks; prepared C11
compile passed. Stable RC follow-up invocation and remaining network/service
phases still need binding before public radio-OFF activation.

Private RC wait now retains a stable follow-up context. A physical success tick
is followed by a separate follow-up admission tick, then one profile/RAM phase
per normal cadence. Physical failure does not enter SDK follow-up. NETWORK_PENDING
and RETAINED keep OFF ownership/public exclusion, never acknowledge completion.
Actual RC wait fixture checks admission once, later progress, no physical replay
and ordinary/resume exclusion (follow-up actor injected); actual profile/RAM
composition separately passes. Runtime manifest distinguishes this partial
profile/RAM binding from the still-unbound public radio OFF entry.

Standalone radio-off-bridge detaches only fixed SDK 2GHz names from br0, one
slot/call, with current physical DOWN observation and service guard. It checks
IFF_UP clear, exact master and stable ifindices; optional absent interfaces
are accepted, Main absence refuses. Foreign bridge refuses without mutation.
After DELIF any error/readback uncertainty is retained, never implicit replay.
Host ASan/UBSan syscall fixture PASS all seven names, absent/already-detached,
UP/foreign/guard/observation refusal and ioctl/close uncertainty. Not staged
or controller-bound yet. Full e05b6189 host suite exit0/hash recorded separately;
completed 37KB scratch removed after evidence capture. No runtime claim.

Bridge phase now follows the RAM state on separate ticks: seven fixed SDK
slots, at most one detach call per tick, REFUSED retains slot without mutation,
UNCERTAIN enters RETAINED without replay, completed slots are never resubmitted.
Only after all seven slots does NETWORK_PENDING become reachable. Controller
composition tests cover ordered seven-slot success and uncertain first detach
with retained baseline; actual syscall helper separately passes. Prepared C11
translation units PASS; helper staged for MIPS ABI/full target symbol gate.
Network/service/WAN/IAPP completion and owner retirement remain open.
