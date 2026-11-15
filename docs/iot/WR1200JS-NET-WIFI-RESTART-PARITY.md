# WR1200JS restart integration parity gate

Audited 2026-11-14 against SDK c25283e915a2a00a763774dd255b14aff997285e.
Input: preserved exact Git tar, `trunk/user/rc/net_wifi.c`, SHA256
`98bbe9cfca0af35be4ddb82742022b90cc51c2f7b34834e627ee6c5f2187dc69`.
Candidate code: d7fdc49. Source inspection only; no router operations.

The new private physical/resume path must preserve stock restart behavior before
replacing `restart_wifi_rt`. Existing source compilation does not prove parity.

| Stock operation | Current private path | Required integration |
|---|---|---|
| `stop_8021x_rt()` before DOWN | Missing orchestration | Guarded one-attempt stop before AUX/Main; uncertain result retained |
| APCLI/WDS/Guest/Main DOWN | Private fixed AUX slots and Main session | Bind request once; never invoke stock combined stop afterward |
| `gen_ralink_config_2g(0)` conditional on reload | Existing captured reload0 skips generator | Verified no-reload bytes/inode/mtime/ctime preservation; reload_svc_rt flag remains separate |
| `reload_svc_rt=1` when reload | Missing | Set only for corresponding captured reload; do not repeat generation |
| `mlme_state_rt(radio_on)` | Missing | Preserve `mlme_radio_rt` policy; distinguish NVRAM from driver readiness |
| Main/Guest UP and br0 attachment | Controllers implemented | Use existing exact generation/Main/Guest checks |
| `wif_control_m2u(0, Main/Guest)` | Missing | Preserve per-BSS multicast conversion after attachment; read saved `IgmpSnEnable` under ownership |
| WDS/APCLI startup | Mode0 only candidate | Preserve mode0 bridge removal; do not claim modes1–4 support from mode0 checks |
| `start_8021x_rt()` | Conditional daemon/RSSI submission | Confirm exact stock branch semantics and stop/start pair; process name alone is not ownership/readiness |
| `restart_guest_lan_isolation()` | Guest router-mode sysfs path implemented | Preserve unrelated 5GHz Guest effects without replaying global side effects |
| `check_apcli_wan(0, radio_on)` | Missing | Verify mode0 no-op or preserve exact side effects |
| `update_vga_clamp_rt(0)` | Missing | Check board macro path; preserve if compiled |
| LED_SW2G ON/OFF | Missing | Preserve terminal ordering; LED is not readiness proof |
| `/usr/bin/iappd.sh restart` | Missing | One owned terminal attempt; command return not daemon readiness |

`wif_control_m2u` calls `brport_set_m2u` with saved `IgmpSnEnable` only when
`USE_IGMP_SNOOP` is absent. Do not add a global driver setting as a substitute.
`mlme_state_rt` writes `mlme_radio_rt`; it is not an RF/DMA observation.

Keep stock entrypoints unbound until these gaps have implementation and focused
composition coverage, followed by exact MIPS/image verification. Preserve the
ACK/stale-response mechanism. Ordinary ra2 toggles must continue to avoid physical
restart/scan. Device acceptance remains a separate owner-authorized stage.


## Authentication-stop controller candidate

`restart-auth-stop.[ch]` implements SDK timing without sleeping: TERM once,
three-second observation, KILL once, one-second observation. Missing/uncertain
submission or expiry retains the owner; no retry storm or physical DOWN follows.
A stopped process is re-observed before readiness. Backward monotonic time and
pending admission refuse progress. Process-name absence is only administrative
stop evidence. Host ASan/UBSan test passes with service adapters injected.
This new module is not yet linked into preparation or physical begin. Actual
fixed-service adapters/guard and integration tests are the next step. Existing
full-suite22508 continues on unchanged d7fdc49 inputs and does not cover this new
unregistered controller. No target or device acceptance claim.

The pinned `common_ex.c::kill_services` always permits at least one second of
waiting, loops with sleep(1), and may sleep after SIGKILL. Calling it from the
RC progress tick would defeat nonblocking operation. `check_apcli_wan` can call
full_restart_wan on MAN/WISP mismatch regardless of mode0; preserve this side
effect under explicit ownership instead of assuming it is inert.


