from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent;root=Path(__file__).resolve().parent
source=(here/'check-restart-finish-check.py').read_text();ns={'__file__':str(here/'check-restart-finish-check.py')};exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<finish actor setup>','exec'),ns)
body='#define WR_IOT_TEST_INITIAL_PARENT 1\n'+ns['body'].split('int main(int argc',1)[0]+r'''
#include "restart-initial-parent.c"
int main(int argc,char **argv){
 assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 (void)check;(void)restored;(void)active_ok;wr_iot_rc_shutdown.active=1;initial_mode=1;
 origin=(struct wr_iot_rc_physical_resume){.origin=WR_PHYSICAL_ORIGIN_INITIAL,.intent={1,1,1},
 .initial={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.idle_serial=3,.attempt=4,.nonce={9}},
 .resume_needed=1,.desired={.enabled=1,.ssid="IoT",.password="iot-password"}};
 strcpy(saved_enabled,"1");char before[4096];size_t n;capture_baseline(before,&n);probe_ok=1;
 struct wr_iot_restart_restore s={0};unsigned char id[16]={7};
 assert(wr_iot_restart_restore_begin(&s,id));
 for(unsigned i=0;i<30&&s.phase!=WR_RESTORE_PREPARED;i++)wr_iot_restart_restore_step(&s);
 assert(s.phase==WR_RESTORE_PREPARED);
 s.busy=1;s.phase=WR_RESTORE_HANDOFF;s.handoff_created=19;
 assert(wr_iot_restart_initial_parent_current(&s,1));
 probe_ok=0;assert(!wr_iot_restart_initial_parent_current(&s,1));assert(wr_iot_restart_initial_parent_current(&s,0));probe_ok=1;
 guest_ok=0;assert(!wr_iot_restart_initial_parent_current(&s,0));guest_ok=1;
 auth_ok=0;assert(!wr_iot_restart_initial_parent_current(&s,0));auth_ok=1;
 strcpy(saved_enabled,"0");assert(!wr_iot_restart_initial_parent_current(&s,0));strcpy(saved_enabled,"1");
 s.main.identity.adapter_epoch=1;assert(!wr_iot_restart_initial_parent_current(&s,0));s.main.identity.adapter_epoch=2;
 s.services.attempted=3;assert(!wr_iot_restart_initial_parent_current(&s,0));s.services.attempted=7;
 origin.initial.attempt++;assert(!wr_iot_restart_initial_parent_current(&s,0));origin.initial.attempt--;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_initial_parent_current(&s,0));wr_iot_rc_shutdown.pending=0;
 assert(!wr_iot_restart_initial_parent_current(&s,2));assert(wr_iot_restart_initial_parent_current(&s,1));
 wr_iot_bundle_release(&s.generation.profile.files);assert(!unlink(profile_path));return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-parent-') as d:
 p=Path(d);(p/'rc.h').write_text('const char *nvram_safe_get(const char *);\n');(p/'check.c').write_text(body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(root),str(p/'check.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check',d],check=True,timeout=15)
print('PASS candidate actual INITIAL prepared parent predicate: exact generation/profile/Main/LAN and child ownership, saved policy/Guest/auth/epoch/origin/pending refusal; idle required preSTART only, postSTART parent predicate is not ACTIVE proof')
