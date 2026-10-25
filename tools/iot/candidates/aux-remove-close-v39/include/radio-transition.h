/* Candidate admission only. NOT installed in the vendor driver.
 * Caller must hold the SAME adapter-scoped short lock for EVERY operation.
 * The admitted ticket, not the spinlock, spans hardware work/waits. All
 * open/close/reset entries must use it and adapter lifetime must be pinned.
 * Admission observes readiness and reserves exclusive mutation atomically;
 * it is not evidence of hardware completion or RF silence. */
#ifndef WR_IOT_RADIO_TRANSITION_H
#define WR_IOT_RADIO_TRANSITION_H
enum wr_iot_radio_phase {WR_RADIO_DOWN,WR_RADIO_READY,WR_RADIO_CLOSING,WR_RADIO_FAULT,WR_RADIO_UNVERIFIED,WR_RADIO_SUSPENDING,WR_RADIO_SUSPENDED};
enum wr_iot_radio_operation {WR_RADIO_START=1,WR_RADIO_BSS_OPEN,WR_RADIO_RESET,WR_RADIO_CLOSE,WR_RADIO_BSS_CLOSE,WR_RADIO_MAIN_OPEN,WR_RADIO_VERIFY,WR_RADIO_AUX_OPEN,WR_RADIO_AUX_CLOSE,WR_RADIO_AUX_START};
enum wr_iot_reset_kind {WR_RADIO_RESET_PDMA=1,WR_RADIO_RESET_PSE=2};
struct wr_iot_radio_ticket {unsigned long serial,epoch;int operation;unsigned int reset_kind;enum wr_iot_radio_phase prior_phase;int prior_ready;};
struct wr_iot_radio_transition {
 unsigned long serial,retired_serial,epoch;
 unsigned int joined_workers,shutdown_stage,close_notified,virtual_down_stage,virtual_up_stage;
 unsigned int active_tx;
 unsigned int active_reset_kind;
 int busy,main_ready,exhausted,main_inhibited,reset_pending,retiring;
 int pm_suspending,pm_suspended;
 enum wr_iot_radio_phase pm_prior_phase;
 int pm_prior_ready;
 enum wr_iot_radio_phase phase;
};
/* Fresh adapter only; never reset this state while references/work exist. */
static inline void wr_iot_radio_transition_init(struct wr_iot_radio_transition *s){
 s->serial=0;s->retired_serial=0;s->epoch=1;s->busy=0;s->main_ready=0;s->exhausted=0;s->main_inhibited=0;s->reset_pending=0;s->retiring=0;s->pm_suspending=0;s->pm_suspended=0;s->pm_prior_phase=WR_RADIO_DOWN;s->pm_prior_ready=0;s->active_reset_kind=0;s->active_tx=0;s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;s->virtual_down_stage=0;s->virtual_up_stage=0;s->phase=WR_RADIO_DOWN;
}
/* Caller holds the common adapter lock. Every OS TX entry must acquire this
 * lease before touching radio state and release it after the driver TX call.
 * PM publishes its fence under that SAME lock, then waits outside the lock
 * for active_tx to reach zero. The staged adapter wrapper supplies the
 * last-TX wakeup; this model supplies neither a waiter nor a lifetime pin.
 * Its count cannot be substituted for kernel netdev refs. */
static inline int wr_iot_radio_tx_enter(struct wr_iot_radio_transition *s){
 if(!s||!s->epoch||s->active_tx==~0U||s->retiring||s->pm_suspending||
    s->pm_suspended||s->phase!=WR_RADIO_READY||!s->main_ready||
    s->main_inhibited||s->reset_pending||s->busy)return 0;
 s->active_tx++;return 1;
}
/* Returns 1 exactly when the last admitted TX exits, for a future wakeup. */
static inline int wr_iot_radio_tx_leave(struct wr_iot_radio_transition *s){
 if(!s||!s->active_tx)return 0;
 s->active_tx--;return s->active_tx==0;
}
/* Fence new hardware work before PCI suspend. An admitted reset is conservatively
 * returned to pending even if its caller later reports success: suspend may cut
 * across its hardware/readback sequence. Caller serializes this with the same
 * adapter lock and drains the in-flight ticket before disabling PCI. */