The standalone `restart-auth-stop-sdk.inc` now supplies exact fixed-service
presence and TERM/KILL commands under the existing service guard and mode0 gate.
Adapter plus actual controller ASan/UBSan composition passes; SDK functions are
injected. It adds no sleep or polling loop; the existing doSystem command itself
is synchronous, so hard command-duration bounds are not established. Name-based
semantics match stock and do not claim PID ownership. Preparation and physical
binding remain pending. Existing full-suite22508 inputs were not edited.


## Authentication stop bound to private physical progression

Prepared net_wifi now receives the fixed-service adapter and its header; runtime
preparation copies/compiles the auth controller. After private IoT OFF quiescence,
physical progress starts auth stop in a separate tick before AUX/ARM/Main. Fresh
absence is rechecked for every later AUX/ARM admission; reappearance retains
without a signal replay. Actual physical/controller composition passes with
service actors injected. Native preparation and physical/quiesce/finish/cancel
checks pass. The full d7fdc49 registered suite exited0 before these changes;
new auth tests are now registered but no new full-head pass is claimed.
Pending-shutdown recovery during pre-ARM auth-stop uncertainty and stock net_wifi
entrypoint binding remain open. No device operation or target acceptance implied.


## Pre-ARM normal shutdown cancellation

Physical progress observes blocked SIGTERM/SIGQUIT before further operations.
Before a session/ARM exists, normal shutdown can finish without waiting for an
uncertain auth-stop receipt: fresh backend CLOSED, completed private quiescence,
idle scheduler and owned outer fence are required. No Main DOWN was submitted
by this physical owner. Cleanup wipes retained desired settings and releases
the guard before deferred signal replay; the physical terminal is taken once.
Pending quiescence continues through its existing OFF path; cancellation cannot
bypass an unfinished OFF. Once a session owns ARM, this shortcut refuses.
A real blocked-SIGTERM fixture covers stale CLOSE, existing session and failed
mask restore, then successful cleanup with no AUX/ARM/Main calls. Physical/auth,
scheduler, finish/cancel/quiesce and native checks pass separately. Target and
device evidence remain pending; stock entrypoints are still unbound.


## Per-BSS multicast transport candidate

Pinned netutils.c::brport_set_m2u sets both multicast_fast_leave and
multicast_to_unicast. The new restart-multicast transport supports only ra0/ra1,
requires service guard and br0 membership, compares ifindex before/after, and
reads back both exact0/1 values. It refuses absent attributes rather than creating
files. A failed apply can partially update attributes: the caller must record
attempt before submission and retain uncertainty, never blindly replay.
Actual regular-file read/write tests pass with guard/master/ifindex actors;
ra2, foreign master, guard loss, index drift and missing attribute are covered.
Runtime preparation compiles/copies it, but Main/Guest controllers do not yet
invoke it. Saved IgmpSnEnable and USE_IGMP_SNOOP gating must be added at the owning
policy layer before claiming stock parity. Host/native evidence does not prove
kernel sysfs or physical multicast operation.


## Captured multicast policy and one-shot controller

Prepared WR helper now exports multicast policy under guard/mode0/radio/Guest
checks. Both USE_IGMP_SNOOP branches are tested: no conversion attributes are
required with snooping; otherwise exact stable IgmpSnEnable is normalized using
SDK boolean semantics. Policy observation performs no NVRAM writes.
The staged multicast controller retains policy and exact Main/Guest pointers,
requires Guest's Main pointer to match, marks each BSS attempt before applying,
and never retries uncertainty. Main precedes enabled Guest; Guest OFF and snoop
branches omit their writes. READY rechecks policy, owners and attribute values.
Host controller tests pass with owner/transport actors; actual transport and
SDK policy tests are separate. Native preparation passed after adding the GNU
feature macro required by included profile receipt declarations. Root restore
integration and finalizer/retirement ownership for this controller remain pending;
these components alone do not complete restart parity.


## Multicast bound before service startup

