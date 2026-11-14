"""Actual restore + profile journal/generation/Main; Guest/services actors injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-main-composition.py').read_text()
ns={'__file__':str(here/'check-restart-main-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<main fixture setup>','exec'),ns)
body=ns['body'].split('int main(int argc',1)[0]
body=body.replace('assert(0);return WR_MAIN_BRIDGE_REFUSED;', 'return WR_MAIN_BRIDGE_UNCERTAIN;').replace('assert(0);return 0;', 'return 1;')
body+=r'''
#include "restart-restore.h"
int wr_iot_restart_guest_begin(struct wr_iot_restart_guest*g,struct wr_iot_restart_main*m){g->owner=getpid();g->main=m;return 1;}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){return g->main!=NULL;}
int wr_iot_restart_services_begin(struct wr_iot_restart_services*s,struct wr_iot_restart_main*m){s->owner=getpid();s->main=m;return 1;}
int wr_iot_restart_services_step(struct wr_iot_restart_services*s){return s->main!=NULL;}
int wr_iot_rc_rebind_begin(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p){(void)r;(void)p;return 0;}
int wr_iot_rc_rebind_active_current(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i){(void)r;(void)p;(void)i;return 0;}
#include "check-multicast-owner-actor.h"
#include "restart-restore.c"
int main(int argc,char**argv){
 assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 origin=(struct wr_iot_rc_physical_resume){.intent={1,1,1},.physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}},.resume_needed=1,.desired={.enabled=1,.ssid="IoT",.password="iot-password"}};
 (void)check;(void)restored;char before[4096];size_t n;capture_baseline(before,&n);
 wr_iot_rc_shutdown.active=1;probe_ok=1;
 struct wr_iot_restart_restore s={0};unsigned char id[16]={7};
 assert(wr_iot_restart_restore_begin(&s,id));
 int prepared=0;for(int i=0;i<25&&!prepared;i++)prepared=wr_iot_restart_restore_step(&s);
 assert(prepared&&ups==1&&generator_calls==1&&s.generation.profile.active);
 assert(s.generation.main_may_have_started&&s.main.generation==&s.generation);
 main_down=1;assert(!wr_iot_restart_generation_abort(&s.generation));main_down=0;
 assert(s.generation.profile.active&&s.generation.profile.files.saved[0].data);
 origin.physical.attempt++;assert(!wr_iot_restart_main_step(&s.main));origin.physical.attempt--;
 assert(wr_iot_restart_main_step(&s.main)&&ups==1&&generator_calls==1);
 /* Process-only fixture cleanup. Production snapshot remains retained. */
 wr_iot_bundle_release(&s.generation.profile.files);assert(!unlink(profile_path));
 puts("PASS restore/actual generation/profile/Main: generated file owned across Guest/services phases, uncertain Main once, baseline retained and restore fenced after UP, physical-origin drift refused; Guest/services/driver/transport actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restore-profile-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'test.c';p.write_text(body);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True)
