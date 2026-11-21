## Applied source integration — 2026-11-16

The prepare/commit pair is now applied to local source. INITIAL enabled finish
checks normal consumer availability after the existing exact ACTIVE finish
proof; ACTIVE detach publishes routing before admission ends. Cancellation
OFF/REJECTED does not publish it. Production readiness and device acceptance
remain unverified. Permanent actual-source regression and target linkage are
required before publication; the analysis below records the original gap.

# INITIAL ACTIVE to normal shutdown: integration requirements

Source checkpoint: af52f1401b72d6750438cac55d9c2a90f77699d3; reviewed 2026-11-16.

`rc-physical-stop.c:resume_cleanup` detaches the INITIAL parent and retains an
ACTIVE backend. `radio-stop-fence.c:fence_end` subsequently clears active
admission and replays a pending signal. `rc-shutdown-admission.h` routes such a
signal only when normal_route_armed is already published. The composed host
checks explicitly arm it; they do not prove an automatic production transition.

An integration must publish the normal consumer before active admission is
cleared. Calling the existing route_arm helper from resume_cleanup cannot do
this: the helper rejects active admission. Arming later from runtime polling
leaves an interval in which a normal signal follows the stock shutdown path.
Neither is an acceptable implementation.

Required transition:

1. Validate the exact retained ACTIVE backend, bound physical consumer and
   current process identity under the INITIAL owner's admission, before
   irreversible parent cleanup. Observation failure retains that owner.
2. Commit the prepared route during the same cleanup boundary while active
   admission still protects signal delivery. No allocation, driver I/O or
   fallible observation belongs in the commit callback.
3. A signal arriving after the fence's first unmask but before admission ends
   must remain represented. If cleanup commits a route, replay must reach that
   route; it must not grant stock shutdown before normal OFF and physical
   RELEASE. Pending-before-cleanup follows existing INITIAL cancellation.
4. Retain routing through WAN/IAPP/root retirement; drain transaction owners
   before normal shutdown claims. Preserve notification exclusion and exact
   signal replay after RELEASE. SIGPWR/fault behavior stays unchanged.
5. Test real handlers at each publication boundary, including cleanup-time
   arrival, double TERM/QUIT, observation refusal, inherited blocked mask,
   notification activity and failed replay. Assertions must inspect backend
   OFF and credential wipe at stock replay, not merely after the test loop.

Current evidence: explicit-arm composed host tests; no automatic route,
physical RF/DMA/IRQ, target image installation or device acceptance claim.

## Concrete binding points reviewed

- `restart-finish-check.c:wr_iot_restart_restore_finish_check` already performs
  full ACTIVE observation twice for enabled INITIAL and rejects pending
  shutdown. This is the preflight boundary; cancellation uses the same cleanup
  callback, so commit must additionally distinguish ACTIVE from OFF/REJECTED.
- `rc-initial-restart-detach.inc:initial_restart_detach_commit` can inspect the
  retained backend directly before detaching its borrowed parent. Its current
  contract is nonfallible; do not add a failing public route_arm call here.
- `rc-normal-shutdown.c` owns static spent/retained/claimed/generated state.
  A readiness predicate must inspect that consumer state before cleanup;
  `normal_route_armed` alone does not prove an available consumer.
- Notification ownership is intentional: an admitted batch drains first.
  Arming must preserve that exclusion rather than reject or erase its owner.
- `radio-stop-fence.c:fence_end` can receive a signal inside cleanup after its
  pending check. Publication must handle that recorded pending signal before
  shutdown_end raises it. A preflight check alone cannot close this interval.
- Cancellation OFF/REJECTED and disabled INITIAL need separate reasoning;
  do not arm an ACTIVE-only contract for them by sharing the callback.

No production source was changed during the running full suite.
