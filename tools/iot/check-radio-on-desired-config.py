#!/usr/bin/env python3
"""Actual cold generation plus native desired store; external DOWN/SDK actors."""
from pathlib import Path
import ast
import subprocess
import tempfile
here=Path(__file__).resolve().parent
text=(here/'check-radio-on-generation.py').read_text()
# Resolve its existing composed C fixture without executing compilation.
cut=text.index('with tempfile.TemporaryDirectory(')
namespace={'__file__':str(here/'check-radio-on-generation.py')}
exec(compile(text[:cut],'<cold-fixture>','exec'),namespace)
body=namespace['body'].split('int main(int argc',1)[0]
provider=r'''
#include "saved-config-store.h"
static char desired_record[WR_IOT_SAVED_CONFIG_MAX];
static int record_present,record_error;
int nvram_getall(char *out,int size,int temporary){
 size_t n=0;assert(temporary==1);if(record_error)return -1;
 memset(out,0,(size_t)size);
 if(record_present){n=strlen(WR_IOT_SAVED_CONFIG_KEY)+strlen(desired_record)+2;
  assert(n+1<(size_t)size);snprintf(out,(size_t)size,"%s=%s",WR_IOT_SAVED_CONFIG_KEY,desired_record);}
 return 0;
}
int nvram_set(const char *key,const char *value){(void)key;(void)value;assert(0);return -1;}
#include "saved-config-store.c"
'''
body=body.replace('#include "radio-on-generation.c"',provider+'\n#include "radio-on-generation.c"')
body=body.replace('#include "radio-on-generation.h"','#include "radio-on-generation.h"\n#include "generation-profile.h"',1)
body=body.replace('int wr_iot_rc_off_profile_current(void){return wr_iot_restart_profile_current(&desired);}',
 'int wr_iot_rc_off_profile_current(void){struct wr_iot_request loaded={.enabled=1,.ssid="IoT",.password="iot-password"};return wr_iot_restart_profile_current(&loaded);}')
anchor='make_profile();return 0;}\n#include "radio-on-admission.c"'
replacement=r'''struct wr_iot_precreated_profile_request selected={0};
 int kind=wr_iot_generation_profile_request(&selected);assert(kind>=0);
 if(kind==1){
  FILE *in=tmpfile(),*out=fopen(profile_path,"w");assert(in&&out);
  assert(fputs(baseline,in)>=0);rewind(in);
  assert(wr_iot_precreated_profile(in,out,selected.ssid,selected.password,0));
  assert(!fclose(in)&&!fclose(out));
 }else make_profile();return 0;}
#include "radio-on-admission.c"'''
assert anchor in body
body=body.replace(anchor,replacement,1)

body+=r'''
int main(int argc,char **argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");
 strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 for(int fault=0;fault<9;fault++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_generation g={0},copy;
  struct wr_iot_saved_config config;
  strcpy(desired.ssid,fault>=7?"New desired IoT":"IoT");config.profile=desired;
  if(fault==8){config.profile.enabled=0;memset(&desired,0,sizeof(desired));}
  record_error=0;record_present=fault!=0;generator_calls=partial=0;make_profile();
  assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
  if(fault==2){strcpy(config.profile.ssid,"Other");assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));}
  if(fault==6)strcpy(desired_record,"malformed");
  assert(wr_iot_on_admission_begin_reload(&a,1)&&a.phase==WR_ON_ADMISSION_CAPTURED);
  if(fault==2||fault==6){
   assert(!wr_iot_on_generation_begin(&g,&a,&desired,1)&&!g.owner&&!a.busy);
   assert(wr_iot_on_admission_cancel(&a));assert(!unlink(profile_path));continue;
  }
  assert(wr_iot_on_generation_begin(&g,&a,&desired,1)&&a.busy);
  {struct wr_iot_precreated_profile_request unavailable={0};
   assert(wr_iot_generation_profile_request(&unavailable)==0);}
  assert(g.config_revision.present==record_present);
  copy=g;assert(!wr_iot_on_generation_step(&copy)&&!generator_calls);
  if(fault==3)strcpy(desired_record,"malformed");
  if(fault==3){assert(wr_iot_on_generation_step(&g)==-1&&!generator_calls);}
  else{
   assert(!wr_iot_on_generation_step(&g)&&generator_calls==1);
   if(fault==4)strcpy(desired_record,"malformed");
   if(fault==5)record_error=1;
   if(fault==4||fault==5)assert(wr_iot_on_generation_step(&g)==-1);
   else {
    assert(wr_iot_on_generation_step(&g)==1&&g.phase==WR_ON_GEN_VERIFIED);
    if(fault==7){
     assert(!wr_iot_restart_profile_current(&desired)&&wr_iot_restart_profile_file_current(&desired));
     /* After Main may have started, desired preferences are a new revision.
      * The retained old-generation file proof must stay valid for shutdown.
      * This does not model the actual driver key/epoch admission. */
     g.main_may_have_started=1;
     strcpy(config.profile.ssid,"Next desired IoT");
     assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
     assert(!wr_iot_generation_config_current(&g.config_revision,g.config_revision.id,g.config_revision.created));
     assert(wr_iot_on_generation_profile_current(&g));
     assert(!wr_iot_on_generation_step(&g)&&generator_calls==1);
     strcpy(config.profile.password,"different-valid-key");
     assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
     assert(wr_iot_on_generation_profile_current(&g));
     record_error=1;assert(wr_iot_on_generation_profile_current(&g));record_error=0;
     make_profile(); /* Foreign/old credentials in the actual file refuse. */
     assert(!wr_iot_on_generation_profile_current(&g));
    }
    if(fault==8)assert(!g.desired.enabled&&!g.desired.ssid[0]&&
      !strcmp(g.provisioning.profile.ssid,"New desired IoT")&&g.provisioning.profile.password[0]);
   }
   {struct wr_iot_precreated_profile_request unavailable={0};
    assert(wr_iot_generation_profile_request(&unavailable)==0);}
  }
  record_error=0;
  /* Fixture teardown only. Production ownership stays retained until its
   * ordinary checked handoff/recovery cleanup; no arbitrary file rollback. */
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_generation_config_release(&g.config_revision));
  wr_iot_saved_wipe(&g.provisioning,sizeof(g.provisioning));
  assert(wr_iot_on_admission_cancel(&a)&&!depth&&!wr_iot_rc_shutdown.active);
  assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-config-revision-') as directory:
 root=Path(directory)
 (root/'rc.h').write_text('const char *nvram_safe_get(const char *);\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((here.parent/'band-steering/settings-snapshot.h').read_bytes())
 (root/'check.c').write_text(body)
 producer=ast.parse((here/'prepare-rc.py').read_text())
 include=next(ast.literal_eval(n.value) for n in producer.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='include' for t in n.targets) and isinstance(n.value,ast.Constant))
 start=include.index('__attribute__((weak))')
 weak=include[start:include.index('}',start)+1]
 (root/'weak.c').write_text('#include "generation-profile.h"\n'+weak)

 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
  '-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20',
  '-I'+directory,'-I'+str(here),str(root/'check.c'),str(root/'weak.c'),str(here.parent/'band-steering/settings-snapshot.c'),'-o',str(root/'check')],check=True)
 subprocess.run([str(root/'check'),directory],check=True,timeout=15)
print('PASS actual OFF-to-ON admission/generation/file journal + native desired capture: absent/match accepted, mismatch/malformed rejected, copied generation refused, changed/error revision restores owned baseline without repeated generator; DOWN/SDK/guard boundary actors, no radio acceptance')
