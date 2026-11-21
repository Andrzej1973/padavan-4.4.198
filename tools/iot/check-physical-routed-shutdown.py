"""Routed shutdown uses actual physical controller/session/fence, injected IO."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
code=code.replace('#include "rc-physical-stop.c"',r'''static int fail_final_restore,duplicate_at_restore;
static int routed_mask(int op,const sigset_t *set,sigset_t *old){
 if(op==SIG_SETMASK&&fail_final_restore)return -1;
 if(op==SIG_SETMASK&&duplicate_at_restore){
  duplicate_at_restore=0;assert(!raise(SIGQUIT));
 }
 return sigprocmask(op,set,old);
}
#define sigprocmask routed_mask
#include "rc-physical-stop.c"
#undef sigprocmask
''')
code+=r'''
static void stock_replay(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!physical.owner&&!depth&&!wr_iot_rc_shutdown.active);
 assert(!wr_iot_rc_shutdown.normal_route_armed&&!wr_iot_rc_shutdown.normal_route_requested);
 shutdowns++;
}
int main(void){
 struct sigaction action={0};action.sa_handler=handler;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,NULL));
 action.sa_handler=stock_replay;assert(!sigaction(SIGQUIT,&action,NULL));
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=17};
 struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_physical_stop_request released={0};
 struct wr_iot_rc_physical_intent ordinary={0};
 assert(!wr_iot_rc_physical_begin_routed_shutdown(&off)&&!physical.owner&&!depth);
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(!shutdowns&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!wr_iot_rc_physical_begin(&ordinary));
 assert(wr_iot_rc_physical_begin_routed_shutdown(&off));
 assert(physical.routed_shutdown&&physical.quiesce.active&&!physical.quiesce.resume_needed);
 for(unsigned i=0;i<sizeof(physical.quiesce.desired);i++)assert(!((unsigned char*)&physical.quiesce.desired)[i]);
 assert(!wr_iot_rc_physical_begin_routed_shutdown(&off));
 assert(!wr_iot_rc_physical_off_read(off.id,off.created,&released));
 /* Software CLOSE alone cannot acknowledge physical completion. */
 for(int i=0;i<3;i++)wr_iot_rc_physical_step();
 assert(physical.quiesced&&!aux_calls&&!calls&&!downs);
 assert(!wr_iot_rc_physical_prearm_cancel());
 assert(wr_iot_rc_backend_closed(&closed));
 assert(!wr_iot_rc_physical_off_read(off.id,off.created,&released));
 for(int i=0;i<12&&!downs;i++)wr_iot_rc_physical_step();
 assert(downs==1&&physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE);
 assert(wr_iot_rc_shutdown.pending==SIGTERM&&!shutdowns&&depth==1);
 query_status=WR_STOP_COMPLETE;
 for(int i=0;i<8&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(!wr_iot_rc_physical_pending()&&!depth&&!wr_iot_rc_shutdown.active&&!shutdowns);
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(wr_iot_rc_physical_off_read(off.id,off.created,&released));
 assert(released.action==WR_STOP_RELEASE&&released.attempt==19&&downs==1&&aux_calls==6);
 assert(!wr_iot_rc_physical_take_off(off.id,off.created));
 assert(!wr_iot_rc_physical_take(&ordinary));
 assert(!wr_iot_rc_physical_shutdown_release(off.id,off.created+1));
 assert(physical.owner==getpid()&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 /* Dedicated stock actor verifies private retirement before original replay. */
 action.sa_handler=stock_replay;assert(!sigaction(SIGTERM,&action,NULL));
 /* An inherited blocked normal mask cannot claim synchronous completion. */
 sigset_t blocked,previous;sigemptyset(&blocked);sigaddset(&blocked,SIGQUIT);
 assert(!sigprocmask(SIG_BLOCK,&blocked,&previous));
 assert(!wr_iot_rc_physical_shutdown_release(off.id,off.created));
 assert(physical.owner==getpid()&&!physical.shutdown_release_mask_set&&!shutdowns);
 assert(!sigprocmask(SIG_SETMASK,&previous,NULL));
 fail_final_restore=1;
 assert(!wr_iot_rc_physical_shutdown_release(off.id,off.created));
 assert(physical.owner==getpid()&&physical.shutdown_release_mask_set&&!shutdowns);
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 fail_final_restore=0;duplicate_at_restore=1;
 assert(wr_iot_rc_physical_shutdown_release(off.id,off.created));
 assert(shutdowns==1&&!physical.owner&&!wr_iot_rc_shutdown.normal_route_armed);
 assert(!wr_iot_rc_shutdown.normal_route_requested);
 assert(!wr_iot_rc_physical_shutdown_release(off.id,off.created)&&shutdowns==1);
 return 0;
}
'''
for variant in ('term','quit'):
 test=code if variant=='term' else code.replace('SIGTERM','WR_TEST_SWAP').replace('SIGQUIT','SIGTERM').replace('WR_TEST_SWAP','SIGQUIT')
 with tempfile.TemporaryDirectory(prefix='wr-routed-physical-'+variant+'-') as d:
  p=Path(d)/'check.c';p.write_text(test);b=Path(d)/'check'
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True,timeout=15)
print('PASS routed physical shutdown: shutdown quiesce suppresses resume, pending intent reaches AUX/ARM/Main/RELEASE, CLOSE alone refuses completion, exact RELEASE required, generic take refused, blocked original mask refused, duplicate at restore retained, failed unmask retained for exact retry, private retirement before stock replay; IO actors, no device proof')
