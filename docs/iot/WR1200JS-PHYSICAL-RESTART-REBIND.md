# Physical restart: identity handoff still required

Status: old completion identity capture implemented locally; new-identity
handoff/resume still required. No production or physical runtime acceptance.
This concerns physical restart after a prior IoT OPEN, not ordinary ra2 toggles.

Source findings verified on 2026-11-14:

- `radio-transition.h`, `wr_iot_radio_begin`: START, AUX_START, MAIN_OPEN and
  RESET increment epoch, even if the netdevice address survives.
- `reopen-admission.c`, `wr_iot_reopen_witness_current`: the current CLOSE must
  match the saved epoch, generation, OPEN token and CLOSE serial exactly.
  This witness deliberately cannot authorize OPEN after epoch replacement.
- `precreated-idle-reference.h`, `wr_iot_precreated_idle_reference`: initial
  admission rejects prior `last_token` and CLOSE history. Advancing radio epoch
  does not erase that history or turn a prior OPEN into initial idle.
- `physical-stop-lifetime.h`, `wr_iot_physical_stop_lifetime_end`: ending the
  completed lifetime clears Main identity and ticket validity in that context.
- `physical-stop-terminal-types.h`: terminal cache now includes a pointer-free
  old Main completion origin. `physical-stop-release.inc` captures it from a
  freshly revalidated actual Main release under the transition lock before
  lifetime end. New-identity mapping is still absent; RELEASED is a cleanup
  receipt, not a resume authorization. Snapshot `valid` alone is insufficient:
  terminal ready/RELEASED and exact PID/request are also mandatory.
- `rc-quiesce.h`: desired settings survive normal OFF in a private RC context.
  They are user intent, not a driver identity or loaded-key receipt.

Therefore neither stale CLOSE reuse nor initial-idle fallback can implement
physical restart resume. Do not clear registry history to make initial admission
pass. The restart guard remains held in the staged controller until its verified
consumer is implemented. The existing MCU ACK and shared TX ownership remain
unchanged.

Next implementation sequence:

1. Implemented locally: before physical lifetime end, retain a bounded kernel-derived completion
   identity for the exact old Main ticket/registration and old IoT CLOSE.
   Keep it outside released task/module/netdev ownership. Preserve existing
   disjoint lock ordering and terminal retry behavior; no naked stale pointers.
2. Bind a Linux-only handoff to the actual issuing PID and original nonce /
   physical attempt. CANCELLED cannot serve as a physical completion receipt.
3. After the existing checked Main startup, validate its fresh READY epoch,
   current Main and ra2 registrations, idle executor, completed old recovery and
   closed IoT state. An unchanged address alone is insufficient.
4. Issue a narrowly scoped old-to-new handoff receipt from those actual facts.
   Define single-use OPEN admission, lost-response recovery, generation/epoch
   drift rejection and adapter retirement before installing its transport.
5. Bind the fresh receipt to RC startup/resume while retaining desired settings
   and service/shutdown guards. Release guards only after the captured intent
   and its resume outcome have been handled. STOP/CANCEL recovery stays distinct.

This is a driver/RC Linux API task using available SDK source. It does not
require changing firmware protocol or obtaining proprietary ROM documentation.
A host fixture cannot certify RF/DMA/IRQ or late TxS retirement.

Regression evidence:

- Actual RC backend/owner quiesce fixture rejects a changed driver epoch with
  cleared output while retaining desired settings and resume ownership.
- The initial-reference fixture has26 cases, including radio epoch advancement
  with prior OPEN and prior CLOSE history. Both remain rejected, without state
  mutation. This fixture is already run by the optional merged-candidate job.
- Both passed strict O2 ASan/UBSan locally. Target and device checks remain open.

Local same-registration Main readiness predicate now compares the old origin
with actual last_release and requires READY/Main-ready, newer epoch and retired
radio serial, no active worker release/reset/PM/TX, same published Main device
and generation, and a strictly newer OPEN token. Native tests cover18 rejection
cases in addition to14 old-origin mismatches. This predicate is not yet called
by a new transport/admission path; it is not ra2 or RF readiness. Replacement
registrations are deliberately unsupported by this predicate and need their own
verified mapping rather than address-based acceptance.

Local ra2 historical identity predicate now requires the original RELEASE tuple
and exact published MBSS device/generation/OPEN token/CLOSE serial/old epoch,
IDLE with completed close stage4 and no removal/uncertain/running/unmutated-open
state. Twelve refusal cases pass with the same strict native sanitizer build as
the18 Main readiness and14 old-origin tests. This is historical identity only:
it does not replace current-epoch beacon/key/probe checks, exact terminal issuer
or single-use OPEN admission. Both new predicates remain unbound to transport.
