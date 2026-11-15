from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-cold-on-handoff.py').read_text();ns={'__file__':str(here/'check-cold-on-handoff.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "rc-cold-shutdown.h"
int wr_iot_activation_owner_closed(const struct wr_iot_activation_owner*s,const struct wr_iot_control_result*r,struct wr_iot_driver_closed_result*out){assert(s==&backend&&r->created==8);*out=(struct wr_iot_driver_closed_result){5,2,7,9};return active_proof;}
int wr_iot_rc_quiesce_shutdown_begin(struct wr_iot_rc_quiesce*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
#include "rc-cold-shutdown.inc"
#include "rc-cold-shutdown-release.inc"
static struct wr_iot_cold_owner *signal_root;static int signals;
static void postshutdown_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_cold_backend_parent);
 assert(signal_root&&!signal_root->owner&&!signal_root->admission.profile.files.count);
 signals++;
}
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct sigaction sa={0};sa.sa_handler=postshutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
 strcpy(desired.gateway,"192.168.30.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.30.10");strcpy(desired.last,"192.168.30.40");
 for(int rejected=0;rejected<=1;rejected++){
  struct wr_iot_cold_owner owner={0};struct wr_iot_cold_handoff h={0};struct wr_iot_control_request input={0};struct wr_iot_cold_stop stop={0};
  down=1;partial=idle_fault=idle_reads=up_calls=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=no_submit=service_fail=service_calls=mc_calls=mc_fail=0;up_result=WR_RESTART_UP_RETURNED;
  memset(&backend,0,sizeof(backend));wr_iot_cold_backend_parent=NULL;memset(&wr_iot_cold_backend_identity,0,sizeof(wr_iot_cold_backend_identity));
  begins=continues=0;claim=active_proof=aux=auth=1;
  memset(input.id,'0',32);input.id[1]='1';input.created=7;input.request=desired;
  assert(wr_iot_cold_owner_begin(&owner,&input,1));
  int ready=0;for(int i=0;i<40;i++)if(wr_iot_cold_owner_step(&owner)){ready=1;break;}
  assert(ready&&wr_iot_cold_handoff_begin(&h,&owner));
  stop.owner=getpid();stop.parent=&owner;stop.handoff=&h;
  if(rejected){backend.phase=WR_IOT_OWNER_REJECTED;backend.start.phase=WR_IOT_RUN_REJECTED;backend.start.rollback.phase=WR_IOT_ROLL_DONE;stop.phase=WR_COLD_STOP_REJECTED;}
  else{
   backend.phase=WR_IOT_OWNER_OFF;backend.start.phase=WR_IOT_RUN_STOPPED;backend.start.open.attempt.identity=owner.main.identity;
   backend.stop.owner=getpid();backend.stop.active=&backend.start;backend.stop.complete=1;backend.stop.created=8;memset(backend.stop.id,'2',32);
   backend.stop.stop.close.request.open_token=7;backend.stop.stop.close_serial=9;
   stop.phase=WR_COLD_STOP_CLOSED;stop.off.owner=getpid();stop.off.complete=1;stop.off.created=8;memcpy(stop.off.id,backend.stop.id,33);
   /* Actual normal-OFF profile mutation is represented by the full CLOSE actor.
    * The old cold baseline must not be replayed or used as current proof. */
   FILE*f=fopen(profile_path,"a");assert(f&&fputs("# current OFF profile\n",f)>=0&&!fclose(f));
  }
  struct wr_iot_generated_file retained;assert(wr_iot_generated_capture(&retained,profile_path));
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_guest_step(&owner.guest)&&guest_downs==1);
  signal_root=&owner;signals=0;assert(!raise(SIGTERM)&&!signals);
  fail_post_unmask=1;assert(!wr_iot_rc_cold_postshutdown_release(&stop)&&owner.admission.profile.active&&depth==1&&!signals);
  fail_post_unmask=0;assert(wr_iot_rc_cold_postshutdown_release(&stop)&&signals==1&&!stop.owner&&!h.owner&&!owner.owner);
  assert(!depth&&!owner.admission.fence.owner&&!wr_iot_rc_shutdown.pending&&up_calls==1&&guest_downs==1);
  assert(backend.phase==(rejected?WR_IOT_OWNER_REJECTED:WR_IOT_OWNER_OFF));
  assert(!wr_iot_rc_cold_postshutdown_release(&stop));
  assert(wr_iot_service_guard_enter(1)==1&&wr_iot_generated_matches(&retained,profile_path));wr_iot_service_guard_leave(1);
  assert(!unlink(profile_path));
 }
}

'''
body=body.replace('int wr_iot_bss_is_down(void){return down;}','int wr_iot_bss_is_down(void){return 1;}')
body=body.replace('#include "radio-stop-fence.c"',r'''static int fail_post_unmask;
static int post_mask(int how,const sigset_t *set,sigset_t *old){if(how==SIG_SETMASK&&fail_post_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask post_mask
#include "radio-stop-fence.c"
#undef sigprocmask
''')

with tempfile.TemporaryDirectory(prefix='wr-cold-handoff-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=20)
print('PASS cold posthandoff shutdown cleanup: CLOSED/rejected exact backend proof, failed mask retains, detach/wipe/guard release before real SIGTERM, current OFF profile unchanged, no Main replay; CLOSED observer actor')
