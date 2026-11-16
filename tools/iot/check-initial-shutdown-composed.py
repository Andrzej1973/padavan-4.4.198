from pathlib import Path
import subprocess,tempfile,json,datetime,hashlib
here=Path(__file__).resolve().parent;root=here
source=(here/'check-rc-physical-quiesce.py').read_text();ns={'__file__':str(here/'check-rc-physical-quiesce.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<quiesce fixture>','exec'),ns)
body=ns['body'].split('int main(void)',1)[0]
for name in ('rc-backend.c','rc-physical-stop.c','rc-initial-stop.c'):
 body=body.replace('#include "'+name+'"','#include "'+str(root/name)+'"')
a='enum wr_iot_physical_call_result wr_iot_physical_initial_call(const struct wr_iot_physical_initial_request *q,struct wr_iot_physical_initial_response *out){(void)q;memset(out,0,sizeof(*out));return WR_PHYSICAL_CALL_NOT_SUBMITTED;}'
b='''static unsigned initial_calls;
enum wr_iot_physical_call_result wr_iot_physical_initial_call(const struct wr_iot_physical_initial_request *q,struct wr_iot_physical_initial_response *out){
 assert(wr_iot_rc_shutdown.pending==SIGTERM);initial_calls++;
 out->identity=*q;out->identity.attempt=19;
 out->status=q->action==WR_STOP_ARM?WR_STOP_ARMED:q->action==WR_STOP_RELEASE?WR_STOP_RELEASED:WR_STOP_COMPLETE;
 return WR_PHYSICAL_CALL_ACKNOWLEDGED;
}'''
assert body.count(a)==1;body=body.replace(a,b)
body+=r'''
static unsigned initial_stock,initial_private;
static void shutdown_original(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!physical.owner&&!depth&&initial_private==1);initial_stock++;
}
static void shutdown_private(void *data){(void)data;assert(!physical.owner&&!depth);initial_private++;}
int main(void){
 reset();idle_reads=0;rollback_dns=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 struct sigaction action={0};action.sa_handler=shutdown_original;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,0)&&!sigaction(SIGQUIT,&action,0));
 struct wr_iot_control_request off={.id="01010101010101010101010101010101",.created=17};
 struct wr_iot_physical_initial_request released;
 assert(wr_iot_rc_boot_idle());assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(wr_iot_rc_physical_begin_routed_shutdown(&off)&&physical.initial.owner==getpid());
 assert(physical_initial.ready&&wr_iot_rc_shutdown.pending==SIGTERM);
 for(unsigned i=0;i<25&&!physical.result;i++)wr_iot_rc_physical_step();
 assert(physical.result==1&&physical_downs==1&&physical_aux==6&&initial_calls==3);
 assert(!depth&&!wr_iot_rc_shutdown.active&&!initial_stock);
 assert(wr_iot_rc_physical_initial_off_read(off.id,off.created,&released));
 assert(!wr_iot_rc_physical_shutdown_release_cleanup(off.id,off.created+1,shutdown_private,0));
 assert(wr_iot_rc_physical_shutdown_release_cleanup(off.id,off.created,shutdown_private,0));
 assert(initial_stock==1&&initial_private==1&&!physical.owner&&!depth);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-routed-initial-composed-') as d:
 subprocess.run(['python3',str(here/'prepare-request-stage-check.py'),d],check=True)
 p=Path(d)/'check.c';p.write_text(ns['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 units=ns['units'];sources=[str(root/n) if n=='initial-off.c' else str(here/n) for n in units]
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+d,'-I'+str(here),str(p),*sources,str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual routed INITIAL fixture: check-initial-shutdown-composed.py; external adapters injected, target/runtime pending')