static inline int wr_iot_radio_request_suspend(struct wr_iot_radio_transition *s){
 if(!s->epoch||s->retiring||s->pm_suspending||s->pm_suspended||
    (s->phase==WR_RADIO_DOWN&&!s->busy)||s->phase==WR_RADIO_CLOSING)return 0;
 if(s->epoch==~0UL){s->exhausted=1;s->main_ready=0;return 0;}
 s->pm_prior_phase=s->phase;s->pm_prior_ready=s->main_ready;
 s->epoch++;s->pm_suspending=1;s->main_ready=0;
 if(s->busy==WR_RADIO_RESET)
  s->reset_pending|=s->active_reset_kind?s->active_reset_kind:WR_RADIO_RESET_PDMA;
 s->phase=WR_RADIO_SUSPENDING;
 return 1;
}
/* Called only after radio close/PM teardown has finished and no ticket remains.
 * It is a software lifecycle marker, not proof that RF power is off. */
static inline int wr_iot_radio_suspend_complete(struct wr_iot_radio_transition *s){
 if(!s->epoch||!s->pm_suspending||s->pm_suspended||s->retiring||s->busy||s->active_tx||
    (s->phase!=WR_RADIO_SUSPENDING&&s->phase!=WR_RADIO_DOWN))return 0;
 s->pm_suspending=0;s->pm_suspended=1;s->main_ready=0;s->phase=WR_RADIO_SUSPENDED;
 return 1;
}
/* PCI suspend failed before physical close/power-down (for example, TX drain
 * timed out). Drop PM ownership only after any admitted operation has retired.
 * Keep admissions closed until a separate hardware/readiness verification;
 * a timed-out driver TX call may still be active and is not DMA retirement. */
static inline int wr_iot_radio_abort_suspend(struct wr_iot_radio_transition *s){
 if(!s||!s->epoch||!s->pm_suspending||s->pm_suspended||s->retiring||
    s->busy||(s->phase!=WR_RADIO_SUSPENDING&&
              s->phase!=WR_RADIO_CLOSING&&s->phase!=WR_RADIO_DOWN))return 0;
 s->pm_suspending=0;s->main_ready=0;s->phase=WR_RADIO_UNVERIFIED;
 return 1;
}
/* Only for a PM wait timeout before ANY queue, vendor-flag or hardware
 * mutation. Caller proves that precondition and holds the common lock.
 * A continuing admitted TX is safe to coexist with restored admission only
 * because the device was never stopped. New reset/close intent forbids it. */
static inline int wr_iot_radio_abort_suspend_unmutated(struct wr_iot_radio_transition *s){
 if(!s||!s->epoch||!s->pm_suspending||s->pm_suspended||s->retiring||
    s->busy||s->phase!=WR_RADIO_SUSPENDING||s->reset_pending||
    s->main_inhibited||s->exhausted||s->pm_prior_phase!=WR_RADIO_READY||
    !s->pm_prior_ready)return 0;
 s->pm_suspending=0;s->phase=WR_RADIO_READY;s->main_ready=1;
 return 1;
}
/* Call after PCI D0/state restoration and driver initialization, before making
 * BSS/queues usable. This deliberately returns to UNVERIFIED; pending reset
 * remains latched and must drain before VERIFY or BSS admission. */
static inline int wr_iot_radio_resume_unverified(struct wr_iot_radio_transition *s){
 if(!s->epoch||!s->pm_suspended||s->pm_suspending||s->retiring||s->busy)return 0;
 if(s->epoch==~0UL){s->exhausted=1;s->main_ready=0;return 0;}
 s->epoch++;s->pm_suspended=0;s->phase=WR_RADIO_UNVERIFIED;s->main_ready=0;
 return 1;
}
/* Invalidate stale queued work before teardown; no wait and no resource free.
 * An already admitted operation still owns its ticket and must retire it. */
static inline void wr_iot_radio_request_close(struct wr_iot_radio_transition *s){
 if(!s->epoch)return; /* zeroed/partial adapter is not initialized */
 if(s->phase!=WR_RADIO_CLOSING){
  if(s->epoch==~0UL)s->exhausted=1;else s->epoch++;
  s->phase=WR_RADIO_CLOSING;
 }
 s->main_ready=0;
}
/* Administrative main-down, even if secondary BSS keeps hardware alive.
 * Latch before wrapper mutations; late completion may not undo this intent. */
static inline void wr_iot_radio_main_down(struct wr_iot_radio_transition *s){
 if(!s->epoch)return;
 if(s->epoch==~0UL)s->exhausted=1;else s->epoch++;
 s->main_inhibited=1;s->main_ready=0;
}
/* Removal intent precedes family unregister. Keep selective teardown usable;
 * physical CLOSING is requested only by the final reference. Caller holds the
 * shared short lock. This invalidates admission, NOT a lifetime reference or
 * proof that producers/workers are quiescent. Never reinitialize for reuse. */
