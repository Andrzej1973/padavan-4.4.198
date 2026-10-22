#include "activation.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
struct fixture {int fail,partial_fail,recovery_fail,locked,unlocks,live,guard,dhcp,policy,attached,bridge,profile,restores,exists,radio_prepared;
 int main_config,stop_config,stop_snapshot,disable_applies,main_ready,main_radio_missing;};
static int operation(void *context,enum wr_iot_activation_operation op){
 struct fixture *f=context;
 if(op==WR_IOT_LOCK){if(f->fail==(int)op+1)return 0;assert(!f->locked);f->locked=1;return 1;}
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
 case WR_IOT_MAIN_RADIO_READY:assert(!f->live&&f->radio_prepared&&f->attached&&f->guard&&f->dhcp&&f->policy);if(f->main_radio_missing)return 0;f->main_ready=1;break;
 case WR_IOT_BSS_UP:assert(!f->live&&f->main_ready&&f->radio_prepared&&f->attached&&f->bridge&&f->guard&&f->dhcp&&f->policy);f->live=1;break;
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
 return 1;
}
static void unlock(void *context){struct fixture *f=context;assert(f->locked);f->locked=0;f->unlocks++;}
int main(void){
 const struct wr_iot_activation_backend backend={operation,unlock};
 struct wr_iot_activation state;struct fixture f;int fail;
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
 puts("PASS IoT activation: main-radio readiness gates BSS_UP; missing main radio rolls back; injected backend, production/runtime unverified");return 0;
}
