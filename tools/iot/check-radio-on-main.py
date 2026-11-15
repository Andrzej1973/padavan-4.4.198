"""Actual admission/generation/Main controller, injected UP and identity transport."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-generation.py').read_text()
ns={'__file__':str(here/'check-radio-on-generation.py')}
exec(source.split('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-main.h"
static int ups,identity_fault;
static enum wr_iot_restart_up_result up_result;
enum wr_iot_restart_up_result wr_iot_restart_main_up(void){assert(depth&&wr_iot_rc_shutdown.active);ups++;down=0;return up_result;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request*r,const unsigned char*id,struct wr_iot_driver_identity*out){
 assert(depth&&r->action==WR_STOP_RELEASE&&id[0]==1);
 memset(out,0,sizeof(*out));out->adapter_epoch=identity_fault==1?1:identity_fault==3?3:2;
 out->device_generation=identity_fault==2?3:2;return identity_fault!=4;
}
#include "radio-on-main.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int outcome=0;outcome<3;outcome++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_generation g={0};struct wr_iot_on_main m={0};
  unsigned char id[16]={1},zero[16]={0};down=1;partial=0;ups=generator_calls=identity_fault=0;
  make_profile();assert(wr_iot_on_admission_begin(&a));assert(wr_iot_on_generation_begin(&g,&a,&desired,1));
  assert(!wr_iot_on_generation_step(&g)&&wr_iot_on_generation_step(&g)==1);
  assert(!wr_iot_on_main_begin(&m,&g,zero)&&!ups&&!g.main_may_have_started);
  up_result=outcome==0?WR_RESTART_UP_RETURNED:outcome==1?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_NOT_SUBMITTED;
  assert(wr_iot_on_main_begin(&m,&g,id)==(outcome==0));
  assert(ups==1&&g.main_may_have_started&&!wr_iot_on_generation_abort(&g)&&!wr_iot_on_generation_step(&g));
  assert(!wr_iot_on_main_begin(&m,&g,id)&&ups==1&&!wr_iot_on_admission_cancel(&a));
  if(outcome<2){
   for(identity_fault=1;identity_fault<=2;identity_fault++)assert(!wr_iot_on_main_step(&m));
   identity_fault=4;assert(!wr_iot_on_main_step(&m));identity_fault=0;
   assert(wr_iot_on_main_step(&m)&&m.phase==WR_ON_MAIN_READY);
   identity_fault=3;assert(!wr_iot_on_main_step(&m));identity_fault=0;
   wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_on_main_step(&m));wr_iot_rc_shutdown.pending=0;
   assert(wr_iot_on_main_step(&m)&&ups==1);
   receipt.attempt++;assert(!wr_iot_on_main_step(&m));receipt.attempt--;
  }else assert(!wr_iot_on_main_step(&m));
  assert(ups==1&&generator_calls==1&&a.profile.active&&a.busy);
  /* Fixture teardown only; no post-UP retirement API is implemented here. */
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_on_admission_cancel(&a)&&!depth);assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-main-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON Main actual admission/generation/controller: one UP max for returned/uncertain/not-submitted, pre-UP restore fenced before call, new epoch and same device generation, stale receipt/epoch drift/pending refuse, baseline retained; transport actors, no device acceptance')
