"""Actual cold parent/profile/Guest/service orchestration; SDK boundaries injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-cold-on-guest.py').read_text()
ns={'__file__':str(here/'check-cold-on-guest.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
body=body.replace('static unsigned char nonce[16]={1};','')
body=body.replace('static int service_calls;', 'static int service_calls,service_fail;').replace('service_calls++;return WR_SERVICE_RETURNED;', 'service_calls++;return service_fail?WR_SERVICE_UNCERTAIN:WR_SERVICE_RETURNED;')
body+=r'''
#include "cold-on-multicast.h"
static int mc_calls,mc_fail;
int wr_iot_rc_restart_multicast_policy(struct wr_iot_multicast_policy*p){*p=(struct wr_iot_multicast_policy){1,1,guest_desired};return 1;}
int wr_iot_restart_multicast_apply(unsigned b,int e){assert(b<2&&e==1);mc_calls++;return !mc_fail;}
int wr_iot_restart_multicast_current(unsigned b,int e){assert(b<2&&e==1);return !mc_fail;}
#include "cold-on-multicast.c"
#include "precreated-down-recovery.c"
#include "cold-on-recovery.c"
#include "cold-on-owner.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.30.1");strcpy(desired.mask,"255.255.255.0");
 strcpy(desired.first,"192.168.30.10");strcpy(desired.last,"192.168.30.40");
 for(int fault=0;fault<=8;fault++){
  struct wr_iot_cold_owner owner={0};struct wr_iot_control_request input={0};
  down=fault!=8;partial=fault==1;idle_fault=idle_reads=up_calls=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=fault!=4;guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=fault==2;no_submit=fault==3;service_fail=fault==5;service_calls=mc_calls=0;mc_fail=fault==6;
  up_result=fault==7?WR_RESTART_UP_NOT_SUBMITTED:WR_RESTART_UP_RETURNED;
  memset(input.id,'0',32);input.id[1]='1';input.created=7;input.request=desired;
  struct wr_iot_control_request bad=input;memset(bad.request.password,'x',sizeof(bad.request.password));
  assert(!wr_iot_cold_owner_begin(&owner,&bad,1)&&!owner.owner&&!depth);
  assert(wr_iot_cold_owner_begin(&owner,&input,1)&&!wr_iot_cold_owner_begin(&owner,&input,1));
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_owner_step(&owner)&&!generator_calls&&!up_calls);
  wr_iot_rc_shutdown.pending=0;
  int ready=0;
  for(int i=0;i<40;i++)if(wr_iot_cold_owner_step(&owner)){ready=1;break;}
  assert(ready==(fault==0||fault==4));
  assert(up_calls<2&&guest_ups<2&&guest_adds<2&&attaches<2&&generator_calls<2);
  if(ready){
   assert(owner.phase==WR_COLD_OWNER_PREPARED&&owner.generation.admission==&owner.admission&&owner.main.generation==&owner.generation);
   assert(owner.guest.main==&owner.main&&service_calls==3&&mc_calls==(guest_desired?2:1));
   for(size_t i=0;i<sizeof(owner.input.request);i++)assert(!((unsigned char*)&owner.input.request)[i]);
   for(int i=0;i<3;i++)assert(wr_iot_cold_owner_step(&owner)&&up_calls==1&&service_calls==3);
   assert(!wr_iot_cold_owner_recover(&owner));
  }else if(fault==1){
   assert(owner.phase==WR_COLD_OWNER_RESTORED&&!up_calls);
   wr_iot_rc_shutdown.pending=SIGTERM;assert(wr_iot_cold_owner_recover(&owner)==-1);wr_iot_rc_shutdown.pending=0;
  }
  if(fault==5)assert(service_calls==1);
  if(fault==6)assert(mc_calls==1);
  if(fault==7)assert(owner.phase==WR_COLD_OWNER_RETAINED&&up_calls==1);
  /* Fixture-only cleanup; public root retirement is deliberately unbound. */
  wr_iot_bundle_release(&owner.admission.profile.files);memset(&owner.admission.profile,0,sizeof(owner.admission.profile));owner.admission.busy=0;
  assert(wr_iot_cold_admission_cancel(&owner.admission)&&!depth&&!wr_iot_rc_shutdown.active);
  assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-owner-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=20)
print('PASS stable cold owner: actual admission/generation/Main/Guest/services/multicast, ordered one-shot phases, Guest OFF, pending/pre-UP restore and failure retention; SDK actors, no OPEN/backend/public binding')
