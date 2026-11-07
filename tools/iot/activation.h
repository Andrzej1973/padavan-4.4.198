/* Serialized activation sequencing. The caller must serialize access to this
 * state object through one RC control worker; the backend LOCK additionally
 * owns network mutations. The stock RC fatal-signal handler calls router
 * shutdown directly, outside its notification loop, so one worker alone
 * does not exclude teardown. A production backend must fence that path too.
 * Post-LOCK checks reject stale logical admissions, but do not make
 * unsynchronized C access to state safe. Backend operations must check
 * ownership, observe success and support idempotent recovery. No backend
 * is installed here. */
#ifndef WR_IOT_ACTIVATION_H
#define WR_IOT_ACTIVATION_H
enum wr_iot_activation_state {WR_IOT_INACTIVE,WR_IOT_STARTING,WR_IOT_ACTIVE,WR_IOT_RECOVERY};
enum wr_iot_activation_operation {
 WR_IOT_LOCK,WR_IOT_VALIDATE,WR_IOT_SNAPSHOT,WR_IOT_QUIESCE,
 WR_IOT_PROFILE,WR_IOT_BRIDGE_PREPARE,WR_IOT_ISOLATE,WR_IOT_DHCP_START,
 WR_IOT_ATTACH,WR_IOT_BRIDGE_UP,WR_IOT_BSS_UP,WR_IOT_OBSERVE,
 WR_IOT_BRIDGE_DOWN,WR_IOT_DETACH,WR_IOT_RESTORE,
 WR_IOT_BRIDGE_REMOVE,WR_IOT_GUARD_REMOVE,
 WR_IOT_POLICY,WR_IOT_RADIO_PREPARE,
 WR_IOT_DISABLE_SNAPSHOT,WR_IOT_DISABLE_APPLY,WR_IOT_DISABLE_OBSERVE,
 WR_IOT_DISABLE_COMMIT,WR_IOT_DISABLE_SERVICES,
 WR_IOT_MAIN_RADIO_READY,
 WR_IOT_RESERVED_READY,WR_IOT_RESERVED_RESTORE,WR_IOT_RESERVED_DISABLE_APPLY
};
struct wr_iot_activation_backend {
 /* QUIESCE must establish driver/RF safety for subsequent teardown, not just
  * Linux administrative DOWN. Vendor queue-recovery helpers can restart BCN
  * transmission even after a flush timeout; an IDLE software state is not a
  * drain receipt. Unverified quiescence must fail and retain recovery/isolation. */
 /* A transport-completed MCU command is also insufficient: require a bounded
  * matching firmware success response with proven callback lifetime, followed
  * by the required hardware observation. Never infer this from RADIO_OFF. */
 int (*perform)(void *,enum wr_iot_activation_operation);
 void (*unlock)(void *);
 /* Poll only outside signal context, between bounded backend operations.
  * A pending normal shutdown aborts START into the existing recovery path. */
 int (*cancel_requested)(void *);
};
struct wr_iot_activation {
 enum wr_iot_activation_state state;
 const struct wr_iot_activation_backend *backend;
 void *context;
 int locked,snapshot,disabling;
 int precreated; /* selected under service lock, immutable through recovery */
 unsigned int recovery_step;
 unsigned long long generation;
};
static inline int wr_iot_activation_call(struct wr_iot_activation *state,enum wr_iot_activation_operation op){
 if(state->precreated){
  if(op==WR_IOT_PROFILE||op==WR_IOT_RADIO_PREPARE)return 0;
  if(op==WR_IOT_RESTORE)op=WR_IOT_RESERVED_RESTORE;
  if(op==WR_IOT_DISABLE_APPLY)op=WR_IOT_RESERVED_DISABLE_APPLY;
 }
 return state->backend->perform(state->context,op)==1;
}
static inline void wr_iot_activation_release(struct wr_iot_activation *state){
 state->backend->unlock(state->context);state->locked=0;
}
/* Retain lock/snapshot/isolation if any recovery operation is unconfirmed.
 * A failed callback may have partially mutated its owned resource. Recovery
 * therefore runs every stage, even when activation failed before that stage. */
