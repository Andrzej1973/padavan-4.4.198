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
int wr_iot_restart_guest_begin(struct wr_iot_restart_guest*g,struct wr_iot_restart_main*m){g->owner=getpid();g->main=m;g->desired=1;g->isolate=1;g->phase=WR_GUEST_ADMIN_UP;return 1;}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){return g->main!=NULL;}
int wr_iot_restart_services_begin(struct wr_iot_restart_services*s,struct wr_iot_restart_main*m){s->owner=getpid();s->main=m;s->phase=WR_SERVICES_SUBMITTED;s->next=3;s->attempted=7;s->policy=(struct wr_iot_restart_service_policy){0,-75,-80};return 1;}
int wr_iot_restart_services_step(struct wr_iot_restart_services*s){return s->main!=NULL;}
int wr_iot_rc_rebind_begin(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p){(void)r;(void)p;return 0;}
static int active_ok,guest_ok=1,auth_ok=1;
int wr_iot_rc_rebind_active_current(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i){(void)r;(void)p;(void)i;return active_ok;}
#include "check-multicast-owner-actor.h"
int wr_iot_rc_restart_radio_state(int reload){assert(reload==0||reload==1);return 1;}
#include "restart-restore.c"
int wr_iot_rc_restart_guest_policy(int*out){*out=1;return guest_ok;}
int wr_iot_rc_restart_guest_isolation_policy(int*out){*out=1;return 1;}
int wr_iot_restart_guest_admin_state(int*out){*out=1;return 1;}
int wr_iot_restart_guest_bridge_current(void){return 1;}
int wr_iot_restart_guest_isolation_current(int isolate){return isolate==1;}
int wr_iot_rc_restart_service_policy(struct wr_iot_restart_service_policy*p){*p=(struct wr_iot_restart_service_policy){0,-75,-80};return 1;}
int wr_iot_rc_restart_auth_process_current(const struct wr_iot_restart_service_policy*p){(void)p;return auth_ok;}
#include "restart-finish-check.c"
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
 struct wr_iot_control_request request={.id="07000000000000000000000000000000",.created=10};request.request=origin.desired;
 assert(!wr_iot_restart_restore_handoff(&s,&request)&&s.phase==WR_RESTORE_HANDOFF);
 assert(!wr_iot_restart_restore_finish_check(&s));active_ok=1;
 assert(wr_iot_restart_restore_finish_check(&s)&&s.generation.profile.active);
 guest_ok=0;assert(!wr_iot_restart_restore_finish_check(&s));guest_ok=1;
 auth_ok=0;assert(!wr_iot_restart_restore_finish_check(&s));auth_ok=1;
 s.multicast.busy=1;assert(!wr_iot_restart_restore_finish_check(&s));s.multicast.busy=0;
 s.multicast.phase=WR_MC_UNCERTAIN;assert(!wr_iot_restart_restore_finish_check(&s));s.multicast.phase=WR_MC_READY;
 s.multicast.main=NULL;assert(!wr_iot_restart_restore_finish_check(&s));s.multicast.main=&s.main;
 s.services.attempted=3;assert(!wr_iot_restart_restore_finish_check(&s));s.services.attempted=7;
 assert(wr_iot_restart_restore_finish_check(&s)&&ups==1&&generator_calls==1);
 /* Process-only fixture cleanup. Production snapshot remains retained. */
 wr_iot_bundle_release(&s.generation.profile.files);assert(!unlink(profile_path));
 puts("PASS finish software gate/actual generation/profile/Main/root: ACTIVE, Guest, auth and service receipts checked; generated file owned across Guest/services phases, uncertain Main once, baseline retained and restore fenced after UP, physical-origin drift refused; Guest/services/driver/transport actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-finish-check-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'test.c';p.write_text(body);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True)
