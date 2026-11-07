#include "activation.h"
#include "rc-shutdown-admission.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static void signal_shutdown(int sig){
 assert(sig==SIGTERM);
 assert(wr_iot_rc_shutdown_note(sig));
}
struct fixture {int fail,partial_fail,recovery_fail,locked,unlocks,live,guard,dhcp,policy,attached,bridge,profile,restores,exists,radio_prepared;
 int main_config,stop_config,stop_snapshot,disable_applies,main_ready,main_radio_missing,lose_radio_after_ready,bss_open_calls;
 int cancel_after,cancelled,cancel_polls,cancel_recovery_fail,signal_after;
 struct wr_iot_activation *state_on_lock;
 enum wr_iot_activation_state lock_state;
 int lock_bump_generation;};
static int operation(void *context,enum wr_iot_activation_operation op){
 struct fixture *f=context;
 if(op==WR_IOT_LOCK){if(f->fail==(int)op+1)return 0;assert(!f->locked);f->locked=1;
  if(f->state_on_lock){
   f->state_on_lock->state=f->lock_state;
   if(f->lock_bump_generation)f->state_on_lock->generation++;
  }
  return 1;}
 assert(f->locked);
 if(f->fail==(int)op+1){f->fail=0;return 0;}
 if(f->recovery_fail==(int)op+1)return 0;
 switch(op){
 case WR_IOT_QUIESCE:f->live=0;break;
 case WR_IOT_PROFILE:f->profile=1;break;
 case WR_IOT_BRIDGE_PREPARE:f->exists=1;break;
 case WR_IOT_ISOLATE:f->guard=1;break;
 case WR_IOT_RADIO_PREPARE:assert(!f->live&&f->profile&&f->exists&&f->guard&&!f->attached&&!f->dhcp);f->radio_prepared=1;break;
 case WR_IOT_DHCP_START:assert(!f->live&&f->guard&&f->attached&&f->bridge);f->dhcp=1;break;
 case WR_IOT_ATTACH:assert(!f->live&&f->guard&&f->radio_prepared&&!f->dhcp);f->attached=1;break;
 case WR_IOT_BRIDGE_UP:assert(!f->live&&f->attached&&f->guard&&!f->dhcp);f->bridge=1;break;
 case WR_IOT_POLICY:assert(!f->live&&f->attached&&f->bridge&&f->guard&&f->dhcp);f->policy=1;break;
 case WR_IOT_MAIN_RADIO_READY:assert(!f->live&&f->radio_prepared&&f->attached&&f->guard&&f->dhcp&&f->policy);if(f->main_radio_missing)return 0;f->main_ready=1;if(f->lose_radio_after_ready)f->main_radio_missing=1;break;
 case WR_IOT_BSS_UP:if(f->main_radio_missing)return 0;f->bss_open_calls++;assert(!f->live&&f->main_ready&&f->radio_prepared&&f->attached&&f->bridge&&f->guard&&f->dhcp&&f->policy);f->live=1;break;
 case WR_IOT_OBSERVE:assert(f->live&&f->guard&&f->dhcp);break;
 case WR_IOT_BRIDGE_DOWN:assert(!f->live);f->bridge=0;break;
 case WR_IOT_DETACH:assert(!f->live&&!f->bridge);f->attached=0;break;
 case WR_IOT_RESTORE:assert(!f->live&&!f->attached&&!f->bridge&&!f->exists);f->dhcp=0;f->policy=0;f->profile=0;f->radio_prepared=0;f->main_ready=0;f->restores++;break;
 case WR_IOT_BRIDGE_REMOVE:assert(!f->live&&!f->attached&&!f->bridge);f->exists=0;break;
 case WR_IOT_GUARD_REMOVE:assert(!f->live&&!f->attached&&!f->bridge&&!f->dhcp);f->guard=0;break;
 case WR_IOT_VALIDATE:case WR_IOT_SNAPSHOT:break;
 case WR_IOT_DISABLE_SNAPSHOT:f->stop_config=f->main_config;f->stop_snapshot=1;break;
 case WR_IOT_DISABLE_SERVICES:
  assert(!f->live&&f->guard&&f->exists&&f->bridge&&f->stop_snapshot);
  assert(f->main_config==f->stop_config);f->dhcp=f->policy=0;break;
 case WR_IOT_DISABLE_APPLY:
  assert(!f->live&&f->guard&&!f->exists&&!f->attached&&f->stop_snapshot);
  assert(f->main_config==f->stop_config);
  f->dhcp=f->policy=f->profile=f->radio_prepared=0;f->disable_applies++;break;
 case WR_IOT_DISABLE_OBSERVE:
  assert(!f->live&&!f->dhcp&&!f->exists&&f->main_config==f->stop_config);break;
 case WR_IOT_DISABLE_COMMIT:
  assert(!f->live&&!f->guard&&!f->dhcp&&f->main_config==f->stop_config);
  f->stop_snapshot=0;break;
 default:assert(0);return 0;
 }
 if(f->partial_fail==(int)op+1){
  /* Model a vendor reload opening ra2 before failing its DOWN observation. */
  if(op==WR_IOT_RADIO_PREPARE){assert(f->guard);f->live=1;}
  f->partial_fail=0;return 0;
 }
 if(f->cancel_after==(int)op+1){
  f->cancelled=1;
  f->recovery_fail=f->cancel_recovery_fail;
 }
 if(f->signal_after==(int)op+1)assert(raise(SIGTERM)==0);
 return 1;
}
static void unlock(void *context){struct fixture *f=context;assert(f->locked);f->locked=0;f->unlocks++;}
static int cancel_requested(void *context){struct fixture *f=context;assert(f->locked);f->cancel_polls++;return f->cancelled||wr_iot_rc_shutdown.pending!=0;}
int main(void){
 const struct wr_iot_activation_backend backend={operation,unlock,cancel_requested};
 const struct wr_iot_activation_backend missing_cancel={operation,unlock,NULL};
 struct wr_iot_activation state;struct fixture f;int fail;
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 assert(!wr_iot_activation_start(&state,&missing_cancel,&f));
 assert(!f.locked&&!f.profile&&!f.guard&&!f.cancel_polls);
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));f.cancelled=1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_INACTIVE&&!state.generation&&!state.backend);
 assert(!f.locked&&!f.profile&&!f.guard&&f.cancel_polls==1&&f.unlocks==1);
 /* Another request completed activation while this request waited on LOCK.
  * The stale pre-lock INACTIVE check must not trigger a second mutation. */
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 f.state_on_lock=&state;f.lock_state=WR_IOT_ACTIVE;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_ACTIVE&&!state.locked&&!state.snapshot);
 assert(!f.locked&&f.unlocks==1&&!f.profile&&!f.guard&&!f.bss_open_calls);
 assert(!state.backend&&!state.context);
 /* A queued stop must not stop a later activation with the same ACTIVE
  * state after the transition lock is acquired. */
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 assert(wr_iot_activation_start(&state,&backend,&f));
 f.state_on_lock=&state;f.lock_state=WR_IOT_ACTIVE;f.lock_bump_generation=1;
 assert(!wr_iot_activation_stop(&state));
 assert(state.state==WR_IOT_ACTIVE&&!state.locked&&f.live&&!f.locked);
 assert(!f.stop_snapshot&&!f.disable_applies);
 f.state_on_lock=NULL;f.lock_bump_generation=0;
 assert(wr_iot_activation_stop(&state));
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 assert(wr_iot_activation_start(&state,&backend,&f));assert(state.state==WR_IOT_ACTIVE&&f.live&&!f.locked);
 assert(!wr_iot_activation_start(&state,&backend,&f));
 f.recovery_fail=WR_IOT_QUIESCE+1;assert(!wr_iot_activation_stop(&state));
 assert(state.state==WR_IOT_RECOVERY&&state.snapshot&&f.locked&&f.guard&&f.live);
 f.recovery_fail=0;assert(wr_iot_activation_stop(&state));assert(!f.live&&!f.guard&&!f.locked&&!state.snapshot);
 assert(wr_iot_activation_stop(&state));
 for(fail=WR_IOT_LOCK+1;fail<=WR_IOT_SNAPSHOT+1;fail++){
  memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));f.fail=fail;
  assert(!wr_iot_activation_start(&state,&backend,&f));
  assert(state.state==WR_IOT_INACTIVE&&!f.locked&&!state.snapshot&&!f.live&&!f.guard);
 }
 {
  static const enum wr_iot_activation_operation stages[]={
   WR_IOT_QUIESCE,WR_IOT_PROFILE,WR_IOT_BRIDGE_PREPARE,WR_IOT_ISOLATE,
   WR_IOT_RADIO_PREPARE,
   WR_IOT_ATTACH,WR_IOT_BRIDGE_UP,WR_IOT_DHCP_START,WR_IOT_POLICY,
   WR_IOT_MAIN_RADIO_READY,WR_IOT_BSS_UP,WR_IOT_OBSERVE
  };
  size_t i;
  for(i=0;i<sizeof(stages)/sizeof(stages[0]);i++){
   memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
   f.fail=stages[i]+1;
   assert(!wr_iot_activation_start(&state,&backend,&f));
   assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked);
   assert(!f.live&&!f.guard&&!f.radio_prepared);
   memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
   f.partial_fail=stages[i]+1;
   assert(!wr_iot_activation_start(&state,&backend,&f));
   assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked);
   assert(!f.live&&!f.guard&&!f.dhcp&&!f.policy&&!f.attached);
   assert(!f.bridge&&!f.profile&&!f.exists&&!f.radio_prepared&&!f.main_ready&&f.restores==1);
  }
 }
 for(fail=WR_IOT_BRIDGE_DOWN+1;fail<=WR_IOT_GUARD_REMOVE+1;fail++){
  memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
  f.partial_fail=WR_IOT_OBSERVE+1;f.recovery_fail=fail;
  assert(!wr_iot_activation_start(&state,&backend,&f));assert(state.state==WR_IOT_RECOVERY&&f.locked&&state.snapshot);
  f.recovery_fail=0;assert(wr_iot_activation_stop(&state));assert(state.state==WR_IOT_INACTIVE&&!f.locked&&!f.guard&&f.restores==1);
 }
 {
  static const enum wr_iot_activation_operation stages[]={
   WR_IOT_QUIESCE,WR_IOT_ISOLATE,WR_IOT_DISABLE_SERVICES,WR_IOT_BRIDGE_DOWN,WR_IOT_DETACH,
   WR_IOT_BRIDGE_REMOVE,WR_IOT_DISABLE_APPLY,WR_IOT_DISABLE_OBSERVE,
   WR_IOT_GUARD_REMOVE,WR_IOT_DISABLE_COMMIT
  };
  size_t i;
  for(i=0;i<sizeof(stages)/sizeof(stages[0]);i++){
   int partial;
   for(partial=0;partial<=1;partial++){
    memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
    assert(wr_iot_activation_start(&state,&backend,&f));f.main_config=42;
    if(partial)f.partial_fail=stages[i]+1;else f.fail=stages[i]+1;
    assert(!wr_iot_activation_stop(&state));
    assert(state.state==WR_IOT_RECOVERY&&state.disabling&&state.snapshot&&f.locked);
    if(stages[i]==WR_IOT_DISABLE_SERVICES)assert(f.exists&&f.bridge&&f.guard&&!f.live);
    assert(f.main_config==42&&!f.restores);
    assert(wr_iot_activation_stop(&state));
    assert(state.state==WR_IOT_INACTIVE&&!state.disabling&&!f.live&&!f.guard&&!f.locked);
    assert(f.main_config==42&&!f.restores&&!f.stop_snapshot);
   }
  }
  memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
  assert(wr_iot_activation_start(&state,&backend,&f));f.main_config=42;
  f.fail=WR_IOT_LOCK+1;
  assert(!wr_iot_activation_stop(&state)&&state.state==WR_IOT_ACTIVE&&!f.locked&&f.live);
  f.fail=WR_IOT_DISABLE_SNAPSHOT+1;
  assert(!wr_iot_activation_stop(&state));
  assert(state.state==WR_IOT_ACTIVE&&!state.disabling&&!f.locked&&f.live&&f.main_config==42);
  assert(wr_iot_activation_stop(&state)&&!f.restores&&f.main_config==42);
 }
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));f.fail=WR_IOT_POLICY+1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_INACTIVE&&!f.live&&!f.policy&&!f.locked&&!f.guard);
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 f.partial_fail=WR_IOT_RADIO_PREPARE+1;f.recovery_fail=WR_IOT_RESTORE+1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_RECOVERY&&state.snapshot&&f.locked&&f.guard&&f.radio_prepared&&!f.live);
 f.recovery_fail=0;assert(wr_iot_activation_stop(&state));
 assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked&&!f.guard&&!f.radio_prepared);
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));f.main_radio_missing=1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked&&!f.live);
 assert(!f.main_ready&&!f.radio_prepared&&!f.guard&&!f.exists&&!f.attached&&!f.bridge&&f.restores==1);
 /* Readiness passed, then radio closed/reset before BSS_UP. The backend
  * must refuse the stale observation before any opening mutation. */
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));f.lose_radio_after_ready=1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(!f.bss_open_calls&&!f.live&&f.restores==1);
 assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked&&!f.guard);
 /* A normal shutdown arrives after radio preparation. The next mutating
  * stage must not run, and the owned snapshot must be recovered. */
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 f.cancel_after=WR_IOT_RADIO_PREPARE+1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked);
 assert(!f.attached&&!f.live&&!f.guard&&!f.radio_prepared&&f.restores==1);
 assert(f.cancel_polls>0);
 /* A shutdown after final OBSERVE still rolls back a newly opened BSS. */
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 f.cancel_after=WR_IOT_OBSERVE+1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked);
 assert(!f.live&&!f.guard&&!f.attached&&f.restores==1);
 /* A canceled start whose quiescence is not proven must retain recovery,
  * the owner lock and quarantine instead of declaring a clean abort. */
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 f.cancel_after=WR_IOT_RADIO_PREPARE+1;
 f.cancel_recovery_fail=WR_IOT_QUIESCE+1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_RECOVERY&&state.snapshot&&state.locked);
 assert(f.locked&&f.guard&&!f.attached&&!f.live);
 f.recovery_fail=0;
 assert(wr_iot_activation_stop(&state));
 assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked&&!f.guard);
 /* Model the RC signal marker as the backend's cancellation source. */
 memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
 assert(signal(SIGTERM,signal_shutdown)!=SIG_ERR);
 assert(wr_iot_rc_shutdown_begin());
 f.signal_after=WR_IOT_RADIO_PREPARE+1;
 assert(!wr_iot_activation_start(&state,&backend,&f));
 assert(state.state==WR_IOT_INACTIVE&&!state.snapshot&&!f.locked);
 assert(wr_iot_rc_shutdown.pending==SIGTERM&&!f.bss_open_calls);
 assert(!f.live&&!f.guard&&f.restores==1);
 assert(wr_iot_rc_shutdown_end()==SIGTERM);
 puts("PASS IoT activation: stale admission, main-radio readiness, signal-marker cancellation and retained uncertain recovery; injected backend only");return 0;
}
