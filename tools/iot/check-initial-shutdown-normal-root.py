from pathlib import Path
import subprocess,tempfile,json,hashlib,datetime
here=Path(__file__).resolve().parent;root=here
script=(root/'check-initial-shutdown-composed.py').read_text();ns={'__file__':str(root/'check-initial-shutdown-composed.py')}
exec(compile(script[:script.index('\nwith tempfile.TemporaryDirectory(')],'<composed prototype setup>','exec'),ns)
# This fixture binds the actual normal controller, not the CLOSE-only actor.
actor='int wr_iot_rc_normal_shutdown_arm_ready(void){assert(0);return 0;}'
assert ns['body'].count(actor)==1
ns['body']=ns['body'].replace(actor,'',1).replace('#include "check-mailbox-normal-consumer.h"','')
body=ns['body'].split('static unsigned initial_stock,initial_private;',1)[0]+r'''
#include "rc-normal-shutdown.c"
static unsigned normal_stock;
static void normal_original(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!physical.owner&&!depth&&!wr_iot_rc_shutdown.active);
 assert(normal_shutdown.spent&&!normal_shutdown.owner&&!wr_iot_rc_shutdown.normal_route_armed);
 normal_stock++;
}
int main(void){
 reset();idle_reads=0;rollback_dns=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 struct sigaction a={0};a.sa_handler=normal_original;sigemptyset(&a.sa_mask);
 assert(!sigaction(SIGTERM,&a,0)&&!sigaction(SIGQUIT,&a,0));
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(wr_iot_rc_normal_shutdown_pending());
 assert(!wr_iot_rc_normal_shutdown_step());
 assert(normal_shutdown.claimed&&physical.initial.owner==getpid()&&!normal_stock);
 assert(!raise(SIGQUIT));
 for(unsigned i=0;i<40&&!normal_stock;i++)(void)wr_iot_rc_normal_shutdown_step();
 assert(normal_stock==1&&normal_shutdown.spent&&!normal_shutdown.owner);
 assert(!physical.owner&&!depth&&physical_downs==1&&physical_aux==6&&initial_calls==3);
 assert(!wr_iot_rc_normal_shutdown_pending());
 for(unsigned i=0;i<3;i++)assert(!wr_iot_rc_normal_shutdown_step());
 assert(normal_stock==1&&physical_downs==1&&initial_calls==3);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-normal-root-') as d:
 subprocess.run(['python3',str(here/'prepare-request-stage-check.py'),d],check=True)
 p=Path(d)/'check.c';p.write_text(ns['ns']['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 sources=[str(root/n) if n=='initial-off.c' else str(here/n) for n in ns['ns']['units']]
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+d,'-I'+str(here),str(p),*sources,str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual routed INITIAL fixture: check-initial-shutdown-normal-root.py; external adapters injected, target/runtime pending')