Root restore embeds multicast at its final stable address and gates service
begin/progress/PREPARED on its readiness. Actual restore/Guest/multicast/services
composition verifies both BSS attempts before any service command. Pre-OPEN
owner checks remain in normal progress. After handoff, finish uses a read-only
multicast observation together with exact rebind ACTIVE proof; it never invokes
old pre-OPEN Main checks. Busy/uncertain/foreign-parent multicast refuses finish.
Physical finish/cancel cleanup clears multicast parent pointers before deferred
shutdown replay. Terminal retirement refuses remaining parent pointers or busy.
Focused source/composition/native checks pass; owner and transport actors remain
explicit in their respective fixtures. Root/profile fixtures use a named
multicast component actor, while the restore composition uses the real multicast
controller. The latest full suite predates this integration. No MIPS/image/device
acceptance is claimed. Remaining reload/mlme/LED/iappd/WAN and stock entrypoint
parity gaps remain open.


## No-reload audit correction

The initial parity table incorrectly described unconditional generation.
`restart-generation.c::generation_step` has skipped generation when captured
intent.reload is0 since be8c0a3. Existing generation tests cover zero calls.
A focused check now also proves original profile bytes, device/inode, size and
mtime/ctime remain unchanged through repeated verification, and abort remains
refused after possible Main UP. The first fixture run measured metadata before
its baseline setup; moving the measurement after setup fixed that fixture error.
No production generator change was needed. The new test is standalone/unregistered
while full-suite75467 uses unchanged1b74afc inputs. This does not resolve the
missing conditional reload_svc_rt update or imply target/runtime acceptance.


## SDK radio/reload state adapter candidate

Standalone restart-radio-state-sdk.inc requires service guard, mode0, enabled
radio and administrative Main DOWN before fixed RAM NVRAM writes. reload0 never
writes reload_svc_rt; reload1 writes1 with readback before mlme_state_rt(1).
Final guard/mode/radio/Main checks and readback refuse partial or uncertain state.
No nvram commit, interface UP or timing-register change is performed.
ASan/UBSan fixture covers admission failures, unchanged reload0 flag and each
readback refusal. SDK setters/observers are actors. This adapter remains unbound:
root must mark a single attempt before calling after profile verification and
before Main UP. Do not infer RF state from mlme_radio_rt. Existing full-suite
75467 uses unchanged1b74afc code and excludes this new standalone component.


## Watchdog reload event correction

Pinned watchdog.c lines341–345 consumes reload_svc_rt1 by resetting it0 and
invalidating RADIO2/GUEST2 schedule caches. update_svc_status_wifi2 also clears
it at421. Therefore producer-side persistence readback is not a valid delivery
receipt. The standalone radio-state adapter now sends the fixed event without
requiring it to remain1; MLME readback and admission checks remain. The host test
passes even when the event is no longer observable, and explicitly makes no
successful-delivery claim. This supersedes earlier reload-readback descriptions.
No root binding has been enabled. Scheduler consumer coordination remains a
required integration check.

Full-suite75467 handle and its /tmp log are missing in the current environment.
Its result is unavailable, not inferred successful from prior progress. Reverify
an immutable integrated revision on CI or a new bounded host run.


## Radio/reload state bound before Main submission

Root restore revalidates generation before the fixed SDK state update, marks
radio_state_attempted before invoking it and retains on any refusal or pending
shutdown. Main begin follows only a successful return, never a repeated setter.
Prepared WR helper/header now installs the real adapter. Actual root failure
fixture proves zero Main UP and no replay after uncertain state update. Existing
restore/Guest/multicast/service composition, profile/finish/premain checks and
native preparation pass with explicitly injected SDK adapters. The watchdog
reload event still has no delivery receipt. No new target/runtime claim.


## IAPP exact-script audit and firewall preparation candidate

Pinned trunk/user/ralinkiappd/iappd.sh::stop sleeps twice when a daemon is
present. start launches ralinkiappd in background, writes neighbor sysctls for
br0/eth2/ra0 and selected rai0/rax0 paths, then appends TCP/UDP3517 INPUT rules
unconditionally. Direct synchronous restart in the RC progress window would
block and repeated starts accumulate rules. Process launch is not readiness.
Standalone prepare-iappd.py converts only these two fixed appends to existence
checks followed by add. Executed shell fixture proves two sequential starts add
each rule once; duplicate/changed source refuses. It is not installed into the
firmware preparation yet and does not serialize competing firewall writers.
Command errors and concurrent replacement need the existing firewall ownership
contract at integration. Do not claim this removes the script sleeps or makes
its lifecycle nonblocking. Full-suite84131 remains independent on unchanged
registered e2c9162 inputs; these new standalone files are not covered by it.


