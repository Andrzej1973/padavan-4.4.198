"""Actual profile generation/journal/controller composition; hardware injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-generation.py').read_text();ns={'__file__':str(here/'check-restart-generation.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<generation fixture setup>','exec'),ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "restart-main-controller.h"
static int ups,probe_ok;static unsigned long long new_epoch=2;
enum wr_iot_restart_up_result wr_iot_restart_main_up(void){ups++;main_down=0;return WR_RESTART_UP_UNCERTAIN;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request*p,const unsigned char*id,struct wr_iot_driver_identity*out){assert(p->epoch==1&&id[0]==7);*out=(struct wr_iot_driver_identity){new_epoch,2};return probe_ok;}
#include "restart-main-bridge.h"
enum wr_iot_main_bridge_result wr_iot_restart_main_bridge_attach(void){assert(0);return WR_MAIN_BRIDGE_REFUSED;}
int wr_iot_restart_main_bridge_current(void){assert(0);return 0;}
#include "restart-main-controller.c"
int main(int argc,char**argv){
 assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 origin=(struct wr_iot_rc_physical_resume){.intent={1,1,1},.physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}},.resume_needed=1,.desired={.enabled=1,.ssid="IoT",.password="iot-password"}};
 (void)check;wr_iot_rc_shutdown.active=1;struct wr_iot_restart_generation g={0};struct wr_iot_restart_main s={0};unsigned char id[16]={7};
 char before[4096];size_t n;capture_baseline(before,&n);(void)restored;
 assert(wr_iot_restart_generation_begin(&g));assert(!wr_iot_restart_generation_step(&g));assert(wr_iot_restart_generation_step(&g));
 assert(!wr_iot_restart_main_begin(&s,&g,id)&&ups==1&&g.main_may_have_started&&s.phase==WR_MAIN_WAIT);
 assert(!wr_iot_restart_main_begin(&s,&g,id)&&ups==1);
 main_down=1;assert(!wr_iot_restart_generation_abort(&g)&&!wr_iot_restart_generation_step(&g)&&g.profile.active);main_down=0;
 assert(!wr_iot_restart_main_step(&s));probe_ok=1;
 origin.physical.attempt++;assert(!wr_iot_restart_main_step(&s));origin.physical.attempt--;
 assert(wr_iot_restart_main_step(&s)&&s.phase==WR_MAIN_READY&&g.profile.active&&ups==1);
 new_epoch=3;assert(!wr_iot_restart_main_step(&s));new_epoch=2;
 assert(wr_iot_restart_main_step(&s)&&ups==1&&generator_calls==1);
 char foreign[1100];snprintf(foreign,sizeof(foreign),"%s/replacement",argv[1]);
 FILE *in=fopen(profile_path,"r"),*out=fopen(foreign,"w");assert(in&&out);int c;
 while((c=fgetc(in))!=EOF)assert(fputc(c,out)!=EOF);
 assert(!fclose(in)&&!fclose(out)&&!rename(foreign,profile_path));
 assert(wr_iot_restart_profile_current(&origin.desired));
 assert(!wr_iot_restart_main_step(&s)&&ups==1&&g.profile.active);
 /* Test process cleanup frees RAM only; production baseline remains owned. */
 wr_iot_bundle_release(&g.profile.files);assert(!unlink(profile_path));
 puts("PASS actual generation/profile journal/Main controller: uncertain UP once, no profile restore after possible UP even when DOWN, changed RELEASE refuses readiness, fresh new epoch pinned; physical/UP/probe actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-main-compose-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n');unit=root/'check.c';unit.write_text(body);out=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(out)],check=True)
 subprocess.run([str(out),d],check=True)
