/* Serialized activation sequencing. Backend operations must check ownership,
 * observe success and support idempotent recovery. No backend is installed here. */
#ifndef WR_IOT_ACTIVATION_H
#define WR_IOT_ACTIVATION_H
enum wr_iot_activation_state {WR_IOT_INACTIVE,WR_IOT_STARTING,WR_IOT_ACTIVE,WR_IOT_RECOVERY};
enum wr_iot_activation_operation {
 WR_IOT_LOCK,WR_IOT_VALIDATE,WR_IOT_SNAPSHOT,WR_IOT_QUIESCE,
 WR_IOT_PROFILE,WR_IOT_BRIDGE_PREPARE,WR_IOT_ISOLATE,WR_IOT_DHCP_START,
 WR_IOT_ATTACH,WR_IOT_BRIDGE_UP,WR_IOT_BSS_UP,WR_IOT_OBSERVE,
 WR_IOT_BRIDGE_DOWN,WR_IOT_DETACH,WR_IOT_RESTORE,
 WR_IOT_BRIDGE_REMOVE,WR_IOT_GUARD_REMOVE
};
struct wr_iot_activation_backend {
 int (*perform)(void *,enum wr_iot_activation_operation);
 void (*unlock)(void *);
};
struct wr_iot_activation {
 enum wr_iot_activation_state state;
 const struct wr_iot_activation_backend *backend;
 void *context;
 int locked,snapshot;
 unsigned int recovery_step;
};
static inline int wr_iot_activation_call(struct wr_iot_activation *state,enum wr_iot_activation_operation op){
 return state->backend->perform(state->context,op)==1;
}
static inline void wr_iot_activation_release(struct wr_iot_activation *state){
 state->backend->unlock(state->context);state->locked=0;
}
/* Retain lock/snapshot/isolation if any recovery operation is unconfirmed.
 * A failed callback may have partially mutated its owned resource. Recovery
 * therefore runs every stage, even when activation failed before that stage. */
static inline int wr_iot_activation_recover(struct wr_iot_activation *state){
 static const enum wr_iot_activation_operation operations[]={
  WR_IOT_QUIESCE,WR_IOT_BRIDGE_DOWN,WR_IOT_DETACH,WR_IOT_RESTORE,
  WR_IOT_BRIDGE_REMOVE,WR_IOT_GUARD_REMOVE
 };
 unsigned int i;
 if(!state||state->state!=WR_IOT_RECOVERY||!state->locked||!state->snapshot)return 0;
 /* Recheck BSS quiescence on every retry; completed destructive stages
  * must not be repeated after their owned resource has disappeared. */
 if(state->recovery_step>sizeof(operations)/sizeof(operations[0]))return 0;
 if(!wr_iot_activation_call(state,WR_IOT_QUIESCE))return 0;
 if(!state->recovery_step)state->recovery_step=1;
 for(i=state->recovery_step;i<sizeof(operations)/sizeof(operations[0]);i++){
  if(!wr_iot_activation_call(state,operations[i]))return 0;
  state->recovery_step=i+1;
 }
 state->snapshot=0;state->recovery_step=0;wr_iot_activation_release(state);state->state=WR_IOT_INACTIVE;return 1;
}
static inline int wr_iot_activation_start(struct wr_iot_activation *state,const struct wr_iot_activation_backend *backend,void *context){
 static const enum wr_iot_activation_operation operations[]={
  WR_IOT_QUIESCE,WR_IOT_PROFILE,WR_IOT_BRIDGE_PREPARE,WR_IOT_ISOLATE,
  WR_IOT_ATTACH,WR_IOT_BRIDGE_UP,WR_IOT_DHCP_START,WR_IOT_BSS_UP,WR_IOT_OBSERVE
 };
 unsigned int i;
 /* Bring up the isolated gateway before probing DHCP/DNS on its subnet.
  * ra2 stays DOWN throughout; client access opens only after service readiness.
  * DHCP_START must prove protocol readiness, not merely launch a process. */
 if(!state||!backend||!backend->perform||!backend->unlock||state->state!=WR_IOT_INACTIVE||state->locked||state->snapshot)return 0;
 state->backend=backend;state->context=context;
 if(!wr_iot_activation_call(state,WR_IOT_LOCK))return 0;
 state->locked=1;
 /* Validation/snapshot callbacks must not mutate live network resources. */
 if(!wr_iot_activation_call(state,WR_IOT_VALIDATE)||!wr_iot_activation_call(state,WR_IOT_SNAPSHOT)){
  wr_iot_activation_release(state);return 0;
 }
 state->snapshot=1;state->state=WR_IOT_STARTING;
 for(i=0;i<sizeof(operations)/sizeof(operations[0]);i++){
  if(!wr_iot_activation_call(state,operations[i])){
   state->recovery_step=0;state->state=WR_IOT_RECOVERY;wr_iot_activation_recover(state);return 0;
  }
 }
 state->state=WR_IOT_ACTIVE;wr_iot_activation_release(state);return 1;
}
static inline int wr_iot_activation_stop(struct wr_iot_activation *state){
 if(!state)return 0;
 if(state->state==WR_IOT_INACTIVE)return !state->locked&&!state->snapshot;
 if(state->state==WR_IOT_ACTIVE){
  if(!wr_iot_activation_call(state,WR_IOT_LOCK))return 0;
  state->locked=1;state->recovery_step=0;state->state=WR_IOT_RECOVERY;
 }
 return wr_iot_activation_recover(state);
}
#endif