static inline int wr_iot_activation_recover(struct wr_iot_activation *state){
 static const enum wr_iot_activation_operation rollback[]={
  WR_IOT_QUIESCE,WR_IOT_BRIDGE_DOWN,WR_IOT_DETACH,WR_IOT_BRIDGE_REMOVE,
  WR_IOT_RESTORE,WR_IOT_GUARD_REMOVE
 };
 static const enum wr_iot_activation_operation disable[]={
  WR_IOT_QUIESCE,WR_IOT_ISOLATE,WR_IOT_DISABLE_SERVICES,WR_IOT_BRIDGE_DOWN,WR_IOT_DETACH,
  WR_IOT_BRIDGE_REMOVE,WR_IOT_DISABLE_APPLY,WR_IOT_DISABLE_OBSERVE,
  WR_IOT_GUARD_REMOVE,WR_IOT_DISABLE_COMMIT
 };
 const enum wr_iot_activation_operation *operations;
 unsigned int i,count;
 if(!state||state->state!=WR_IOT_RECOVERY||!state->locked||!state->snapshot)return 0;
 if(state->disabling!=0&&state->disabling!=1)return 0;
 if(state->precreated!=0&&state->precreated!=1)return 0;
 operations=state->disabling?disable:rollback;
 count=state->disabling?sizeof(disable)/sizeof(disable[0]):sizeof(rollback)/sizeof(rollback[0]);
 /* Startup rollback's captured baseline has no IoT bridge. Remove the owned, down, empty
  * bridge before restoring temporary settings, which refuse a live bridge.
  * Keep isolation until settings and previous services are restored.
  * Recheck BSS quiescence on every retry; completed destructive stages
  * must not be repeated after their owned resource has disappeared. Normal
  * disable instead uses its fresh stop transaction and never calls RESTORE. */
 if(state->recovery_step>count)return 0;
 if(!wr_iot_activation_call(state,WR_IOT_QUIESCE))return 0;
 if(!state->recovery_step)state->recovery_step=1;
 for(i=state->recovery_step;i<count;i++){
  if(!wr_iot_activation_call(state,operations[i]))return 0;
  state->recovery_step=i+1;
 }
 state->snapshot=0;state->recovery_step=0;state->disabling=0;wr_iot_activation_release(state);state->state=WR_IOT_INACTIVE;return 1;
}
static inline int wr_iot_activation_start_mode(struct wr_iot_activation *state,const struct wr_iot_activation_backend *backend,void *context,int precreated){
 static const enum wr_iot_activation_operation operations[]={
  WR_IOT_QUIESCE,WR_IOT_PROFILE,WR_IOT_BRIDGE_PREPARE,WR_IOT_ISOLATE,
  WR_IOT_RADIO_PREPARE,
  WR_IOT_ATTACH,WR_IOT_BRIDGE_UP,WR_IOT_DHCP_START,WR_IOT_POLICY,
  WR_IOT_MAIN_RADIO_READY,WR_IOT_BSS_UP,WR_IOT_OBSERVE
 };
 static const enum wr_iot_activation_operation reserved_operations[]={
  WR_IOT_QUIESCE,WR_IOT_RESERVED_READY,WR_IOT_BRIDGE_PREPARE,WR_IOT_ISOLATE,
  WR_IOT_ATTACH,WR_IOT_BRIDGE_UP,WR_IOT_DHCP_START,WR_IOT_POLICY,
  WR_IOT_MAIN_RADIO_READY,WR_IOT_BSS_UP,WR_IOT_OBSERVE
 };
 const enum wr_iot_activation_operation *selected=precreated?reserved_operations:operations;
 unsigned int count=precreated?sizeof(reserved_operations)/sizeof(reserved_operations[0]):sizeof(operations)/sizeof(operations[0]);
 unsigned int i;
 if(precreated!=0&&precreated!=1)return 0;
 /* Bring up the isolated gateway before probing DHCP/DNS on its subnet.
  * ra2 stays DOWN throughout; client access opens only after service readiness.
  * DHCP_START must prove protocol readiness, not merely launch a process. */
 /* POLICY applies and observes the scoped DHCP/DNS/WAN policy while BSS is
  * still down. The earlier ISOLATE operation establishes full quarantine. */
 /* MAIN_RADIO_READY observes the main 2.4 GHz interface UP on the expected
  * adapter and IoT BSS still DOWN after radio preparation. This observation
  * grants no future permission: BSS_UP must revalidate adapter generation,
  * main-radio readiness and absence of close/reset under the SAME driver
  * transition owner as its opening mutation. The outer RC lock alone cannot
  * exclude watchdog, manual radio controls or driver teardown. Reject stale
  * readiness without opening BSS; preserve recovery on uncertain mutation. */
 /* PROFILE may quiesce the main radio and generate its candidate file, but
  * must not reopen the radio or create/open the candidate BSS. RADIO_PREPARE
  * reloads/creates it only after quarantine exists, and succeeds only with
  * ra2 observed DOWN. A failed callback may have partially opened it; retained
  * recovery must quiesce it before any teardown. QUIESCE on recovery targets
  * IoT, not a previously restored main/guest radio. RESTORE owns that radio
  * rollback and must observe the original main/guest state before returning. */
 if(!state||!backend||!backend->perform||!backend->unlock||!backend->cancel_requested||state->state!=WR_IOT_INACTIVE||state->locked||state->snapshot||state->disabling)return 0;
 /* The optimistic check above can become stale while LOCK waits. Do not
  * publish a new backend/context into shared state before owning that lock. */
 if(backend->perform(context,WR_IOT_LOCK)!=1)return 0;
 if(state->state!=WR_IOT_INACTIVE||state->locked||state->snapshot||state->disabling){
  backend->unlock(context);return 0;
 }
 if(state->generation==~0ULL){backend->unlock(context);return 0;}
 /* A shutdown that arrived while waiting for LOCK must not start even the
  * read-only snapshot. Leave the old state and generation untouched. */
 if(backend->cancel_requested(context)){backend->unlock(context);return 0;}
 state->backend=backend;state->context=context;state->locked=1;
 state->precreated=precreated;
 state->generation++;
 /* Validation/snapshot callbacks must not mutate live network resources. */
 if(!wr_iot_activation_call(state,WR_IOT_VALIDATE)||!wr_iot_activation_call(state,WR_IOT_SNAPSHOT)){
  wr_iot_activation_release(state);return 0;
 }
 state->snapshot=1;state->state=WR_IOT_STARTING;
 for(i=0;i<count;i++){
  if(backend->cancel_requested(context)||!wr_iot_activation_call(state,selected[i])){
   state->recovery_step=0;state->state=WR_IOT_RECOVERY;wr_iot_activation_recover(state);return 0;
  }
 }
 if(backend->cancel_requested(context)){
  state->recovery_step=0;state->state=WR_IOT_RECOVERY;wr_iot_activation_recover(state);return 0;
 }
 state->state=WR_IOT_ACTIVE;wr_iot_activation_release(state);return 1;
}
/* Reserved callbacks are deliberately distinct: legacy backends must refuse
 * unknown operations instead of silently regenerating/reloading a profile.
 * READY proves loaded identity/credentials and closed BSS under current owner;
 * it must never provision, restart, scan or invoke global SSID/auth setters.
 * RESERVED_RESTORE / DISABLE_APPLY restore only scoped network/service state,
 * keep the reserved profile intact and observe current Main/Guest unchanged. */
