from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-off-followup.py').read_text();ns={'__file__':str(here/'check-radio-off-followup.py')}
exec(compile(source[:source.rindex('with tempfile.TemporaryDirectory(')],'<OFF followup fixture>','exec'),ns)
body=ns['body'].split('int main(int argc',1)[0]
old='int wr_iot_terminal_iapp_step(struct wr_iot_terminal_iapp*s){(void)s;assert(0);return 0;}'
assert old in body
body=body.replace(old,r'''
#define WR_IOT_IAPP_POLICY_H
#define WR_IOT_IAPP_POLICY_PREPARED 1
static int iapp_begins,iapp_steps,iapp_result;
int wr_iot_terminal_iapp_begin(struct wr_iot_terminal_iapp*s,struct wr_iot_iapp_child*c){
 assert(!depth&&!wr_iot_rc_shutdown.active&&!s->owner&&!c->owner&&bridge_observations==14);
 iapp_begins++;s->owner=getpid();s->child=c;wr_iot_rc_shutdown.active=1;return 1;
}
int wr_iot_terminal_iapp_step(struct wr_iot_terminal_iapp*s){
 assert(s->owner==getpid()&&wr_iot_rc_shutdown.active);iapp_steps++;
 if(iapp_result){s->child->owner=getpid();s->child->attempted=1;s->child->fd=-1;s->child->result=iapp_result;s->result=iapp_result;s->child=0;wr_iot_rc_shutdown.active=0;}
 return iapp_result;
}
''')
body+=r'''
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_radio_off_owner off={.owner=getpid(),.result=1,.policy_ready=1,.policy={.reload=1},.released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
 for(int failure=0;failure<2;failure++){
  struct wr_iot_off_followup s={0};make_profile();generator_calls=state_calls=auth_calls=0;
  bridge_calls=bridge_observations=0;wan_calls=iapp_begins=iapp_steps=iapp_result=0;
  wr_iot_rc_shutdown.radio_off_owned=1;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_off_followup_begin(&s,&off));
  for(int i=0;i<50&&s.phase!=WR_OFF_FOLLOWUP_IAPP;i++)(void)wr_iot_off_followup_step(&s);
  assert(s.phase==WR_OFF_FOLLOWUP_IAPP&&iapp_begins==1&&!iapp_steps&&s.profile.baseline.active);
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(wr_iot_off_followup_step(&s)==WR_OFF_FOLLOWUP_IAPP&&iapp_steps==1);
  iapp_result=failure?-1:1;
  assert(wr_iot_off_followup_step(&s)==(failure?WR_OFF_FOLLOWUP_RETAINED:WR_OFF_FOLLOWUP_FINAL_PENDING));
  assert(iapp_begins==1&&iapp_steps==2&&s.profile.baseline.active&&wr_iot_rc_shutdown.radio_off_owned);
  wr_iot_rc_shutdown.pending=0;
  if(!failure){
   assert(wr_iot_service_guard_enter(1)==1);
   assert(wr_iot_off_followup_final_current(&s));
   s.child.fd=9;assert(!wr_iot_off_followup_final_current(&s));s.child.fd=-1;
   s.profile.baseline.files.pending=1;assert(!wr_iot_off_followup_final_current(&s));s.profile.baseline.files.pending=0;
   observed=0;assert(!wr_iot_off_followup_final_current(&s));observed=1;
   assert(wr_iot_off_followup_final_current(&s)&&s.profile.baseline.active&&wr_iot_rc_shutdown.radio_off_owned);
   wr_iot_service_guard_leave(1);
  }
  for(int i=0;i<3;i++)(void)wr_iot_off_followup_step(&s);
  assert(iapp_begins==1&&iapp_steps==2&&generator_calls==1&&!wan_calls);
  wr_iot_bundle_release(&s.profile.baseline.files);assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-iapp-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS OFF gated IAPP order: after post-WAN observations, begin once, active/pending shutdown drains terminal, failure retained, final pending preserves baseline/exclusion; terminal actor injected')
