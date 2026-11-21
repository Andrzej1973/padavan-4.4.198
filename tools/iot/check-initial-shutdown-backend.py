from pathlib import Path
import subprocess,tempfile,ast,json,hashlib,datetime
here=Path(__file__).resolve().parent;root=here
source=(here/'check-rc-backend-composition.py').read_text();ns={'__file__':str(here/'check-rc-backend-composition.py')}
exec(compile(source[:source.index('with tempfile.TemporaryDirectory(')],'<backend fixture>','exec'),ns)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
body=ns['body'].split('int main(void)',1)[0]
body=body.replace('#include "rc-backend.c"','#include "'+str(root/'rc-backend.c')+'"')
body+=r'''
#include "initial-shutdown-owner.h"
int main(void){
 reset();idle_reads=0;rollback_dns=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 struct wr_iot_radio_stop_fence fence={0};struct wr_iot_initial_shutdown_owner owner={0};
 struct wr_iot_control_request off={.id="01010101010101010101010101010101",.created=1};
 struct wr_iot_physical_initial_request q={0};unsigned char nonce[16]={9};
 assert(wr_iot_rc_shutdown_route_arm());assert(wr_iot_rc_shutdown_note(SIGTERM));
 assert(wr_iot_radio_stop_fence_begin_routed_shutdown(&fence));assert(wr_iot_initial_shutdown_claim(&owner,&fence));
 assert(!wr_iot_activation_prepare_radio_stop());
 assert(wr_iot_rc_backend_initial_shutdown_prepare(&off,&owner)&&!depth);
 struct wr_iot_initial_off retained=physical_initial;
 int token=wr_iot_service_guard_enter(1);assert(token==1);
 assert(wr_iot_rc_backend_shutdown_initial_request(&owner,nonce,&q)&&q.action==WR_STOP_ARM);
 backend.busy=1;assert(!wr_iot_rc_backend_shutdown_initial_request(&owner,nonce,&q)&&!q.action);
 assert(!wr_iot_rc_backend_initial_shutdown_prepare(&off,&owner));backend.busy=0;
 assert(!memcmp(&retained,&physical_initial,sizeof(retained)));
 struct wr_iot_initial_shutdown_owner foreign=owner;foreign.owner++;
 assert(!wr_iot_rc_backend_initial_shutdown_prepare(&off,&foreign));
 assert(!wr_iot_rc_backend_shutdown_initial_request(&foreign,nonce,&q)&&!q.action);
 assert(wr_iot_rc_backend_shutdown_initial_request(&owner,nonce,&q));
 assert(wr_iot_rc_shutdown.pending==SIGTERM&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 wr_iot_service_guard_leave(token);
 (void)signal_handler;(void)submit;(void)terminal;return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-shutdown-initial-backend-') as d:
 subprocess.run(['python3',str(here/'prepare-request-stage-check.py'),d],check=True)
 p=Path(d)/'check.c';p.write_text(ns['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 # Use candidate initial observation but all other actual baseline units.
 sources=[str(root/n) if n=='initial-off.c' else str(here/n) for n in units]
 if 'radio-stop-fence.c' not in units:sources.append(str(here/'radio-stop-fence.c'))
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+d,'-I'+str(here),str(p),*sources,'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual routed INITIAL fixture: check-initial-shutdown-backend.py; external adapters injected, target/runtime pending')
