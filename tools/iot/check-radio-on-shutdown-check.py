"""Actual ON handoff/shutdown witness with exact backend boundary actor."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-handoff.py').read_text();ns={'__file__':str(here/'check-radio-on-handoff.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-shutdown-check.h"
static int closed_ready,rejected_ready;
int wr_iot_rc_rebind_shutdown_closed(const struct wr_iot_control_result*on,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i,const struct wr_iot_rc_quiesce*off,struct wr_iot_driver_closed_result*out){
 assert(on->created==10&&!strcmp(on->id,"01000000000000000000000000000000")&&p->epoch==1);
 (void)out;return closed_ready&&i->adapter_epoch==2&&off->complete&&!off->active;
}
int wr_iot_rc_rebind_preopen_rejected(const struct wr_iot_control_result*on,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i){assert(on->created==10&&p->epoch==1);return rejected_ready&&i->adapter_epoch==2;}
#include "radio-on-shutdown-check.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_on_admission a={0};struct wr_iot_on_restore r={0};unsigned char id[16]={1};
 down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;make_profile();
 guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
 bridge_fail=no_submit=ram_fail=mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
 assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_restore_begin(&r,&a,&desired,1,id));
 int ready=0;for(int t=0;t<30&&!ready;t++)ready=wr_iot_on_restore_step(&r);assert(ready);
 struct wr_iot_control_request input={.id="01000000000000000000000000000000",.created=10,.request=desired};admitted=1;
 assert(wr_iot_on_restore_handoff(&r,&input));
 struct wr_iot_rc_quiesce off={.owner=getpid(),.complete=1};
 assert(!wr_iot_on_shutdown_closed_current(&r,&off));
 wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_on_guest_step(&r.guest)&&guest_downs==1&&!guest_state);
 assert(!wr_iot_on_shutdown_closed_current(&r,&off));closed_ready=1;
 assert(wr_iot_on_shutdown_closed_current(&r,&off));
 off.active=1;assert(!wr_iot_on_shutdown_closed_current(&r,&off));off.active=0;
 assert(!wr_iot_on_shutdown_rejected_current(&r));rejected_ready=1;
 assert(wr_iot_on_shutdown_rejected_current(&r)&&wr_iot_on_shutdown_closed_current(&r,NULL));
 r.main.identity.adapter_epoch=3;assert(!wr_iot_on_shutdown_closed_current(&r,&off)&&!wr_iot_on_shutdown_rejected_current(&r));r.main.identity.adapter_epoch=2;
 receipt.attempt++;assert(!wr_iot_on_shutdown_closed_current(&r,&off));receipt.attempt--;
 assert(wr_iot_on_shutdown_closed_current(&r,&off)&&a.profile.active&&a.busy&&ups==1);
 wr_iot_rc_shutdown.pending=0;wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
 assert(wr_iot_on_admission_cancel(&a)&&!depth&&!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-shutdown-check-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON post-handoff shutdown witnesses actual parent: pending/Guest DOWN, exact ON+RELEASE+new identity, CLOSED or separate pre-OPEN rejection, active/stale refusal, baseline retained; backend actor, no cleanup or hardware acceptance')
