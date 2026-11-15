"""Actual cold parent/profile and RC backend predicate before pending shutdown."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-cold-on-owner.py').read_text();ns={'__file__':str(here/'check-cold-on-owner.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "activation-owner.h"
static struct wr_iot_activation_owner backend;
static struct {pid_t owner;} rebind;
static const struct wr_iot_cold_owner *wr_iot_cold_backend_parent;
#include "rc-cold-prehandoff.inc"
#include "cold-on-prehandoff.c"
#include "cold-on-shutdown.c"
static struct wr_iot_cold_owner *signal_root;static int signals;
static void cold_shutdown_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned);
 assert(signal_root&&!signal_root->owner&&!signal_root->admission.profile.files.count);
 for(size_t j=0;j<sizeof(signal_root->generation);j++)assert(!((unsigned char*)&signal_root->generation)[j]);
 signals++;
}
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct sigaction sa={0};sa.sa_handler=cold_shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
 strcpy(desired.gateway,"192.168.30.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.30.10");strcpy(desired.last,"192.168.30.40");
 for(int enabled=0;enabled<=1;enabled++){
  struct wr_iot_cold_owner owner={0};struct wr_iot_control_request input={0};
  down=1;partial=idle_fault=idle_reads=up_calls=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=no_submit=service_fail=service_calls=mc_calls=mc_fail=0;up_result=WR_RESTART_UP_RETURNED;
  memset(input.id,'0',32);input.id[1]='1';input.created=7;if(enabled)input.request=desired;
  assert(wr_iot_cold_owner_begin(&owner,&input,1));
  int ready=0;for(int i=0;i<40;i++)if(wr_iot_cold_owner_step(&owner)){ready=1;break;}
  assert(ready&&up_calls==1&&guest_ups==1);
  assert(!wr_iot_cold_prehandoff_shutdown_current(&owner));
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_cold_prehandoff_shutdown_current(&owner));
  assert(!wr_iot_cold_guest_step(&owner.guest)&&guest_downs==1&&!guest_state);
  assert(wr_iot_cold_prehandoff_shutdown_current(&owner));
  wr_iot_cold_backend_parent=&owner;assert(!wr_iot_cold_prehandoff_shutdown_current(&owner));wr_iot_cold_backend_parent=NULL;
  backend.owner=getpid();backend.phase=WR_IOT_OWNER_ACTIVE;assert(!wr_iot_cold_prehandoff_shutdown_current(&owner));memset(&backend,0,sizeof(backend));
  rebind.owner=getpid();assert(!wr_iot_cold_prehandoff_shutdown_current(&owner));rebind.owner=0;
  owner.main.identity.adapter_epoch++;assert(!wr_iot_cold_prehandoff_shutdown_current(&owner));owner.main.identity.adapter_epoch--;
  idle_fault=4;assert(!wr_iot_cold_prehandoff_shutdown_current(&owner));idle_fault=0;
  assert(wr_iot_cold_prehandoff_shutdown_current(&owner)&&owner.admission.profile.active&&depth==1);
  assert(!wr_iot_cold_owner_recover(&owner)&&up_calls==1&&guest_downs==1);

  struct wr_iot_generated_file retained_profile=owner.admission.profile.files.generated[0];
  signal_root=&owner;signals=0;
  assert(!raise(SIGTERM)&&!signals);
  fail_shutdown_unmask=1;
  assert(!wr_iot_cold_prehandoff_shutdown(&owner)&&owner.admission.profile.active&&depth==1&&!signals);
  fail_shutdown_unmask=0;
  assert(wr_iot_cold_prehandoff_shutdown(&owner)&&signals==1&&!owner.owner&&!depth);
  assert(!owner.admission.fence.owner&&!wr_iot_rc_shutdown.pending&&!owner.admission.profile.active);
  assert(!wr_iot_cold_prehandoff_shutdown(&owner)&&up_calls==1&&guest_downs==1);
  assert(wr_iot_service_guard_enter(1)==1);
  assert(wr_iot_generated_matches(&retained_profile,profile_path));wr_iot_service_guard_leave(1);
  assert(!unlink(profile_path));

 }
}
'''
body=body.replace('#include "radio-stop-fence.c"',r'''static int fail_shutdown_unmask;
static int shutdown_mask(int how,const sigset_t *set,sigset_t *old){if(how==SIG_SETMASK&&fail_shutdown_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask shutdown_mask
#include "radio-stop-fence.c"
#undef sigprocmask
''')

with tempfile.TemporaryDirectory(prefix='wr-cold-prehandoff-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=20)
print('PASS cold prehandoff real shutdown cleanup both intents: pending+owned Guest DOWN, exact new READY/never-opened ra2 double IDLE, inactive backend only, profile/epoch/serial drift refused, no Main replay/rollback; real pending signal after wipe, failed unmask retention; SDK actors')