static inline void wr_iot_radio_retire(struct wr_iot_radio_transition *s){
 if(!s->epoch||s->retiring)return;
 s->retiring=1;
 wr_iot_radio_main_down(s);
}/* Request at the TOP-LEVEL reset entry, before PSE/PDMA mutations. A busy
 * owner retires normally; pending reset blocks new open/verification work.
 * Caller must schedule/drain it; this helper neither queues nor waits. */
static inline int wr_iot_radio_request_reset_kind(struct wr_iot_radio_transition *s,unsigned int kind){
 if(!kind||(kind&~(WR_RADIO_RESET_PDMA|WR_RADIO_RESET_PSE)))return 0;
 if(s->retiring||!s->epoch||(s->phase==WR_RADIO_DOWN&&!s->busy)||
    (s->phase==WR_RADIO_CLOSING&&!s->pm_suspending&&!s->pm_suspended))return 0;
 if(s->pm_suspending||s->pm_suspended){
  if(!s->reset_pending&&s->epoch!=~0UL)s->epoch++;
  if(s->epoch==~0UL)s->exhausted=1;
  s->reset_pending|=kind;s->main_ready=0;return 1;
 }
 if(!s->reset_pending){if(s->epoch==~0UL)s->exhausted=1;else s->epoch++;}
 s->reset_pending|=kind;s->main_ready=0;return 1;
}
/* Unspecified recovery conservatively requests PSE (which includes PDMA).
 * Real callers must identify their required scope explicitly. */
static inline void wr_iot_radio_request_reset(struct wr_iot_radio_transition *s){
 wr_iot_radio_request_reset_kind(s,WR_RADIO_RESET_PSE);
}
static inline int wr_iot_radio_begin(struct wr_iot_radio_transition *s,
 unsigned long expected_epoch,int operation,struct wr_iot_radio_ticket *t){
 if(!s->epoch||s->busy||s->serial==~0UL||expected_epoch!=s->epoch)return 0;
 /* A prior PM abort may leave an admitted TX executing in UNVERIFIED.
  * No new radio mutation, including VERIFY, may race that call. */
 if(s->active_tx)return 0;
 if(s->pm_suspended||(s->pm_suspending&&operation!=WR_RADIO_CLOSE))return 0;
 if(s->retiring&&operation!=WR_RADIO_CLOSE&&operation!=WR_RADIO_BSS_CLOSE&&operation!=WR_RADIO_AUX_CLOSE)return 0;
 if(operation==WR_RADIO_CLOSE){if(s->phase!=WR_RADIO_CLOSING)return 0;}
 else{
  if(s->exhausted&&operation!=WR_RADIO_BSS_CLOSE&&operation!=WR_RADIO_AUX_CLOSE)return 0;
  if(s->reset_pending&&operation!=WR_RADIO_RESET&&operation!=WR_RADIO_BSS_CLOSE&&operation!=WR_RADIO_AUX_CLOSE)return 0;
  if(operation==WR_RADIO_START||operation==WR_RADIO_AUX_START){if(s->phase!=WR_RADIO_DOWN)return 0;}
  else if(operation==WR_RADIO_MAIN_OPEN){
   if(s->phase!=WR_RADIO_READY&&s->phase!=WR_RADIO_UNVERIFIED)return 0;
  }else if(operation==WR_RADIO_VERIFY){
   if((s->phase!=WR_RADIO_UNVERIFIED&&s->phase!=WR_RADIO_READY)||s->main_inhibited)return 0;
  }else if(operation==WR_RADIO_BSS_CLOSE||operation==WR_RADIO_AUX_CLOSE){
   if(s->phase!=WR_RADIO_READY&&s->phase!=WR_RADIO_UNVERIFIED&&s->phase!=WR_RADIO_FAULT)return 0;
  }
  else if(operation==WR_RADIO_RESET){
   if((s->phase!=WR_RADIO_READY&&s->phase!=WR_RADIO_UNVERIFIED)||s->main_inhibited)return 0;
  }else if(operation==WR_RADIO_AUX_OPEN){
   if(s->phase!=WR_RADIO_READY)return 0;
  }else if(operation==WR_RADIO_BSS_OPEN){
   if(s->phase!=WR_RADIO_READY||!s->main_ready)return 0;
  }else return 0;
 }
 /* Startup/reset can reconstruct adapter radio state. Invalidate work
  * queued before this reconstruction, even if the netdevice address survives. */
 if(operation==WR_RADIO_START||operation==WR_RADIO_AUX_START||operation==WR_RADIO_MAIN_OPEN||operation==WR_RADIO_RESET){
  if(s->epoch==~0UL){s->exhausted=1;s->main_ready=0;s->phase=WR_RADIO_FAULT;return 0;}
  s->epoch++;
 }
 t->prior_phase=s->phase;t->prior_ready=s->main_ready;
 if(operation==WR_RADIO_START||operation==WR_RADIO_AUX_START){s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;}
 if(operation==WR_RADIO_CLOSE||operation==WR_RADIO_BSS_CLOSE||operation==WR_RADIO_AUX_CLOSE)s->virtual_down_stage=0;
 s->virtual_up_stage=0;
 s->busy=operation;t->serial=++s->serial;t->epoch=s->epoch;t->operation=operation;
 t->reset_kind=operation==WR_RADIO_RESET?
   (s->reset_pending?(unsigned int)s->reset_pending:WR_RADIO_RESET_PDMA):0;
 s->active_reset_kind=operation==WR_RADIO_RESET?t->reset_kind:0;
 if(operation==WR_RADIO_RESET)s->reset_pending=0;
 if(operation==WR_RADIO_RESET||operation==WR_RADIO_VERIFY)s->main_ready=0;
 return 1;
}
/* Cancel an admitted BSS open ONLY before any vendor/hardware mutation.
 * Caller holds the shared transition lock. A concurrent close, main-down or
 * reset intent remains authoritative; cancellation never republishes READY.
 * Keep serial advanced so a retired ticket cannot be reused. */