Pinned IAPP preparation has now been exercised against the complete preserved
SDK script (SHA256 f414c96fe5270b18320a5bce75b95736469113b1302bb170999a01558c0f25d6).
Only the two exact rule lines change; reverse substitution reproduces every
original byte. CLI invocation preserves executable permission bits, sh -n passes,
and duplicate preparation fails without mutation. This standalone check accepts
--archive for another exact SDK archive path. It does not execute daemon/sysctl
commands or prove target iptables -C support, firewall-writer serialization,
service readiness or nonblocking lifecycle. Those gates remain required before
installation. No full archive extraction or persistent copy was created.


Pinned iptables1.8.7 `iptables/iptables.c` source SHA256
02b79eda91661d0de8436a166214d67872057df36fc85c361739b7576543542a
parses case 'C' as CMD_CHECK and dispatches it to check_entry. Reproducible
check-iappd-iptables-source.py passed against the preserved archive. This proves
source capability only; effective firmware selection, final binary and kernel
behavior remain unverified. No archive extraction or persistent scratch.


IAPP rule preparation now distinguishes check status1 from other failures.
Only1 permits an append; other nonzero statuses return from start without adding.
Append failure is propagated too. Executed shell fixture injects check status2
and proves no extra rule append; pinned-script byte/mode/syntax tests pass again.
This does not prove all status1 errors mean absence or solve concurrent writers;
source CLI semantics and ownership remain integration prerequisites.
Full immutable registered e2c9162 host suite84131 exited0. Source log hash/size
recorded in E2C9162-HOST-SUITE evidence, finished log removed. New standalone IAPP
checks are separate and not part of that suite. MIPS/image/device remain separate.


## IAPP asynchronous child transport candidate

PID1 init.c::catch_sig_reap uses waitpid(-1,NULL,WNOHANG), discarding child exit
statuses. A direct later waitpid on an IAPP child is therefore insufficient.
Standalone restart-iapp-child uses a supervisor and nonblocking CLOEXEC pipe;
the supervisor resets inherited SIGCHLD handling and owns its script child's
wait result. The parent reads an explicit success/failure byte, treating EOF or
unknown receipt as failure. Command exec resets signal handlers/mask and closes
inherited nonstandard descriptors before fixed /usr/bin/iappd.sh restart. No
arbitrary arguments, PID killing or automatic resubmission are exposed.
Actual fork/exec/pipe test under PID1-style reaper passes for script exit0 and7.
This is script completion only, not daemon readiness. Source is standalone:
service/firewall ownership, shutdown handling, supervisor lifetime/guard pinning,
command-duration policy, firmware copy/link and root binding remain open. A hung
script retains uncertainty; no timer authorizes duplicate restart. No router use.


IAPP supervisor now closes inherited nonstandard descriptors except its receipt
pipe before forking the script. Parent alone retains service/status ownership.
A real pipe EOF fixture verifies inherited writer closure while the script is
still running, rather than only after child exit. Missing exec yields failure,
not success/retry; exit0/nonzero and generic PID1 reaping remain covered. Script
fixture waits1s to distinguish descriptor cleanup from command completion.
Parent must keep its ownership until receipt; no child pins are implied. The
component remains uninstalled and needs shutdown/root/finalizer integration.
ABI43638435042 for e2c9162 succeeded; this does not cover the new IAPP module.


IAPP child begin now checks active admission, no pending shutdown and current
service guard before pipe/fork. Existing receipt drain requires retained admission
and guard, but permits pending shutdown without any new launch. A closed predicate
reports only idle or consumed success/failure with no live pipe; it does not
convert failure into restart success. Actual process tests cover pre-admission,
guard loss, pre-begin pending refusal and post-begin pending drain. Runtime
preparation now copies/compiles the child unit/header; native check passes.
The unit is registered in host suite, but root/finish/cancel remain unbound.
Firewall writer coordination remains a separate unmet prerequisite.


