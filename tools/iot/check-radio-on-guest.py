"""OFF-to-ON Guest continuation with actual parent controllers and profile IO."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-main.py').read_text()
ns={'__file__':str(here/'check-radio-on-main.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-guest.h"
#include "restart-guest-bridge.h"
#include "restart-guest-isolation.h"
static int guest_desired=1,guest_isolate=1,guest_state,guest_bridge,guest_isolated,guest_adds,guest_ups,guest_downs,bridge_fail,no_submit;
int wr_iot_rc_restart_guest_policy(int*out){*out=guest_desired;return 1;}
int wr_iot_rc_restart_guest_isolation_policy(int*out){*out=guest_isolate;return 1;}
int wr_iot_restart_guest_admin_state(int*out){*out=guest_state;return 1;}
enum wr_iot_main_bridge_result wr_iot_restart_guest_bridge_attach(void){assert(!guest_state);guest_adds++;if(!bridge_fail)guest_bridge=1;return WR_MAIN_BRIDGE_UNCERTAIN;}
int wr_iot_restart_guest_bridge_current(void){return guest_bridge;}
int wr_iot_restart_guest_isolation_prepare(int desired_isolate){assert(guest_bridge&&!guest_state&&desired_isolate==1);guest_isolated=1;return 1;}
int wr_iot_restart_guest_isolation_current(int desired_isolate){return guest_isolated&&desired_isolate==1;}
enum wr_iot_restart_up_result wr_iot_restart_guest_up(void){assert(guest_bridge&&guest_isolated);guest_ups++;if(no_submit)return WR_RESTART_UP_NOT_SUBMITTED;guest_state=1;return WR_RESTART_UP_RETURNED;}
enum wr_iot_restart_up_result wr_iot_restart_guest_down(void){guest_downs++;guest_state=0;return WR_RESTART_UP_RETURNED;}
#include "radio-on-guest.c"
#include "radio-on-services.h"
static int service_calls;
int wr_iot_rc_restart_service_policy(struct wr_iot_restart_service_policy*p){p->enterprise=1;p->kick_rssi=-75;p->assoc_rssi=-80;return 1;}
enum wr_iot_restart_service_result wr_iot_rc_restart_service_submit(const struct wr_iot_restart_service_policy*p,unsigned slot){assert(p->enterprise&&slot==(unsigned)service_calls);service_calls++;return WR_SERVICE_RETURNED;}
#include "radio-on-services.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<6;fault++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_generation g={0};struct wr_iot_on_main m={0};struct wr_iot_on_guest guest={0};unsigned char id[16]={1};
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=fault!=3;guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;bridge_fail=fault==4;no_submit=fault==5;
  assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_generation_begin(&g,&a,&desired,1));
  assert(!wr_iot_on_generation_step(&g)&&wr_iot_on_generation_step(&g)==1);
  up_result=WR_RESTART_UP_RETURNED;assert(wr_iot_on_main_begin(&m,&g,id));
  assert(wr_iot_on_guest_begin(&guest,&m)&&!wr_iot_on_guest_begin(&guest,&m));
  if(fault==3){assert(wr_iot_on_guest_step(&guest)&&!guest_ups&&!guest_adds);}
  else{
   assert(!wr_iot_on_guest_step(&guest)&&guest_adds==1);
   if(fault==4){assert(!wr_iot_on_guest_step(&guest)&&guest_adds==1&&!guest_ups);}
   else{
    assert(!wr_iot_on_guest_step(&guest)&&guest_isolated);
    assert(!wr_iot_on_guest_step(&guest)&&guest_ups==1);
    if(fault==5)assert(!wr_iot_on_guest_step(&guest)&&!guest_downs);
    else{
     assert(wr_iot_on_guest_step(&guest));
     if(fault==1)guest_desired=0;
     if(fault==2)guest_isolated=0;
     if(fault){assert(!wr_iot_on_guest_step(&guest)&&guest_downs==1&&!guest_state);assert(!wr_iot_on_guest_step(&guest)&&guest_downs==1);}
     else {
      assert(wr_iot_on_guest_step(&guest)&&!guest_downs);
      struct wr_iot_on_services services={0};service_calls=0;
      assert(wr_iot_on_services_begin(&services,&guest));
      wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_on_services_step(&services)&&!service_calls);wr_iot_rc_shutdown.pending=0;
      for(int i=0;i<3;i++)assert(!wr_iot_on_services_step(&services)&&service_calls==i+1);
      assert(wr_iot_on_services_step(&services)&&service_calls==3);
      guest_desired=0;assert(!wr_iot_on_services_step(&services)&&service_calls==3&&guest_downs==1);
     }
    }
   }
  }
  assert(ups==1&&a.busy&&a.profile.active&&generator_calls==1);
  /* Fixture cleanup only: parent/Guest retirement is not installed in RC. */
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_on_admission_cancel(&a)&&!depth);assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-guest-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON Guest actual parent/profile lifecycle: bridge then isolation then one UP, policy OFF no UP, failed bridge no replay, policy/isolation loss after UP one DOWN, no-submission retains; SDK boundary actors, no device acceptance')