static inline int wr_iot_radio_abort_bss_open_unmutated(
 struct wr_iot_radio_transition *s,const struct wr_iot_radio_ticket *t){
 if(!s->epoch||!t||t->operation!=WR_RADIO_BSS_OPEN||
    s->busy!=WR_RADIO_BSS_OPEN||s->serial!=t->serial)return 0;
 s->busy=0;s->retired_serial=t->serial;
 return 1;
}
/* Auxiliary (AP-client/WDS/monitor) open uses the same exclusive ticket but
 * cannot impersonate MBSS. Abort only before any driver/vendor mutation. */
static inline int wr_iot_radio_abort_aux_open_unmutated(
 struct wr_iot_radio_transition *s,const struct wr_iot_radio_ticket *t){
 if(!s||!s->epoch||!t||
    (t->operation!=WR_RADIO_AUX_OPEN&&t->operation!=WR_RADIO_AUX_START)||
    s->busy!=t->operation||s->serial!=t->serial)return 0;
 s->busy=0;s->retired_serial=t->serial;return 1;
}
/* Non-last AUX_CLOSE reservation may be withdrawn before any queue, family
 * CLOSE, HNAT or vendor-count mutation. Preserve concurrent reset/PM intent. */
static inline int wr_iot_radio_abort_aux_close_unmutated(
 struct wr_iot_radio_transition *s,const struct wr_iot_radio_ticket *t){
 if(!s||!t||!s->epoch||t->operation!=WR_RADIO_AUX_CLOSE||
    s->busy!=WR_RADIO_AUX_CLOSE||s->serial!=t->serial||
    s->virtual_down_stage)return 0;
 s->busy=0;s->retired_serial=t->serial;return 1;
}
/* Main open may fail its registry reservation before AP_MAIN_OPEN or virtual
 * dispatcher mutation. Restore only that unmutated ticket. A concurrent
 * close/reset/PM intent remains authoritative and cannot publish READY. */
static inline int wr_iot_radio_abort_main_open_unmutated(
 struct wr_iot_radio_transition *s,const struct wr_iot_radio_ticket *t){
 if(!s||!t||!s->epoch||
    (t->operation!=WR_RADIO_START&&t->operation!=WR_RADIO_MAIN_OPEN)||
    s->busy!=t->operation||s->serial!=t->serial)return 0;
 s->busy=0;s->retired_serial=t->serial;
 if(s->epoch==t->epoch&&!s->main_inhibited&&!s->reset_pending&&
    !s->pm_suspending&&!s->pm_suspended&&!s->retiring&&
    s->phase!=WR_RADIO_CLOSING){
  s->phase=t->prior_phase;s->main_ready=t->prior_ready;
 }else s->main_ready=0;
 return 1;
}
/* The caller holds the common lock over this count and reference ownership.
 * Zero references require physical start but must not publish main-ready. */
