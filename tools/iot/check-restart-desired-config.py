#!/usr/bin/env python3
"""Run existing restart journal regression with actual desired store enabled."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
text=(here/'check-restart-generation.py').read_text()
ns={'__file__':str(here/'check-restart-generation.py')}
exec(compile(text[:text.index('with tempfile.TemporaryDirectory(')],'<restart-fixture>','exec'),ns)
tree=ast.parse((here/'check-cold-config-revision.py').read_text())
provider=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='provider' for t in n.targets))
body=ns['body'].replace('#include "restart-generation.c"','int wr_iot_service_guard_enter(int enabled){assert(enabled==1);return guard?1:0;}\nvoid wr_iot_service_guard_leave(int token){assert(token==1); }\n'+provider+'\n#include "restart-generation.c"')
# Proven absence exercises existing CLOSE and INITIAL restoration/retirement
# under actual coherent native snapshot checks. Present/new profiles next.
body=body.replace('int main(int argc,char**argv)', 'int legacy_restart_main(int argc,char**argv)',1)
body=body.replace('#include "restart-generation.h"','#include "restart-generation.h"\n#include "generation-profile.h"',1)
anchor='make_profile();return 0;}'
replacement=r'''struct wr_iot_precreated_profile_request selected={0};
 int kind=wr_iot_generation_profile_request(&selected);assert(kind>=0);
 if(kind){FILE*in=tmpfile(),*out=fopen(profile_path,"w");assert(in&&out);
  assert(fputs(baseline,in)>=0);rewind(in);
  assert(wr_iot_precreated_profile(in,out,selected.ssid,selected.password,0));
  assert(!fclose(in)&&!fclose(out));
 }else make_profile();return 0;}'''
assert anchor in body
body=body.replace(anchor,replacement,1)
body=body.rstrip()[:-1]+'return 0;\n}\n'
body+=r'''
#include "restart-main-controller.h"
#include "restart-main-bridge.h"
static int main_ups;
enum wr_iot_restart_up_result wr_iot_restart_main_up(void){main_ups++;main_down=0;return WR_RESTART_UP_RETURNED;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request *p,
 const unsigned char *id,struct wr_iot_driver_identity *out){
 assert(p->epoch==1&&id[0]==7);*out=(struct wr_iot_driver_identity){2,2};return 1;
}
int wr_iot_initial_main_current(const struct wr_iot_physical_initial_request *p,
 const unsigned char *id,struct wr_iot_driver_identity *out){(void)p;(void)id;(void)out;assert(0);return 0;}
enum wr_iot_main_bridge_result wr_iot_restart_main_bridge_attach(void){assert(0);return WR_MAIN_BRIDGE_REFUSED;}
int wr_iot_restart_main_bridge_current(void){assert(0);return 0;}
#include "restart-main-controller.c"
int main(int argc,char**argv){
 assert(legacy_restart_main(argc,argv)==0);
 for(int scenario=0;scenario<4;scenario++){
  struct wr_iot_restart_generation g={0};
  struct wr_iot_saved_config config={.profile={.enabled=1,.ssid="New restart IoT",
   .password="new-restart-password",.gateway="192.168.50.1",.mask="255.255.255.0",
   .first="192.168.50.20",.last="192.168.50.200"}};
  char before[4096];size_t n;
  origin=(struct wr_iot_rc_physical_resume){.intent={1,1,1},
   .physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}},
   .resume_needed=1,.desired=config.profile};
  initial_mode=0;main_down=guard=1;guard_after=drift=0;reads=0;
  origin_reads=fail_origin_at=generator_calls=generator_failure=record_error=0;
  record_present=1;
  if(scenario==1){
   config.profile.enabled=0;origin.origin=WR_PHYSICAL_ORIGIN_INITIAL;
   origin.initial=(struct wr_iot_physical_initial_request){.action=WR_STOP_RELEASE,
    .epoch=1,.generation=2,.idle_serial=3,.attempt=4,.nonce={9}};
   memset(&origin.physical,0,sizeof(origin.physical));
   memset(&origin.desired,0,sizeof(origin.desired));origin.resume_needed=0;initial_mode=1;
  }
  assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
  capture_baseline(before,&n);
  if(scenario==2){strcpy(origin.desired.ssid,"Wrong request");
   assert(!wr_iot_restart_generation_begin(&g)&&!g.owner&&!g.profile.active&&!generator_calls);
   restored(before,n);assert(!unlink(profile_path));continue;
  }
  assert(wr_iot_restart_generation_begin(&g));
  assert(!wr_iot_restart_generation_step(&g)&&generator_calls==1);
  if(scenario==3){
   strcpy(config.profile.ssid,"Changed desired");
   assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
   assert(!wr_iot_restart_generation_step(&g));
   for(unsigned step=0;step<4&&g.phase!=WR_RESTART_GEN_ROLLED_BACK;step++)
    assert(!wr_iot_restart_generation_step(&g));
   assert(g.phase==WR_RESTART_GEN_ROLLED_BACK&&generator_calls==1);restored(before,n);
  }else{
   assert(wr_iot_restart_generation_step(&g)&&g.phase==WR_RESTART_GEN_VERIFIED);
   assert(restart_config_profile_current(&g));
   assert(wr_iot_restart_generation_profile_current(&g));
   struct wr_iot_restart_generation copied=g;
   assert(!wr_iot_restart_generation_profile_current(&copied));
   if(scenario==0){
    struct wr_iot_restart_main main={0};unsigned char id[16]={7};
    assert(!wr_iot_restart_profile_current(&origin.desired));
    assert(wr_iot_restart_main_begin(&main,&g,id)&&main_ups==1);
    strcpy(config.profile.ssid,"Later desired C");
    assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
    assert(wr_iot_restart_main_step(&main)&&main.phase==WR_MAIN_READY);
    assert(wr_iot_restart_generation_profile_current(&g));
    make_profile();assert(!wr_iot_restart_main_step(&main)&&main_ups==1);
    /* Fixture-only disposal after fake Main actor; no production rollback. */
    wr_iot_bundle_release(&g.profile.files);
    assert(wr_iot_generation_config_release(&g.config_revision));
    wr_iot_saved_wipe(&g.provisioning,sizeof(g.provisioning));
    assert(!unlink(profile_path));continue;
   }
   if(scenario==0)assert(!wr_iot_restart_profile_current(&origin.desired));
   assert(wr_iot_restart_generation_abort(&g));
   for(unsigned step=0;step<4&&g.phase!=WR_RESTART_GEN_ROLLED_BACK;step++)
    assert(!wr_iot_restart_generation_step(&g));
   assert(g.phase==WR_RESTART_GEN_ROLLED_BACK);restored(before,n);
  }
  {
   struct wr_iot_generation_config empty={0};struct wr_iot_saved_config no_credentials={0};
   assert(!memcmp(&g.config_revision,&empty,sizeof(empty)));
   assert(!memcmp(&g.provisioning,&no_credentials,sizeof(no_credentials)));
  }
  assert(!unlink(profile_path));
 }
 return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='wr-restart-desired-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((here.parent/'band-steering/settings-snapshot.h').read_bytes())
 (root/'check.c').write_text(body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20','-I'+d,'-I'+str(here),str(root/'check.c'),str(here.parent/'band-steering/settings-snapshot.c'),'-o',str(root/'check')],check=True)
 subprocess.run([str(root/'check'),d],check=True,timeout=15)
print('PASS actual restart generation/journal with native desired capture enabled and proven absent record; CLOSE/INITIAL original regression, injected native/SDK boundaries; new ON/OFF credentials, mismatched request and drift recovery covered; no physical acceptance')

print('PASS restart Main observes retained B with unchanged legacy A and later desired C; copied generation and foreign A file refuse; native revision/file/controller actual, Main/driver actors injected')