static inline int wr_iot_activation_start(struct wr_iot_activation *s,const struct wr_iot_activation_backend *b,void *c){
 return wr_iot_activation_start_mode(s,b,c,0);
}
static inline int wr_iot_activation_start_precreated(struct wr_iot_activation *s,const struct wr_iot_activation_backend *b,void *c){
 return wr_iot_activation_start_mode(s,b,c,1);
}
static inline int wr_iot_activation_stop(struct wr_iot_activation *state){
 unsigned long long generation;
 if(!state)return 0;
 if(state->state==WR_IOT_INACTIVE)return !state->locked&&!state->snapshot&&!state->disabling;
 if(state->state==WR_IOT_ACTIVE){
  generation=state->generation;
  if(!wr_iot_activation_call(state,WR_IOT_LOCK))return 0;
  /* A preceding stop or a stop followed by a new start may have completed
   * while this caller waited. Never stop that newer activation. */
  if(state->generation!=generation||state->state!=WR_IOT_ACTIVE||
     state->locked||!state->snapshot||state->disabling){
   state->backend->unlock(state->context);
   return state->generation==generation&&state->state==WR_IOT_INACTIVE&&
          !state->locked&&!state->snapshot&&!state->disabling;
  }
  state->locked=1;
  /* Read-only snapshot of CURRENT desired main/guest/services before normal
   * OFF. Failure must leave ACTIVE unchanged. SERVICES prepares/commits normal
   * DNS/DHCP while the owned bridge still exists so its current baseline can
   * recover on failure. BSS remains closed/quarantined. APPLY removes owned IoT state
   * using this new transaction, never the historical startup baseline.
   * OBSERVE verifies current main/guest/services plus IoT absence; COMMIT
   * releases the stop snapshot only after successful teardown. All steps
   * support retry; no failed normal stop may reopen the IoT BSS. */
  if(!wr_iot_activation_call(state,WR_IOT_DISABLE_SNAPSHOT)){
   wr_iot_activation_release(state);return 0;
  }
  state->disabling=1;state->recovery_step=0;state->state=WR_IOT_RECOVERY;
 }
 return wr_iot_activation_recover(state);
}
#endif