static inline int wr_iot_radio_begin_aux_open(struct wr_iot_radio_transition *s,
 unsigned int active_interfaces,struct wr_iot_radio_ticket *t){
 if(!s||!t)return 0;
 return wr_iot_radio_begin(s,s->epoch,
   active_interfaces?WR_RADIO_AUX_OPEN:WR_RADIO_AUX_START,t);
}
/* Candidate stop reservation. The caller must stabilize VirtualIfCnt and
 * interface ownership against EVERY increment/decrement for this decision.
 * This helper never decrements the vendor count or performs teardown.
 * Return 1 only with an owned ticket; 0 means unresolved mandatory teardown,
 * NOT permission to return from ndo_stop as if cleanup had completed.
 * An invalid zero count is refused before publishing any closing intent.
 * Last-reference intent invalidates pending work even when an owner is busy;
 * that owner must retire before the caller retries with pinned resources. */
static inline int wr_iot_radio_begin_stop(struct wr_iot_radio_transition *s,
 unsigned int active_interfaces,struct wr_iot_radio_ticket *t){
 if(!active_interfaces||!s->epoch)return 0;
 if(active_interfaces==1){
  wr_iot_radio_request_close(s);
  return wr_iot_radio_begin(s,s->epoch,WR_RADIO_CLOSE,t);
 }
 return wr_iot_radio_begin(s,s->epoch,WR_RADIO_BSS_CLOSE,t);
}
/* Main-interface stop must publish main-down BEFORE waiting for an admitted
 * secondary open, then claim exclusive teardown under the SAME adapter lock.
 * Zero count is invalid: never change main state from an unowned stop. A
 * failed claim means the caller must wait for the current ticket and retry
 * with a fresh, stabilized reference count; it must not mutate the adapter.
 * This helper does not provide a wait queue or authorize ndo_stop binding. */
static inline int wr_iot_radio_begin_main_stop(struct wr_iot_radio_transition *s,
 unsigned int active_interfaces,struct wr_iot_radio_ticket *t){
 if(!s||!s->epoch||!active_interfaces||!t)return 0;
 if(!s->main_inhibited)wr_iot_radio_main_down(s);
 return wr_iot_radio_begin_stop(s,active_interfaces,t);
}
/* A waiter snapshots serial under the adapter lock and waits outside it.
 * A new ticket may start after the old one retires, so recount and retry
 * main-stop admission after wakeup. Wake only after releasing the lock. */
static inline int wr_iot_radio_ticket_retired(
 const struct wr_iot_radio_transition *s,unsigned long serial){
 return s&&serial&&s->retired_serial>=serial;
}
/* Auxiliary close never uses BSS-specific teardown. Last reference still
 * claims the physical close, under the caller's stabilized owner/count lock. */
static inline int wr_iot_radio_begin_aux_stop(struct wr_iot_radio_transition *s,
 unsigned int active_interfaces,struct wr_iot_radio_ticket *t){
 if(!active_interfaces||!s->epoch)return 0;
 if(active_interfaces==1){
  wr_iot_radio_request_close(s);
  return wr_iot_radio_begin(s,s->epoch,WR_RADIO_CLOSE,t);
 }
 return wr_iot_radio_begin(s,s->epoch,WR_RADIO_AUX_CLOSE,t);
}
/* BSS_CLOSE is selective: it must not request adapter CLOSE or clear main
 * readiness. Caller must prove it is not the last virtual-interface close;
 * last-reference teardown needs the adapter-wide closing protocol instead. */
/* observed_success includes required actual hardware/readback evidence.
 * A failure is uncertain: only teardown can recover this candidate state.
 * Close requested during admitted work must never be undone by late success. */
