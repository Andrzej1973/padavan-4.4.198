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
 assert(argc==3);int scenario=atoi(argv[2]);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 origin=(struct wr_iot_rc_physical_resume){.intent={1,1,1},.physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}},.resume_needed=1,.desired={.enabled=1,.ssid="IoT",.password="iot-password"}};
 (void)check;(void)restored;char before[4096];size_t n;capture_baseline(before,&n);
 wr_iot_rc_shutdown.active=1;probe_ok=1;
 struct wr_iot_restart_restore s={0};unsigned char id[16]={7};
 assert(wr_iot_restart_restore_begin(&s,id));
 if(scenario!=1)assert(!wr_iot_restart_restore_step(&s)); /* actual generator once */
 if(scenario==2){
  char foreign[1100];snprintf(foreign,sizeof(foreign),"%s/foreign",argv[1]);
  FILE*f=fopen(foreign,"w");assert(f&&fputs("foreign-owner\n",f)>=0&&!fclose(f));
  assert(!rename(foreign,profile_path));
 }
 wr_iot_rc_shutdown.pending=SIGTERM;
 for(int i=0;i<8&&s.generation.phase!=WR_RESTART_GEN_ROLLED_BACK;i++)
  assert(!wr_iot_restart_restore_step(&s));
 if(scenario==2){
  assert(s.generation.phase==WR_RESTART_GEN_RECOVERING&&s.generation.profile.active&&s.generation.origin.desired.password[0]);
  char bytes[32]={0};FILE*f=fopen(profile_path,"r");assert(f&&fgets(bytes,sizeof(bytes),f)&&!fclose(f));assert(!strcmp(bytes,"foreign-owner\n"));
  assert(!ups&&generator_calls==1);
 }else{
 assert(s.generation.phase==WR_RESTART_GEN_ROLLED_BACK&&!s.generation.profile.active);
 assert(!s.generation.origin.desired.password[0]&&!ups&&generator_calls==(scenario==1?0:1));
 restored(before,n);
 assert(wr_iot_restart_profile_receipt_current(&s.generation.rollback_receipt));
 assert(!s.generation.profile.files.saved[0].data);
 assert(wr_iot_restart_generation_rollback_current(&s.generation));
 origin.physical.attempt++;assert(!wr_iot_restart_generation_rollback_current(&s.generation));origin.physical.attempt--;
 main_down=0;assert(!wr_iot_restart_generation_rollback_current(&s.generation));main_down=1;
 s.generation.main_may_have_started=1;assert(!wr_iot_restart_generation_rollback_current(&s.generation));s.generation.main_may_have_started=0;
 assert(wr_iot_restart_generation_rollback_current(&s.generation));
 }
 assert(wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.pending==SIGTERM);
 /* Process-only fixture cleanup. Production snapshot remains retained. */
 wr_iot_bundle_release(&s.generation.profile.files);assert(!unlink(profile_path));
 puts("PASS actual pre-Main shutdown: pre/post-write rollback, foreign file retained without overwrite, zero Main UP, physical admission retained; driver/probe actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restore-premain-stop-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'test.c';p.write_text(body);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 for scenario in range(3):subprocess.run([str(b),d,str(scenario)],check=True)