IAPP receipt handling now distinguishes confirmed command failure(-1) from
unknown completion(-2). EOF/read/close error or an unknown byte cannot prove
that a command stopped if its supervisor died. Unknown remains retained and
closed refuses; no relaunch or outer cleanup is authorized. Only recognized
success/failure receipts from the supervisor (or failure to fork before a command
exists) establish closed state. Real pipe EOF/malformed-receipt tests pass along
with actual exec/reaper tests; native preparation passes. This corrects earlier
wording that grouped missing receipt with a closed failure. Root remains unbound.


## Root cleanup fence for IAPP child

Root now reserves a stable embedded IAPP context. Physical finish, cancellation,
pre-Main/pre-handoff cancellation and terminal retirement refuse a live or
unknown-completion child. Finish additionally refuses a confirmed script failure;
cancellation can accept confirmed failure only with its existing independent
CLOSED/Guest/physical proofs. No IAPP begin is yet invoked by root.
Actual physical finish/cancel fixtures inject unknown child completion and prove
guard retention; retirement does likewise. Real child-process tests remain green.
Native preparation passes. This is cleanup protection, not IAPP lifecycle or
firewall ownership completion; root launch remains disabled until those gates.


Supervisor wait-error correction: receipt defaults to unknown3, not confirmed
failure2. Only an exact waitpid result supplies success/failure; failed command
fork supplies confirmed failure because no script exists. Setup/wait errors
remain unknown. Receipt3 fault fixture refuses closed/cleanup. Actual process
checks and native preparation pass. This narrows completion evidence only;
root launch and firewall ownership integration remain pending.


Direct supervisor wait-failure fixture now injects ECHILD from the actual wait
call after reaping its test command. Actual supervisor emits unknown3; parent
returns-2 and refuses closed and duplicate begin. The fixture reaps children and
removes its temporary script. This tests the wait-error branch in addition to
raw malformed/EOF receipt parsing. Host ASan/UBSan PASS; no target/runtime claim.


## Firewall writer integration decision

Exact firewall_ex.c has iptables-restore calls at1233,1280,1339,1359,2091,2134
and2223 (last uses-n). Existing service-lock explicitly protects participating
writers only. Current preparation does not wrap all these paths with that lock.
Consequently IAPP service-guard admission does not prove firewall serialization.
Keep root launch disabled. Integrate fixed IAPP INPUT policy into the owned
normal/default firewall builders, then remove independent script additions only
with source/image parity checks. Preserve post-firewall hooks and final isolation
readback. This is a source-identified integration gap, not evidence of a device
race. Input hash and exact calls recorded in IAPP-FIREWALL-WRITERS evidence.


Standalone prepare-iappd-builder now stages TCP/UDP3517 br0 INPUT policy in IPv4
normal/default builders immediately after their exact existing WR quarantine
hooks. Compiled/executed transformed fragments show IoT DROP before IAPP LAN
ACCEPTs. Missing/duplicate hooks refuse before output; no IPv6/ra2 policy is
introduced. This is a fragment fixture, not full SDK/image verification. The
transform is not yet invoked by firmware preparation. Script rule removal must
be installed atomically with builder integration after exact prepared-SDK proof.
Full registered aaebbfe suite71195 remains independently active and unchanged.


Exact SDK firewall body composition now uses the actual quarantine-insertion
AST loop from prepare-rc.py, then applies IAPP builder transformation. Both IPv4
functions receive one pair after quarantine; IPv6 bodies receive none. The
paired prepare-iappd-policy-pair validates builder and original script before
returning either output; removes exactly two script appends. Exact script shell
syntax passes and changed input refuses. CLI writes are not a filesystem atomic
transaction: candidate trees must be discarded on write error. Neither transform
is installed in firmware preparation yet. Full SDK compile/image parity remains
required; this test is source composition, not a complete prepared SDK build.


