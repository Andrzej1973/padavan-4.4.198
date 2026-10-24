/* Candidate admission only. NOT installed in the vendor driver.
 * Caller must hold the SAME adapter-scoped short lock for EVERY operation.
 * The admitted ticket, not the spinlock, spans hardware work/waits. All
 * open/close/reset entries must use it and adapter lifetime must be pinned.
 * Admission observes readiness and reserves exclusive mutation atomically;
 * it is not evidence of hardware completion or RF silence. */
#ifndef WR_IOT_RADIO_TRANSITION_H
#define WR_IOT_RADIO_TRANSITION_H
enum wr_iot_radio_phase {WR_RADIO_DOWN,WR_RADIO_READY,WR_RADIO_CLOSING,WR_RADIO_FAULT,WR_RADIO_UNVERIFIED};
enum wr_iot_radio_operation {WR_RADIO_START=1,WR_RADIO_BSS_OPEN,WR_RADIO_RESET,WR_RADIO_CLOSE,WR_RADIO_BSS_CLOSE,WR_RADIO_MAIN_OPEN,WR_RADIO_VERIFY};
enum wr_iot_reset_kind {WR_RADIO_RESET_PDMA=1,WR_RADIO_RESET_PSE=2};
struct wr_iot_radio_ticket {unsigned long serial,epoch;int operation;unsigned int reset_kind;enum wr_iot_radio_phase prior_phase;int prior_ready;};
struct wr_iot_radio_transition {
 unsigned long serial,epoch;
 unsigned int joined_workers,shutdown_stage,close_notified,virtual_down_stage;
 int busy,main_ready,exhausted,main_inhibited,reset_pending,retiring;
 enum wr_iot_radio_phase phase;
};
/* Fresh adapter only; never reset this state while references/work exist. */
static inline void wr_iot_radio_transition_init(struct wr_iot_radio_transition *s){
 s->serial=0;s->epoch=1;s->busy=0;s->main_ready=0;s->exhausted=0;s->main_inhibited=0;s->reset_pending=0;s->retiring=0;s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;s->virtual_down_stage=0;s->phase=WR_RADIO_DOWN;
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
 if(s->retiring||!s->epoch||(s->phase==WR_RADIO_DOWN&&!s->busy)||s->phase==WR_RADIO_CLOSING)return 0;
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
 if(s->retiring&&operation!=WR_RADIO_CLOSE&&operation!=WR_RADIO_BSS_CLOSE)return 0;
 if(operation==WR_RADIO_CLOSE){if(s->phase!=WR_RADIO_CLOSING)return 0;}
 else{
  if(s->exhausted&&operation!=WR_RADIO_BSS_CLOSE)return 0;
  if(s->reset_pending&&operation!=WR_RADIO_RESET&&operation!=WR_RADIO_BSS_CLOSE)return 0;
  if(operation==WR_RADIO_START){if(s->phase!=WR_RADIO_DOWN)return 0;}
  else if(operation==WR_RADIO_MAIN_OPEN){
   if(s->phase!=WR_RADIO_READY&&s->phase!=WR_RADIO_UNVERIFIED)return 0;
  }else if(operation==WR_RADIO_VERIFY){
   if((s->phase!=WR_RADIO_UNVERIFIED&&s->phase!=WR_RADIO_READY)||s->main_inhibited)return 0;
  }else if(operation==WR_RADIO_BSS_CLOSE){
   if(s->phase!=WR_RADIO_READY&&s->phase!=WR_RADIO_UNVERIFIED&&s->phase!=WR_RADIO_FAULT)return 0;
  }
  else if(operation==WR_RADIO_RESET){
   if((s->phase!=WR_RADIO_READY&&s->phase!=WR_RADIO_UNVERIFIED)||s->main_inhibited)return 0;
  }else if(operation==WR_RADIO_BSS_OPEN){
   if(s->phase!=WR_RADIO_READY||!s->main_ready)return 0;
  }else return 0;
 }
 /* Startup/reset can reconstruct adapter radio state. Invalidate work
  * queued before this reconstruction, even if the netdevice address survives. */
 if(operation==WR_RADIO_START||operation==WR_RADIO_MAIN_OPEN||operation==WR_RADIO_RESET){
  if(s->epoch==~0UL){s->exhausted=1;s->main_ready=0;s->phase=WR_RADIO_FAULT;return 0;}
  s->epoch++;
 }
 t->prior_phase=s->phase;t->prior_ready=s->main_ready;
 if(operation==WR_RADIO_START){s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;}
 if(operation==WR_RADIO_CLOSE||operation==WR_RADIO_BSS_CLOSE)s->virtual_down_stage=0;
 s->busy=operation;t->serial=++s->serial;t->epoch=s->epoch;t->operation=operation;
 t->reset_kind=operation==WR_RADIO_RESET?
   (s->reset_pending?(unsigned int)s->reset_pending:WR_RADIO_RESET_PDMA):0;
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
 s->busy=0;
 return 1;
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
/* BSS_CLOSE is selective: it must not request adapter CLOSE or clear main
 * readiness. Caller must prove it is not the last virtual-interface close;
 * last-reference teardown needs the adapter-wide closing protocol instead. */
/* observed_success includes required actual hardware/readback evidence.
 * A failure is uncertain: only teardown can recover this candidate state.
 * Close requested during admitted work must never be undone by late success. */
static inline int wr_iot_radio_finish(struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t,int observed_success){
 if(!s->epoch||!s->busy||s->busy!=t->operation||s->serial!=t->serial)return 0;
 /* Main-down/close may invalidate an already admitted ticket. */
 if(t->epoch!=s->epoch&&s->phase!=WR_RADIO_CLOSING&&!s->main_inhibited&&!s->reset_pending)return 0;
 s->busy=0;
 if(t->operation==WR_RADIO_CLOSE){
  s->phase=observed_success?WR_RADIO_DOWN:WR_RADIO_CLOSING;s->main_ready=0;
  if(observed_success)s->reset_pending=0;
 }else if(s->phase!=WR_RADIO_CLOSING&&t->operation==WR_RADIO_BSS_CLOSE&&observed_success){
  /* Teardown is not verification: preserve uncertainty/fault and pending intent. */
  s->phase=t->prior_phase;
  s->main_ready=t->prior_ready&&t->epoch==s->epoch&&!s->main_inhibited&&!s->reset_pending;
 }else if(s->phase!=WR_RADIO_CLOSING){
  s->phase=observed_success?WR_RADIO_READY:WR_RADIO_FAULT;
  if(observed_success&&t->epoch==s->epoch&&
     (t->operation==WR_RADIO_START||t->operation==WR_RADIO_MAIN_OPEN))s->main_inhibited=0;
  s->main_ready=!!observed_success&&!s->main_inhibited&&!s->reset_pending;
 }
 return 1;
}
/* Software wrapper returned success, but hardware readback is still missing.
 * Same caller-held lock covers finish and demotion: no READY is published. */
static inline int wr_iot_radio_finish_unverified(struct wr_iot_radio_transition *s,
 const struct wr_iot_radio_ticket *t){
 int finished=wr_iot_radio_finish(s,t,1);
 if(finished&&s->phase==WR_RADIO_READY){s->phase=WR_RADIO_UNVERIFIED;s->main_ready=0;}
 return finished;
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
