"""Actual ON shutdown progression with backend/quiesce boundary actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-shutdown-check.py').read_text();ns={'__file__':str(here/'check-radio-on-shutdown-check.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
static int stop_begins,stop_steps,stop_ready,allow_stop;
int wr_iot_rc_quiesce_shutdown_begin(struct wr_iot_rc_quiesce*s,const struct wr_iot_control_request*off){
 assert(!s->owner&&!off->request.enabled&&off->created==11&&!strcmp(off->id,"02000000000000000000000000000000"));
 if(!allow_stop)return 0;
 stop_begins++;s->owner=getpid();s->active=1;memcpy(s->id,off->id,33);s->created=off->created;return 1;
}
int wr_iot_rc_quiesce_advance(struct wr_iot_rc_quiesce*s,struct wr_iot_driver_closed_result*out){
 (void)out;stop_steps++;if(!stop_ready)return 0;s->active=0;s->complete=1;closed_ready=1;return 1;
}
#include "radio-on-shutdown.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int rejected=0;rejected<2;rejected++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_restore r={0};struct wr_iot_on_shutdown stop={0};unsigned char id[16]={1};
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=ram_calls=mc_calls=service_calls=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=no_submit=ram_fail=mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_restore_begin(&r,&a,&desired,1,id));
  int ready=0;for(int t=0;t<30&&!ready;t++)ready=wr_iot_on_restore_step(&r);assert(ready);
  struct wr_iot_control_request input={.id="01000000000000000000000000000000",.created=10,.request=desired};admitted=1;
  assert(wr_iot_on_restore_handoff(&r,&input));
  struct wr_iot_control_request off={.id="02000000000000000000000000000000",.created=11};
  assert(!wr_iot_on_shutdown_begin(&stop,&r,&off));wr_iot_rc_shutdown.pending=SIGTERM;
  off.created=9;assert(!wr_iot_on_shutdown_begin(&stop,&r,&off));off.created=11;
  strcpy(off.id,input.id);assert(!wr_iot_on_shutdown_begin(&stop,&r,&off));strcpy(off.id,"02000000000000000000000000000000");
  strcpy(off.request.password,"must-not-retain");
  stop_begins=stop_steps=stop_ready=closed_ready=rejected_ready=allow_stop=0;
  assert(wr_iot_on_shutdown_begin(&stop,&r,&off)&&!stop.input.request.password[0]);
  assert(!wr_iot_on_shutdown_begin(&stop,&r,&off));
  assert(!wr_iot_on_shutdown_step(&stop)&&guest_downs==1&&!stop_begins);
  if(rejected){rejected_ready=1;assert(wr_iot_on_shutdown_step(&stop)&&stop.phase==WR_ON_STOP_REJECTED&&!stop_begins&&!stop_steps);}
  else{
   allow_stop=1;assert(!wr_iot_on_shutdown_step(&stop)&&stop_begins==1&&stop.phase==WR_ON_STOP_DRAIN);
   assert(!wr_iot_on_shutdown_step(&stop)&&stop_steps==1);
   stop_ready=1;assert(wr_iot_on_shutdown_step(&stop)&&stop.phase==WR_ON_STOP_CLOSED&&stop_begins==1);
  }
  int count=continues;assert(wr_iot_on_shutdown_step(&stop)&&continues==count&&stop_begins==!rejected&&ups==1&&a.profile.active);
  receipt.attempt++;assert(!wr_iot_on_shutdown_step(&stop));receipt.attempt--;
  wr_iot_rc_shutdown.pending=0;wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_on_admission_cancel(&a)&&!depth&&!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-shutdown-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON shutdown controller actual parent/checks: exact OFF ID/time, credentials omitted, Guest down, retained continuation then one admitted OFF, bounded drain, CLOSED distinct from REJECTED/no OFF, stale receipt holds; backend actors, no root release/runtime')
