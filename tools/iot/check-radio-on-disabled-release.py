"""Actual disabled parent release through RC receipt and signal fence."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-release.py')}
exec((here/'check-radio-on-release.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-disabled.h"
static int idle_ok=1;
int wr_iot_initial_off_begin(struct wr_iot_initial_off*s,const struct wr_iot_control_request*r){assert(!r->request.enabled);s->owner=getpid();s->ready=1;return 1;}
int wr_iot_initial_off_restarted_observed(const struct wr_iot_initial_off*s,const struct wr_iot_physical_stop_request*r,const struct wr_iot_driver_identity*m){assert(s->ready&&r->action==WR_STOP_RELEASE&&m->adapter_epoch==2);return idle_ok;}
int wr_iot_on_followup_observed(struct wr_iot_on_restore*r,int(*o)(struct wr_iot_on_restore*,void*),void*c){(void)r;(void)o;(void)c;assert(0);return 0;}
int wr_iot_initial_off_observed(const struct wr_iot_initial_off*s){(void)s;assert(0);return 0;}
#include "radio-on-disabled.c"
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_on_admission a={0};struct wr_iot_on_restore restore={0};struct wr_iot_on_disabled witness={0};
 struct wr_iot_request off={0};unsigned char id[16]={1};
 make_profile();membership=guest_desired=guest_isolate=1;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
 assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_restore_begin(&restore,&a,&off,1,id));
 int ready=0;for(int tick=0;tick<30&&!ready;tick++)ready=wr_iot_on_restore_step(&restore);assert(ready);
 struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10};
 assert(wr_iot_on_disabled_begin(&witness,&restore,&r));
 receipt.attempt++;assert(!wr_iot_on_disabled_release(&witness)&&a.profile.active);receipt.attempt--;
 auth_current=0;assert(!wr_iot_on_disabled_release(&witness)&&a.profile.active);auth_current=1;
 fail_unmask=1;assert(!wr_iot_on_disabled_release(&witness)&&a.profile.active&&radio_off_receipt_valid&&depth==1);
 fail_unmask=0;idle_ok=0;assert(!wr_iot_on_disabled_release(&witness)&&a.profile.active&&radio_off_receipt_valid);
 idle_ok=1;assert(wr_iot_on_disabled_release(&witness));
 assert(restore.phase==WR_ON_RESTORE_RELEASED&&!radio_on_releasing&&!a.profile.active&&!a.profile.files.count&&!a.guard&&!depth&&!radio_off_receipt_valid);
 assert(!wr_iot_on_disabled_release(&witness));
 assert(wr_iot_wan_followup_step(&restore.wan)&&wan_submits==1);
 assert(wr_iot_wan_followup_step(&restore.wan)&&wan_submits==1);
 assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-disabled-release-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS disabled RC release: exact receipt/auth, failed unmask holds, fresh idle rechecked on retry, profile wiped/receipt consumed once, WAN after release only; SDK actors')
