"""Actual private OFF-to-ON parent progression; SDK/kernel boundaries injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-guest.py').read_text()
ns={'__file__':str(here/'check-radio-on-guest.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-restore.h"
static int rollback_calls;
static int ram_calls,ram_fail,mc_calls,mc_fail,mc_read=1,aux_ok=1;
int wr_iot_on_aux_down_current(void){return aux_ok;}
int wr_iot_rc_radio_on_rollback_state(const struct wr_iot_physical_stop_request*r){assert(depth&&down&&r->action==WR_STOP_RELEASE);rollback_calls++;return 1;}
int wr_iot_rc_radio_on_rollback_current(const struct wr_iot_physical_stop_request*r){assert(depth&&r->action==WR_STOP_RELEASE);return down&&rollback_calls>0;}
int wr_iot_rc_restart_radio_state(int reload){assert(depth&&down&&reload>=0&&reload<=1&&!ups);ram_calls++;return !ram_fail;}
int wr_iot_rc_restart_multicast_policy(struct wr_iot_multicast_policy*p){p->required=p->enabled=1;p->guest=guest_desired;return 1;}
int wr_iot_restart_multicast_apply(unsigned bss,int enabled){assert(enabled==1&&bss==(unsigned)mc_calls&&guest_state==guest_desired);mc_calls++;return !mc_fail;}
int wr_iot_restart_multicast_current(unsigned bss,int enabled){assert(enabled==1&&bss<2);return mc_read;}
#include "radio-on-multicast.c"
#include "radio-on-restore.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<5;fault++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_restore restore={0};unsigned char id[16]={1};
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=fault!=3;guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;bridge_fail=no_submit=0;
  ram_calls=mc_calls=service_calls=rollback_calls=0;ram_fail=fault==1;mc_fail=fault==2;mc_read=1;up_result=WR_RESTART_UP_RETURNED;
  assert(wr_iot_on_admission_begin(&a));
  assert(wr_iot_on_restore_begin(&restore,&a,&desired,fault!=3,id));
  assert(!wr_iot_on_restore_begin(&restore,&a,&desired,1,id));
  if(fault==4){
   assert(!wr_iot_on_restore_step(&restore));
   wr_iot_rc_shutdown.pending=SIGTERM;
   assert(!wr_iot_on_restore_step(&restore)&&restore.rollback_state_returned&&rollback_calls==1&&!ups);
   assert(!wr_iot_on_restore_step(&restore)&&rollback_calls==1&&a.profile.active&&a.busy);
   wr_iot_rc_shutdown.pending=0;
   wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
   assert(wr_iot_on_admission_cancel(&a)&&!depth);assert(!unlink(profile_path));continue;
  }
  int ready=0;for(int tick=0;tick<30&&!ready;tick++)ready=wr_iot_on_restore_step(&restore);
  if(fault==1){assert(!ready&&ram_calls==1&&!ups&&!service_calls&&restore.phase==WR_ON_RESTORE_RETAINED);}
  else if(fault==2){assert(!ready&&mc_calls==1&&restore.multicast.phase==WR_ON_MC_UNCERTAIN&&!service_calls&&ups==1);}
  else{
   assert(ready&&restore.phase==WR_ON_RESTORE_PREPARED&&ups==1&&ram_calls==1&&mc_calls==(guest_desired?2:1)&&service_calls==3);
   aux_ok=0;assert(!wr_iot_on_restore_step(&restore)&&ups==1&&service_calls==3);aux_ok=1;
   assert(wr_iot_on_restore_step(&restore)&&ups==1&&service_calls==3);
   mc_read=0;assert(!wr_iot_on_restore_step(&restore)&&ups==1&&service_calls==3);mc_read=1;
   assert(wr_iot_on_restore_step(&restore));
   wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_on_restore_step(&restore));wr_iot_rc_shutdown.pending=0;
   if(guest_desired)assert(guest_downs==1&&!guest_state);
  }
  assert(generator_calls==(fault!=3)&&a.busy&&a.profile.active);
  /* Fixture disposal of retained children, never a production retirement. */
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_on_admission_cancel(&a)&&!depth);assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-restore-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON restore actual child composition: profile then RAM once before UP, Main LAN then Guest then multicast then services, reload0/Guest OFF, RAM/MC failure retained with no replay, pending Guest DOWN, no root retirement or device acceptance')
