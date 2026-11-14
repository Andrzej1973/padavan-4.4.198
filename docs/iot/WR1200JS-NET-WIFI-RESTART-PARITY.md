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
