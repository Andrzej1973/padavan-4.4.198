#!/usr/bin/env python3
"""Extract actual RC dispatch; injected mailbox/backend do not prove IPC."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('server',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
source=a.server.read_text(encoding='utf-8')
anchor='int wr_iot_rc_dispatch(void)'
if source.count(anchor)!=1:
    raise SystemExit('RC dispatch missing or duplicated')
function=source[source.index(anchor):].strip()
shutdown=(Path(__file__).with_name('rc-shutdown-admission.h')).read_text(encoding='utf-8')
a.output.write_text(r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
'''+shutdown+r'''
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
#define WR_IOT_CONTROL_DIRECTORY "fixture"
enum wr_iot_result_state {WR_IOT_RESULT_QUEUED=1,WR_IOT_RESULT_RUNNING,
 WR_IOT_RESULT_APPLIED,WR_IOT_RESULT_REJECTED,WR_IOT_RESULT_RECOVERY};
struct wr_iot_request {int enabled;};
struct wr_iot_control_request {char id[33];unsigned long long created;struct wr_iot_request request;};
struct wr_iot_control_result {char id[33];enum wr_iot_result_state state;unsigned long long created,observed;};
struct wr_iot_mailbox {int open;};
static struct wr_iot_control_request queued;
static struct wr_iot_control_result result;
static int opens,locked,claim=1,executions,finishes,fail_open,shutdown_delivered,emit_shutdown;
static int expected_shutdown;
static enum wr_iot_result_state outcome;
static unsigned long long now=20;
static void shutdown_test(int sig){
 assert(sig==expected_shutdown);
 if(wr_iot_rc_shutdown_note(sig))return;
 shutdown_delivered++;
}
static unsigned long long wr_iot_control_now(void){return now;}
static void wr_iot_mailbox_init(struct wr_iot_mailbox *m){m->open=0;}
static int wr_iot_mailbox_open(struct wr_iot_mailbox *m,const char *path,int create){
 assert(!m->open&&!locked&&!create&&!strcmp(path,"fixture"));
 if(++opens==fail_open)return 0;
 m->open=locked=1;return 1;
}
static void wr_iot_mailbox_close(struct wr_iot_mailbox *m){assert(m->open&&locked);m->open=locked=0;}
static int wr_iot_mailbox_claim(struct wr_iot_mailbox *m,unsigned long long time,struct wr_iot_control_request *out){
 assert(m->open&&locked&&time==now);if(!claim)return 0;
 *out=queued;return 1;
}
static int wr_iot_mailbox_result(struct wr_iot_mailbox *m,struct wr_iot_control_result *out){
 assert(m->open&&locked);*out=result;return 1;
}
static int wr_iot_mailbox_finish(struct wr_iot_mailbox *m,const char *id,enum wr_iot_result_state state,unsigned long long time){
 assert(m->open&&locked&&time==now&&!strcmp(id,queued.id));
 result.state=state;finishes++;return 1;
}
static enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *request){
 assert(!locked&&!strcmp(request->id,queued.id)&&request->created==queued.created);
 assert(request->request.enabled==queued.request.enabled);executions++;
 if(emit_shutdown){
  int sig=emit_shutdown;
  emit_shutdown=0;
  assert(raise(sig)==0);
#ifdef SIGPWR
  if(sig==SIGPWR){
   assert(shutdown_delivered==1&&!wr_iot_rc_shutdown.pending);
  }else
#endif
   assert(!shutdown_delivered&&wr_iot_rc_shutdown.pending==sig);
  assert(signal(sig,shutdown_test)!=SIG_ERR);
 }
 return outcome;
}
'''+function+r'''
static void reset(void){
 memset(&queued,0,sizeof(queued));memset(queued.id,'a',32);
 queued.created=10;queued.request.enabled=1;memset(&result,0,sizeof(result));
 memcpy(result.id,queued.id,33);result.state=WR_IOT_RESULT_RUNNING;
 opens=locked=executions=finishes=fail_open=shutdown_delivered=emit_shutdown=0;claim=1;now=20;
 outcome=WR_IOT_RESULT_APPLIED;
}
int main(void){
 int i;
 expected_shutdown=SIGTERM;
 assert(signal(SIGTERM,shutdown_test)!=SIG_ERR);
 reset();emit_shutdown=SIGTERM;
 assert(wr_iot_rc_dispatch()&&executions==1&&finishes==1&&!locked);
 assert(shutdown_delivered==1&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 assert(result.state==WR_IOT_RESULT_APPLIED);
#ifdef SIGQUIT
 expected_shutdown=SIGQUIT;
 assert(signal(SIGQUIT,shutdown_test)!=SIG_ERR);
 reset();emit_shutdown=SIGQUIT;
 assert(wr_iot_rc_dispatch()&&executions==1&&finishes==1&&!locked);
 assert(shutdown_delivered==1&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
#endif
#ifdef SIGPWR
 expected_shutdown=SIGPWR;
 assert(signal(SIGPWR,shutdown_test)!=SIG_ERR);
 reset();emit_shutdown=SIGPWR;
 assert(wr_iot_rc_dispatch()&&executions==1&&finishes==1&&!locked);
 assert(shutdown_delivered==1&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
#endif
 reset();outcome=WR_IOT_RESULT_REJECTED;assert(wr_iot_rc_dispatch());
 assert(result.state==WR_IOT_RESULT_REJECTED);
 reset();outcome=WR_IOT_RESULT_QUEUED;assert(wr_iot_rc_dispatch());
 assert(result.state==WR_IOT_RESULT_RECOVERY);
 for(i=1;i<=2;i++){
  reset();fail_open=i;assert(!wr_iot_rc_dispatch()&&!finishes&&!locked);
  assert(executions==(i==2));
 }
 reset();now=0;assert(!wr_iot_rc_dispatch()&&!opens&&!executions);
 reset();claim=0;assert(!wr_iot_rc_dispatch()&&!executions&&!finishes&&!locked);
 reset();claim=0;result.state=WR_IOT_RESULT_APPLIED;
 assert(wr_iot_rc_dispatch()&&!executions&&finishes==1&&!locked);
 assert(!shutdown_delivered&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 puts("PASS actual RC dispatch: available shutdown signal paths, transaction envelope, uncertain recovery and no replay; injected IPC");
 return 0;
}
''',encoding='utf-8')
print('Prepared actual RC dispatch fixture with injected IPC and activation')