Experimental prepare-iappd-policy-source now installs the pair only after a
WR1200JS runtime manifest with production_ready=false. It checks both source
paths, validates both transformations and shell syntax before writes, preserves
script mode and emits input/output hashes in a final manifest. Wrong board,
production and duplicate inputs are tested to refuse without mutation. On any
write failure the candidate must be discarded; final manifest/hash verification
is required downstream. This installer is not yet invoked by the main workflow,
and IAPP root launch remains false. Full SDK compile/image acceptance pending.


ABI workflow now stages the exact SDK IAPP script alongside prepared runtime
firewall sources, invokes paired preparation, checks output manifest SHA256,
quarantine-before-IAPP ordering and script mutation removal, and uploads its
manifest with ABI diagnostics. Host installer test verifies post-preparation
script drift refuses; workflow YAML parses. This added step is source verification,
not an additional full firewall MIPS compile or ROMFS admission. Root launch stays
false. A dispatched run is required before claiming actual CI success.


Full registered host suite for aaebbfe completed with observed exit0 (71195).
IAPP process/receipt/cleanup checks are included; newer paired firewall source
checks are separate. Log hash/size retained in AAEBBFE-HOST-SUITE evidence and
completed log removed. ABI now explicitly compiles prepared restart-iapp-child
with the pinned MIPS/uClibc compiler; this object was not covered by the former
small runtime subset. Native preparation preflight and workflow parse pass.
Actual MIPS result is pending, and does not imply script/kernel/device readiness.


Root restore now drains an attempted, not-confirmed-closed IAPP child before
other progression, including pending shutdown. Unknown completion remains fenced;
confirmed failure can reach existing cancellation checks. No new launch is
performed by this path. Focused actual-root test covers sticky unknown result and
a separate pending-to-failure scenario with child adapter injected. Restore/
Guest/multicast/services, finish/premain and native checks pass. Root launch is
still disabled; paired source verification and final terminal ordering remain.


Runtime preparation now emits restart-iapp-policy.h with PREPARED0. Only paired
policy installation accepts that exact inactive gate and writes PREPARED1 after
both source transformations. Manifest verification requires the enabled gate
as well as source hashes. Unexpected/already-enabled gate refuses before source
writes. Host installer and native preparation pass. Root does not yet consume
this gate; launch remains unbound until the guarded root branch is implemented.


## Guarded root IAPP launch implemented

Root consumes PREPARED policy gate: after Guest/multicast/services, it marks one
IAPP launch attempt before calling begin, then waits for successful receipt
before PREPARED/handoff. Admission failure cannot replay launch; existing service
phase remains cancellable. Existing receipt draining precedes pending shutdown;
unknown completion blocks cleanup. Default/local gate0 skips launch. Paired
candidate gate1 enables it and manifest records that binding. Host gated-root
fixture covers pending, success, failed command and failed admission with actors;
default restore and prehandoff checks pass separately. Native preparation passes.
ABI now explicitly compiles the gate1 prepared restore with MIPS compiler after
policy installation. New MIPS/image/runtime results are pending, and main firmware
workflow still needs paired preparation before claiming IAPP installed there.


ABI dd9f7d4 run43665195993 failed before C compilation in the new policy step:
source sparse checkout omitted trunk/user/ralinkiappd/iappd.sh. Added that exact
directory to the pinned checkout. Experimental compile-runtime-link now copies
ralinkiappd with RC/HTTP, applies/verifies paired policy before target link and
retains candidate script/manifest. Base firmware/binaries remain hash-checked
and unchanged. Shell syntax, sparse checkout YAML assertion and host installer
checks pass; new SDK target result pending. This activates only the isolated
experimental target-link candidate, not the release firmware image.


## WAN terminal follow-up planning

Pure restart-wan-plan captures check_apcli_wan decisions after interface-name
resolution: AP mode skips; MAN/WISP band mismatch needs full WAN restart;
unchanged active APCLI on the changed enabled band needs reconnect; otherwise
none.72 valid combinations match a transcription of the pinned SDK branches;
invalid identities refuse. This is not proof of live interface resolution or
SDK execution. The eventual follow-up must occur after release of radio/service
ownership; calling full_restart_wan inside resume would cross the unfinished
transaction. Planner is standalone/unbound, not permission to drop WAN actions.
CI058542e ABI43665781009 pending and standard43665783692 running at last check.
