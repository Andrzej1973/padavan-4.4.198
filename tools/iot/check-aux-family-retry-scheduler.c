#include "aux-family-retry-scheduler.h"
#include <assert.h>
#include <stdio.h>

static void ready(struct wr_iot_interface_ref *record,
 struct wr_iot_family_close *state,
 enum wr_iot_ref_family family){
 record->published=1;record->phase=WR_REF_CLOSING;
 record->family=family;
 record->close_stage=1;record->close_serial=17;
 record->close_epoch=11;record->last_token=9;
 state->device=record->device;state->generation=record->generation;
 state->serial=record->close_serial;state->epoch=record->close_epoch;
 state->token=record->last_token;state->family=family;
 state->phase=WR_FAMILY_DOWN_RETRY;
}

/* Enumerate cancellation boundaries; these are model checks, not kernel
 * concurrency or workqueue execution evidence. */
static void stop_boundaries(void){
 int device=0,drop=0,stage;
 for(stage=0;stage<3;stage++){
  struct wr_iot_interface_ref record;
  struct wr_iot_family_close state;
  struct wr_iot_aux_retry_owner owner;
  wr_iot_ref_init(&record,&device,5);
  wr_iot_family_close_init(&state);
  ready(&record,&state,WR_REF_FAMILY_APCLI);
  wr_iot_aux_retry_init(&owner);
  assert(wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
  if(stage>0)assert(wr_iot_aux_retry_begin(&owner,&record,&state));
  if(stage>1)assert(wr_iot_aux_retry_action(&owner,&record,&state));
  assert(wr_iot_aux_retry_request_stop(&owner));
  assert(!wr_iot_aux_retry_action(&owner,&record,&state));
  assert(!wr_iot_aux_retry_release_ready(&owner,1));
  if(stage<2){
   assert(wr_iot_aux_retry_abandon(&owner));
   assert(!wr_iot_aux_retry_complete(&owner,1,&drop));
   assert(owner.netdev_held&&owner.module_pin_held&&owner.deferred_owners==1);
  }else{
   /* An already claimed exact action may finish during stop. Stale
    * completion must retain ownership, even if it reports pin release. */
   record.phase=WR_REF_IDLE;record.close_stage=2;
   state.phase=WR_FAMILY_CLOSE_DONE;
   record.generation++;
   assert(!wr_iot_aux_retry_mark_completed(&owner,&record,&state,1));
   record.generation--;
   assert(wr_iot_aux_retry_mark_completed(&owner,&record,&state,1));
   assert(!wr_iot_aux_retry_complete(&owner,0,&drop));
   assert(wr_iot_aux_retry_complete(&owner,1,&drop)&&drop);
   assert(wr_iot_aux_retry_release_ready(&owner,1));
  }
 }
}

static void rejected_submission_budget(void){
 int device=0;
 struct wr_iot_interface_ref record;
 struct wr_iot_family_close state;
 struct wr_iot_aux_retry_owner owner;
 wr_iot_ref_init(&record,&device,5);wr_iot_family_close_init(&state);
 ready(&record,&state,WR_REF_FAMILY_APCLI);wr_iot_aux_retry_init(&owner);
 assert(wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 assert(wr_iot_aux_retry_schedule_result(&owner,0));
 assert(owner.attempts==0&&owner.failed_submissions==1);
 assert(wr_iot_aux_retry_rearm_retained(&owner,&record,&state,1,2));
 assert(wr_iot_aux_retry_schedule_result(&owner,0));
 assert(owner.attempts==0&&owner.failed_submissions==2);
 assert(!wr_iot_aux_retry_rearm_retained(&owner,&record,&state,1,2));
 assert(owner.netdev_held&&owner.module_pin_held&&owner.deferred_owners==1);
 assert(!wr_iot_aux_retry_release_ready(&owner,1));
}

static void retained_rearm(void){
 int device=0;
 struct wr_iot_interface_ref record;
 struct wr_iot_family_close state;
 struct wr_iot_aux_retry_owner owner;
 wr_iot_ref_init(&record,&device,5);wr_iot_family_close_init(&state);
 ready(&record,&state,WR_REF_FAMILY_MONITOR);wr_iot_aux_retry_init(&owner);
 assert(wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 assert(wr_iot_aux_retry_begin(&owner,&record,&state));
 assert(wr_iot_aux_retry_action(&owner,&record,&state));
 assert(wr_iot_aux_retry_retain(&owner));
 assert(!wr_iot_aux_retry_rearm_retained(&owner,&record,&state,0,2));
 assert(!wr_iot_aux_retry_rearm_retained(&owner,&record,&state,1,1));
 record.generation++;
 assert(!wr_iot_aux_retry_rearm_retained(&owner,&record,&state,1,2));
 record.generation--;
 assert(wr_iot_aux_retry_rearm_retained(&owner,&record,&state,1,2));
 assert(owner.deferred_owners==1&&owner.netdev_held&&owner.module_pin_held);
 assert(wr_iot_aux_retry_begin(&owner,&record,&state));
 assert(wr_iot_aux_retry_action(&owner,&record,&state));
 assert(wr_iot_aux_retry_retain(&owner));
 assert(!wr_iot_aux_retry_rearm_retained(&owner,&record,&state,1,2));
 assert(wr_iot_aux_retry_request_stop(&owner));
 assert(!wr_iot_aux_retry_rearm_retained(&owner,&record,&state,1,3));
 assert(!wr_iot_aux_retry_release_ready(&owner,1));
}

int main(void){
 retained_rearm();
 rejected_submission_budget();
 stop_boundaries();
 int device=0;
 struct wr_iot_interface_ref record;
 struct wr_iot_family_close state;
 struct wr_iot_aux_retry_owner owner;
 int drop=0;
 wr_iot_ref_init(&record,&device,5);
 wr_iot_family_close_init(&state);
 ready(&record,&state,WR_REF_FAMILY_APCLI);
 wr_iot_aux_retry_init(&owner);

 state.family=WR_REF_FAMILY_WDS;
 assert(!wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 state.family=WR_REF_FAMILY_APCLI;
 state.phase=WR_FAMILY_CLOSE_CONFIRMED;
 assert(!wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 state.phase=WR_FAMILY_DOWN_RETRY;
 assert(!wr_iot_aux_retry_queue(&owner,&record,&state,0,1,1));
 assert(!wr_iot_aux_retry_queue(&owner,&record,&state,1,0,1));
 assert(!wr_iot_aux_retry_queue(&owner,&record,&state,1,1,0));
 assert(wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 assert(owner.deferred_owners==1&&owner.phase==WR_AUX_RETRY_QUEUED);
 assert(!wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 assert(!wr_iot_aux_retry_release_ready(&owner,1));

 /* A rejected submission retains every claim; it never looks complete. */
 assert(wr_iot_aux_retry_schedule_result(&owner,0));
 assert(owner.phase==WR_AUX_RETRY_RETAINED&&owner.failed_submissions==1);
 assert(owner.netdev_held&&owner.module_pin_held&&owner.deferred_owners==1);
 assert(!wr_iot_aux_retry_release_ready(&owner,1));
 assert(wr_iot_aux_retry_request_stop(&owner));
 assert(owner.phase==WR_AUX_RETRY_STOPPING);
 assert(!wr_iot_aux_retry_begin(&owner,&record,&state));
 assert(wr_iot_aux_retry_abandon(&owner));
 assert(owner.phase==WR_AUX_RETRY_STOPPING);
 assert(!wr_iot_aux_retry_release_ready(&owner,1));

 wr_iot_aux_retry_init(&owner);
 ready(&record,&state,WR_REF_FAMILY_APCLI);
 assert(wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 assert(wr_iot_aux_retry_schedule_result(&owner,1));
 assert(wr_iot_aux_retry_begin(&owner,&record,&state));
 record.close_serial++;
 assert(!wr_iot_aux_retry_action(&owner,&record,&state));
 record.close_serial--;
 state.epoch++;
 assert(!wr_iot_aux_retry_action(&owner,&record,&state));
 state.epoch--;
 assert(wr_iot_aux_retry_action(&owner,&record,&state));
 assert(!wr_iot_aux_retry_action(&owner,&record,&state));

 /* A successful helper consumes the record and module pin; a failed helper
   retains all ownership and cannot be mistaken for completion. */
 record.phase=WR_REF_IDLE;record.close_stage=2;
 state.phase=WR_FAMILY_CLOSE_DONE;
 assert(!wr_iot_aux_retry_mark_completed(&owner,&record,&state,0));
 assert(wr_iot_aux_retry_mark_completed(&owner,&record,&state,1));
 assert(owner.completed&&!owner.module_pin_held&&owner.deferred_owners==1);
 assert(!wr_iot_aux_retry_complete(&owner,0,&drop));
 assert(wr_iot_aux_retry_complete(&owner,1,&drop)&&drop);
 owner.work_joined=1;
 assert(wr_iot_aux_retry_release_ready(&owner,1));

 wr_iot_aux_retry_init(&owner);
 ready(&record,&state,WR_REF_FAMILY_MONITOR);
 assert(wr_iot_aux_retry_queue(&owner,&record,&state,1,1,1));
 assert(wr_iot_aux_retry_schedule_result(&owner,1));
 assert(wr_iot_aux_retry_begin(&owner,&record,&state));
 record.close_epoch++;
 assert(!wr_iot_aux_retry_action(&owner,&record,&state));
 record.close_epoch--;
 assert(wr_iot_aux_retry_action(&owner,&record,&state));
 assert(wr_iot_aux_retry_retain(&owner));
 assert(owner.phase==WR_AUX_RETRY_RETAINED);
 assert(owner.netdev_held&&owner.module_pin_held&&owner.deferred_owners==1);
 assert(!wr_iot_aux_retry_complete(&owner,1,&drop));
 assert(wr_iot_aux_retry_request_stop(&owner));
 assert(!wr_iot_aux_retry_release_ready(&owner,1));
 puts("PASS auxiliary retry retains netdev/module/adapter until joined completion");
 return 0;
}