static inline int wr_iot_radio_finish(struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t,int observed_success){
 if(!s->epoch||!s->busy||s->busy!=t->operation||s->serial!=t->serial)return 0;
 /* Suspend invalidates in-flight success. Preserve its reset request and retire
  * the ticket without publishing READY; PCI power-down must wait for this. */
 if(s->pm_suspending&&s->phase==WR_RADIO_SUSPENDING){
  if(t->operation==WR_RADIO_RESET)
   s->reset_pending|=t->reset_kind?t->reset_kind:WR_RADIO_RESET_PDMA;
  s->busy=0;s->retired_serial=t->serial;s->active_reset_kind=0;s->main_ready=0;
  return 1;
 }
 /* Main-down/close may invalidate an already admitted ticket. */
 if(t->epoch!=s->epoch&&s->phase!=WR_RADIO_CLOSING&&!s->main_inhibited&&!s->reset_pending)return 0;
 s->busy=0;s->retired_serial=t->serial;
 s->active_reset_kind=0;
 if(t->operation==WR_RADIO_CLOSE){
  s->phase=observed_success?WR_RADIO_DOWN:WR_RADIO_CLOSING;s->main_ready=0;
  if(observed_success&&!s->pm_suspending&&!s->pm_suspended)s->reset_pending=0;
 }else if(s->phase!=WR_RADIO_CLOSING&&t->operation==WR_RADIO_AUX_START){
  s->phase=!observed_success?WR_RADIO_FAULT:
    (t->epoch==s->epoch&&!s->reset_pending?WR_RADIO_READY:WR_RADIO_UNVERIFIED);
  s->main_ready=0;
 }else if(s->phase!=WR_RADIO_CLOSING&&
          (t->operation==WR_RADIO_BSS_CLOSE||t->operation==WR_RADIO_AUX_CLOSE)&&
          observed_success){
  /* Teardown is not verification: preserve uncertainty/fault and pending intent. */
  s->phase=t->prior_phase;
  s->main_ready=t->prior_ready&&t->epoch==s->epoch&&!s->main_inhibited&&!s->reset_pending;
 }else if(s->phase!=WR_RADIO_CLOSING&&t->operation==WR_RADIO_AUX_OPEN&&observed_success){
  s->phase=t->epoch==s->epoch&&!s->reset_pending?
    t->prior_phase:WR_RADIO_UNVERIFIED;
  s->main_ready=t->prior_ready&&t->epoch==s->epoch&&!s->main_inhibited&&!s->reset_pending;
 }else if(s->phase!=WR_RADIO_CLOSING){
  s->phase=observed_success?WR_RADIO_READY:WR_RADIO_FAULT;
  if(observed_success&&t->epoch==s->epoch&&
     (t->operation==WR_RADIO_START||t->operation==WR_RADIO_MAIN_OPEN))s->main_inhibited=0;
  s->main_ready=!!observed_success&&!s->main_inhibited&&!s->reset_pending;
 }
 return 1;
}
/* Evaluate an auxiliary open after retiring its ticket, under the same
 * transition lock. A vendor success can be invalidated by reset, main-down
 * or PCI suspend before the wrapper publishes its netdev as owned. */
static inline int wr_iot_aux_open_accepted(
 const struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t,int finished){
 return s&&t&&finished&&t->operation==WR_RADIO_AUX_OPEN&&
  s->retired_serial==t->serial&&t->epoch==s->epoch&&
  s->phase==WR_RADIO_READY&&!s->busy&&!s->reset_pending&&
  !s->retiring&&!s->main_inhibited&&!s->pm_suspending&&
  !s->pm_suspended&&!s->exhausted;
}
/* Software wrapper returned success, but hardware readback is still missing.
 * Same caller-held lock covers finish and demotion: no READY is published. */
static inline int wr_iot_radio_finish_unverified(struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t){
 int finished=wr_iot_radio_finish(s,t,1);
 if(finished&&s->phase==WR_RADIO_READY){s->phase=WR_RADIO_UNVERIFIED;s->main_ready=0;}
 return finished;
}
/* Main-open deliberately awaits hardware readback in UNVERIFIED. Distinguish
 * that expected state from a late success invalidated by reset/close/PM. */
static inline int wr_iot_main_open_accepted(
 const struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t,int finished){
 return s&&t&&finished&&
  (t->operation==WR_RADIO_START||t->operation==WR_RADIO_MAIN_OPEN)&&
  s->retired_serial==t->serial&&t->epoch==s->epoch&&
  s->phase==WR_RADIO_UNVERIFIED&&!s->busy&&!s->main_ready&&
  !s->reset_pending&&!s->retiring&&!s->main_inhibited&&
  !s->pm_suspending&&!s->pm_suspended&&!s->exhausted;
}

/* Admission stays reserved while the caller performs reviewed radio readback
 * outside the spinlock. Retiring a ticket is not the same as accepting proof:
 * epoch/intent changes during observation must return false to its caller. */
static inline int wr_iot_radio_verify_finish(struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t,int observed_success){
 if(t->operation!=WR_RADIO_VERIFY)return 0;
 if(!wr_iot_radio_finish(s,t,observed_success))return 0;
 return observed_success&&s->epoch==t->epoch&&s->phase==WR_RADIO_READY&&s->main_ready;
}

#endif
