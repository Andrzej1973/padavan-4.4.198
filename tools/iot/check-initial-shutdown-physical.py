from pathlib import Path
import subprocess,tempfile,json,hashlib,datetime
here=Path(__file__).resolve().parent;root=here
ns={'__file__':str(here/'check-rc-physical-initial.py')};script=(here/'check-rc-physical-initial.py').read_text();exec(compile(script[:script.index('\nwith tempfile.TemporaryDirectory(')],'<initial owner fixture>','exec'),ns)
prefix=ns['code'].split('int main(void)',1)[0]
prefix=prefix.replace('#include "'+str(here/'rc-physical-stop.c')+'"','#include "'+str(root/'rc-physical-stop.c')+'"')
prefix=prefix.replace('#include "rc-initial-stop.c"','#include "'+str(root/'rc-initial-stop.c')+'"')
marker='#include "'+str(root/'rc-physical-stop.c')+'"'
prefix=prefix.replace(marker,'''static int fail_final_mask,duplicate_restore;
static int initial_final_mask(int op,const sigset_t *set,sigset_t *old){
 if(op==SIG_SETMASK&&fail_final_mask)return -1;
 if(op==SIG_SETMASK&&duplicate_restore){duplicate_restore=0;assert(!raise(SIGQUIT));}
 return sigprocmask(op,set,old);
}
#define sigprocmask initial_final_mask
'''+marker+'\n#undef sigprocmask',1)
code=prefix+r'''
int wr_iot_rc_boot_idle(void){return 1;}
int wr_iot_rc_backend_initial_shutdown_prepare(const struct wr_iot_control_request *off,const struct wr_iot_initial_shutdown_owner *owner){
 assert(!off->request.enabled&&wr_iot_initial_shutdown_current(owner)&&depth==1);prepared_initial++;return 1;
}
int wr_iot_rc_backend_shutdown_initial_request(const struct wr_iot_initial_shutdown_owner *owner,const unsigned char *nonce,struct wr_iot_physical_initial_request *out){
 assert(wr_iot_initial_shutdown_current(owner));return wr_iot_rc_backend_prepared_initial_request(nonce,out);
}
static unsigned replayed,cleaned;
static void original_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!physical.owner&&!depth&&!wr_iot_rc_shutdown.active&&cleaned==1);
 replayed++;
}
static void private_cleanup(void *unused){(void)unused;assert(!physical.owner&&!depth);cleaned++;}
int main(void){
 (void)handler;struct sigaction action={0};action.sa_handler=original_signal;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,0)&&!sigaction(SIGQUIT,&action,0));
 struct wr_iot_control_request off={.id="01010101010101010101010101010101",.created=17};
 struct wr_iot_physical_initial_request released;
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(wr_iot_rc_physical_begin_routed_shutdown(&off)&&physical.initial.owner==getpid());
 for(unsigned i=0;i<25&&!physical.result;i++)wr_iot_rc_physical_step();
 assert(physical.result==1&&!depth&&downs==1&&initial_calls==3&&!replayed);
 assert(wr_iot_rc_physical_initial_off_read(off.id,off.created,&released));
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!wr_iot_rc_physical_shutdown_release_cleanup(off.id,off.created+1,private_cleanup,0));
 assert(physical.owner==getpid()&&!replayed&&!cleaned);
 fail_final_mask=1;
 assert(!wr_iot_rc_physical_shutdown_release_cleanup(off.id,off.created,private_cleanup,0));
 assert(physical.owner==getpid()&&!replayed&&!cleaned);
 fail_final_mask=0;duplicate_restore=1;
 assert(wr_iot_rc_physical_shutdown_release_cleanup(off.id,off.created,private_cleanup,0));
 assert(replayed==1&&cleaned==1&&!physical.owner&&!wr_iot_rc_shutdown.normal_route_armed);
 assert(!wr_iot_rc_physical_shutdown_release_cleanup(off.id,off.created,private_cleanup,0));
 assert(replayed==1&&downs==1&&initial_calls==3);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-routed-initial-physical-') as d:
 p=Path(d)/'check.c';p.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual routed INITIAL fixture: check-initial-shutdown-physical.py; external adapters injected, target/runtime pending')
