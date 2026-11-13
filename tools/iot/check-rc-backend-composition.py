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
#include "rc-backend.c"
#include "activation-observe.h"
#define WR_IOT_NOTIFY() ((void)0)
#include "control-client.c"


static volatile sig_atomic_t shutdowns;
int wr_iot_activation_result_observed(const struct wr_iot_control_result *r){return wr_iot_rc_backend_observed(r);}
static void signal_handler(int sig){assert(sig==SIGTERM);if(!wr_iot_rc_shutdown_note(sig))shutdowns++;}
static int mode_ok=1,mode_reads;
int wr_iot_rc_mode_read(struct wr_iot_rc_mode *m){assert(depth);mode_reads++;*m=(struct wr_iot_rc_mode){1,1,0};return mode_ok;}
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
 assert(wr_iot_activation_execute(&on)==WR_IOT_RESULT_RECOVERY&&!depth&&!mode_reads);
 wr_iot_rc_shutdown.active=1;mode_ok=0;
 assert(wr_iot_activation_execute(&on)==WR_IOT_RESULT_REJECTED&&!depth&&backend.phase==WR_IOT_OWNER_IDLE);
 wr_iot_rc_shutdown.active=0;mode_ok=1;

 submit(&on);assert(wr_iot_rc_dispatch()&&wr_iot_rc_shutdown.active);
 assert(!wr_iot_rc_dispatch());
 mode_ok=0;int previous_mode_reads=mode_reads;
 assert(wr_iot_activation_execute(&on)==WR_IOT_RESULT_RECOVERY&&mode_reads==previous_mode_reads);
 mode_ok=1;

 for(unsigned i=0;i<60&&wr_iot_rc_shutdown.active;i++)assert(wr_iot_rc_continue());
 assert(!wr_iot_rc_shutdown.active&&backend.phase==WR_IOT_OWNER_ACTIVE&&!depth);
 terminal(on.id);assert(!wr_iot_rc_continue());
 submit(&off);assert(wr_iot_rc_dispatch()&&wr_iot_rc_shutdown.active);
 for(unsigned i=0;i<60&&backend.stop.stop.phase!=WR_IOT_STOP_ISOLATE;i++)assert(wr_iot_rc_continue());
 assert(backend.stop.stop.phase==WR_IOT_STOP_ISOLATE&&depth==3);
 quarantine_ready=0;
 for(unsigned i=0;i<3;i++)assert(wr_iot_rc_continue());
 assert(closes==1&&depth==3);
 assert(!raise(SIGTERM)&&!shutdowns&&wr_iot_rc_shutdown.pending==SIGTERM);
 assert(signal(SIGTERM,signal_handler)!=SIG_ERR);quarantine_ready=1;
 for(unsigned i=0;i<60&&wr_iot_rc_shutdown.active;i++)assert(wr_iot_rc_continue());
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&shutdowns==1);
 assert(backend.phase==WR_IOT_OWNER_OFF&&!depth&&closes==1&&progresses==1&&releases==1);
 terminal(off.id);assert(!wr_iot_rc_continue());
 char path[PATH_MAX];
 for(unsigned i=0;i<2;i++){
  assert(snprintf(path,sizeof(path),"%s/%s",mailbox_directory,i?"lock":"result")<(int)sizeof(path));
  assert(!unlink(path));
 }
 assert(!rmdir(mailbox_directory));
 puts("PASS actual RC backend/mailbox/server/client/owner/runner/OFF: ON and OFF published APPLIED, duplicate dispatch refused, delayed isolation retains guard, pending SIGTERM delivered only after terminal publication; external resource/driver hooks injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-rc-backend-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('activation-observe.c','control-mailbox.c','initial-off.c','activation-owner.c','active-stop.c','start-runner.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','precreated-stop.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
