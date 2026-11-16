from pathlib import Path
import subprocess,tempfile,json,datetime,hashlib
here=Path(__file__).resolve().parent;root=here
prefix=(here/'check-rc-initial-stop.c').read_text().split('int main(void)',1)[0]
code=prefix+r'''
int wr_iot_rc_backend_shutdown_initial_request(const struct wr_iot_initial_shutdown_owner *owner,const unsigned char *nonce,struct wr_iot_physical_initial_request *out){
 assert(wr_iot_initial_shutdown_current(owner)&&wr_iot_rc_shutdown.pending==SIGTERM);
 return wr_iot_rc_backend_prepared_initial_request(nonce,out);
}
static void initial_signal(int sig){assert(wr_iot_rc_shutdown_note(sig));}
int main(void){
 struct sigaction action={0};action.sa_handler=initial_signal;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,0)&&!sigaction(SIGQUIT,&action,0));
 struct wr_iot_radio_stop_fence fence={0};struct wr_iot_initial_shutdown_owner owner={0};
 struct wr_iot_rc_initial_stop s={0};unsigned char nonce[16]={1};
 struct wr_iot_physical_initial_request release;
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(wr_iot_radio_stop_fence_begin_routed_shutdown(&fence));
 assert(wr_iot_initial_shutdown_claim(&owner,&fence));
 assert(!wr_iot_rc_initial_stop_begin(&s,nonce));
 assert(wr_iot_rc_initial_stop_begin_shutdown(&s,nonce,&owner));
 owner.signal=SIGQUIT;assert(!wr_iot_rc_initial_stop_step(&s)&&!aux&&!calls);owner.signal=SIGTERM;
 for(unsigned i=0;i<8;i++)assert(!wr_iot_rc_initial_stop_step(&s));
 assert(aux==6&&!downs&&!calls);
 uncertain=1;assert(!wr_iot_rc_initial_stop_step(&s)&&calls==1&&!downs);
 uncertain=0;assert(!wr_iot_rc_initial_stop_step(&s));
 assert(!wr_iot_rc_initial_stop_step(&s)&&downs==1);
 assert(!raise(SIGQUIT));
 assert(wr_iot_rc_shutdown.pending==SIGTERM);
 assert(!wr_iot_rc_initial_stop_step(&s));status=WR_STOP_COMPLETE;
 assert(!wr_iot_rc_initial_stop_step(&s));assert(wr_iot_rc_initial_stop_step(&s)==1);
 assert(wr_iot_rc_initial_stop_released(&s,&release)&&release.action==WR_STOP_RELEASE);
 assert(wr_iot_rc_shutdown.pending==SIGTERM&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(wr_iot_radio_stop_fence_end(&fence));
 assert(!wr_iot_initial_shutdown_current(&owner)&&!depth);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-shutdown-controller-') as d:
 p=Path(d)/'check.c';p.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+str(here),str(p),str(root/'rc-initial-stop.c'),str(here/'physical-initial-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
# Same candidate must preserve all ordinary controller regression cases.
with tempfile.TemporaryDirectory(prefix='wr-initial-shutdown-ordinary-controller-') as d:
 p=Path(d)/'check.c';p.write_text((here/'check-rc-initial-stop.c').read_text()+'''\nint wr_iot_rc_backend_shutdown_initial_request(const struct wr_iot_initial_shutdown_owner *o,const unsigned char *n,struct wr_iot_physical_initial_request *q){(void)o;(void)n;(void)q;assert(0);return 0;}\n''')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+str(here),str(p),str(root/'rc-initial-stop.c'),str(here/'physical-initial-session.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual routed INITIAL fixture: check-initial-shutdown-controller.py; external adapters injected, target/runtime pending')
