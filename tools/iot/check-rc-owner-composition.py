#!/usr/bin/env python3
"""Actual mailbox/server/retained owner/runner/OFF; resource and driver hooks injected."""
from pathlib import Path
import ast,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-activation-owner-composition.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
prefix=(here/'check-start-closed-rollback-composition.c').read_text().split('int main(void){',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('int wr_iot_open_controller_recovery_read(', 'int wr_iot_close_controller_begin(', 'int wr_iot_close_controller_advance(')))+'\n'
prefix+=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
observer_source=(here/'check-activation-observe-composition.py').read_text()
observer_hooks=next(ast.literal_eval(n.value) for n in ast.parse(observer_source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='hooks' for t in n.targets))
body=body.replace('s->phase=WR_IOT_COMMIT_ACTIVE;return 1;','s->owner=getpid();s->open_token=3;s->phase=WR_IOT_COMMIT_ACTIVE;return 1;')
body=body.split('int main(void){',1)[0]+observer_hooks+r'''
static char mailbox_directory[]="/tmp/iot-rc-owner-mailbox-XXXXXX";
#define WR_IOT_CONTROL_DIRECTORY mailbox_directory
#include "control-server.c"
#include "activation-observe.h"
#define WR_IOT_NOTIFY() ((void)0)
#include "control-client.c"
static struct wr_iot_activation_owner backend;
static unsigned executions,continuations;
static volatile sig_atomic_t shutdowns;
int wr_iot_activation_result_observed(const struct wr_iot_control_result *r){return wr_iot_activation_owner_observed(&backend,r);}
static void signal_handler(int sig){assert(sig==SIGTERM);if(!wr_iot_rc_shutdown_note(sig))shutdowns++;}
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *r){
 executions++;return wr_iot_activation_owner_execute(&backend,r,1,1,0);
}
enum wr_iot_result_state wr_iot_activation_continue(const char *id,unsigned long long created){
 continuations++;return wr_iot_activation_owner_continue(&backend,id,created);
}
static void submit(struct wr_iot_control_request *request){
 struct wr_iot_mailbox m;wr_iot_mailbox_init(&m);
 request->created=wr_iot_control_now();assert(request->created);
 assert(wr_iot_mailbox_open(&m,mailbox_directory,1));
 assert(wr_iot_mailbox_submit(&m,request));wr_iot_mailbox_close(&m);
}
static void terminal(const char *id){
 struct wr_iot_mailbox m;struct wr_iot_control_result result;
 wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,mailbox_directory,0));
 assert(wr_iot_mailbox_result(&m,&result)&&!strcmp(id,result.id)&&result.state==WR_IOT_RESULT_APPLIED);
 assert(faccessat(m.directory,"request",F_OK,0)&&errno==ENOENT);
 wr_iot_mailbox_close(&m);
 assert(wr_iot_rc_status(id,&result)&&result.state==WR_IOT_RESULT_APPLIED);
}
int main(void){
 struct wr_iot_control_request on={.id="01010101010101010101010101010101",.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 struct wr_iot_control_request off={.id="02020202020202020202020202020202"};
 assert(candidate_read(NULL,"wr_iot_enable"));
 reset();idle_reads=0;rollback_dns=0;abort_calls=0;closes=progresses=releases=0;
 close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(mkdtemp(mailbox_directory));assert(signal(SIGTERM,signal_handler)!=SIG_ERR);
 submit(&on);assert(wr_iot_rc_dispatch()&&executions==1&&wr_iot_rc_shutdown.active);
 assert(!wr_iot_rc_dispatch()&&executions==1);
 for(unsigned i=0;i<60&&wr_iot_rc_shutdown.active;i++)assert(wr_iot_rc_continue());
 assert(!wr_iot_rc_shutdown.active&&backend.phase==WR_IOT_OWNER_ACTIVE&&!depth);
 terminal(on.id);assert(!wr_iot_rc_continue());
 submit(&off);assert(wr_iot_rc_dispatch()&&executions==2&&wr_iot_rc_shutdown.active);
 for(unsigned i=0;i<60&&backend.stop.stop.phase!=WR_IOT_STOP_ISOLATE;i++)assert(wr_iot_rc_continue());
 assert(backend.stop.stop.phase==WR_IOT_STOP_ISOLATE&&depth==3);
 quarantine_ready=0;unsigned before=continuations;
 for(unsigned i=0;i<3;i++)assert(wr_iot_rc_continue());
 assert(continuations==before+3&&closes==1&&depth==3);
 assert(!raise(SIGTERM)&&!shutdowns&&wr_iot_rc_shutdown.pending==SIGTERM);
 assert(signal(SIGTERM,signal_handler)!=SIG_ERR);quarantine_ready=1;
 for(unsigned i=0;i<60&&wr_iot_rc_shutdown.active;i++)assert(wr_iot_rc_continue());
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&shutdowns==1);
 assert(backend.phase==WR_IOT_OWNER_OFF&&!depth&&closes==1&&progresses==1&&releases==1&&executions==2);
 terminal(off.id);assert(!wr_iot_rc_continue());
 char path[PATH_MAX];
 for(unsigned i=0;i<2;i++){
  assert(snprintf(path,sizeof(path),"%s/%s",mailbox_directory,i?"lock":"result")<(int)sizeof(path));
  assert(!unlink(path));
 }
 assert(!rmdir(mailbox_directory));
 puts("PASS actual RC mailbox/server/retained owner/runner/OFF: ON and OFF published APPLIED, one execute each, delayed isolation retains guard, pending SIGTERM delivered only after terminal publication; external resource/driver hooks injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-rc-owner-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('activation-observe.c','control-mailbox.c','activation-owner.c','active-stop.c','start-runner.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','precreated-stop.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
