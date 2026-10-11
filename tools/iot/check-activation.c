#include "activation.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
struct fixture {int fail,recovery_fail,locked,unlocks,live,guard,dhcp,attached,bridge,restores,exists;};
static int operation(void *context,enum wr_iot_activation_operation op){
 struct fixture *f=context;
 if(op==WR_IOT_LOCK){if(f->fail==(int)op+1)return 0;assert(!f->locked);f->locked=1;return 1;}
 assert(f->locked);
 if(f->fail==(int)op+1){f->fail=0;return 0;}
 if(f->recovery_fail==(int)op+1)return 0;
 switch(op){
 case WR_IOT_QUIESCE:f->live=0;break;
 case WR_IOT_BRIDGE_PREPARE:f->exists=1;break;
 case WR_IOT_ISOLATE:f->guard=1;break;
 case WR_IOT_DHCP_START:assert(!f->live&&f->guard&&f->attached&&f->bridge);f->dhcp=1;break;
 case WR_IOT_ATTACH:assert(!f->live&&f->guard&&!f->dhcp);f->attached=1;break;
 case WR_IOT_BRIDGE_UP:assert(!f->live&&f->attached&&f->guard&&!f->dhcp);f->bridge=1;break;
 case WR_IOT_BSS_UP:assert(f->attached&&f->bridge&&f->guard&&f->dhcp);f->live=1;break;
 case WR_IOT_OBSERVE:assert(f->live&&f->guard&&f->dhcp);break;
 case WR_IOT_BRIDGE_DOWN:assert(!f->live);f->bridge=0;break;
 case WR_IOT_DETACH:assert(!f->live&&!f->bridge);f->attached=0;break;
 case WR_IOT_RESTORE:assert(!f->live&&!f->attached&&!f->bridge&&!f->exists);f->dhcp=0;f->restores++;break;
 case WR_IOT_BRIDGE_REMOVE:assert(!f->live&&!f->attached&&!f->bridge);f->exists=0;break;
 case WR_IOT_GUARD_REMOVE:assert(!f->live&&!f->attached&&!f->bridge&&!f->dhcp);f->guard=0;break;
 default:break;
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
 for(fail=WR_IOT_LOCK+1;fail<=WR_IOT_OBSERVE+1;fail++){
  memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));f.fail=fail;
  assert(!wr_iot_activation_start(&state,&backend,&f));
  assert(state.state==WR_IOT_INACTIVE&&!f.locked&&!state.snapshot&&!f.live&&!f.guard);
 }
 for(fail=WR_IOT_BRIDGE_DOWN+1;fail<=WR_IOT_GUARD_REMOVE+1;fail++){
  memset(&state,0,sizeof(state));memset(&f,0,sizeof(f));
  assert(wr_iot_activation_start(&state,&backend,&f));f.recovery_fail=fail;
  assert(!wr_iot_activation_stop(&state));assert(state.state==WR_IOT_RECOVERY&&f.locked&&state.snapshot);
  f.recovery_fail=0;assert(wr_iot_activation_stop(&state));assert(state.state==WR_IOT_INACTIVE&&!f.locked&&!f.guard&&f.restores==1);
 }
 puts("PASS IoT activation sequencing and retained recovery: injected backend; production bindings and runtime unverified");return 0;
}
