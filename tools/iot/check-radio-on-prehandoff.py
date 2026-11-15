from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-restore.py').read_text();ns={'__file__':str(here/'check-radio-on-restore.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-prehandoff.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_on_admission a={0};struct wr_iot_on_restore r={0};unsigned char id[16]={1};
 down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;make_profile();
 guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
 bridge_fail=no_submit=ram_fail=mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
 assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_restore_begin(&r,&a,&desired,1,id));
 int ready=0;for(int t=0;t<30&&!ready;t++)ready=wr_iot_on_restore_step(&r);assert(ready);
 assert(!wr_iot_on_prehandoff_cancel_current(&r));
 wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_on_prehandoff_cancel_current(&r)); /* Guest still UP. */
 assert(!wr_iot_on_restore_step(&r)&&guest_downs==1&&!guest_state);
 assert(wr_iot_on_prehandoff_cancel_current(&r)&&ups==1&&a.profile.active);
 identity_fault=1;assert(!wr_iot_on_prehandoff_cancel_current(&r));identity_fault=0;
 identity_fault=2;assert(!wr_iot_on_prehandoff_cancel_current(&r));identity_fault=0;
 r.handoff_created=10;assert(!wr_iot_on_prehandoff_cancel_current(&r));r.handoff_created=0;
 r.main.phase=WR_ON_MAIN_NOT_SUBMITTED;assert(!wr_iot_on_prehandoff_cancel_current(&r));r.main.phase=WR_ON_MAIN_READY;
 receipt.attempt++;assert(!wr_iot_on_prehandoff_cancel_current(&r));receipt.attempt--;
 assert(wr_iot_on_prehandoff_cancel_current(&r)&&a.busy&&ups==1&&guest_downs==1);
 /* Fixture disposal only: witness grants no post-UP retirement API. */
 wr_iot_rc_shutdown.pending=0;wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
 assert(wr_iot_on_admission_cancel(&a)&&!depth&&!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-prehandoff-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON prehandoff shutdown witness actual restore: Guest recovery DOWN, exact new Main/config/profile, old/wrong epoch and receipt/no-submission/handoff refusal, baseline retained; SDK actors, no post-UP retirement or device proof')
