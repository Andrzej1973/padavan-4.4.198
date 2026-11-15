"""Actual disabled profile generation under existing OFF receipt admission."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-generation.py')}
exec((here/'check-radio-on-generation.py').read_text().split('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int reload=0;reload<=1;reload++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_generation g={0};struct wr_iot_request off={0};
  make_profile();generator_calls=0;assert(wr_iot_on_admission_begin_reload(&a,reload));
  struct wr_iot_request wrong=off;strcpy(wrong.ssid,"forbidden");assert(!wr_iot_on_generation_begin(&g,&a,&wrong,reload));
  assert(wr_iot_on_generation_begin(&g,&a,&off,reload));
  assert(!wr_iot_on_generation_step(&g)&&wr_iot_on_generation_step(&g)==1);
  assert(generator_calls==reload&&!g.main_may_have_started&&g.desired.enabled==0);
  strcpy(saved_enabled,"1");assert(!wr_iot_on_generation_step(&g));strcpy(saved_enabled,"0");
  assert(wr_iot_on_generation_recover(&g)==-1);
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_on_admission_cancel(&a)&&!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-generation-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS disabled generation: reload0/1, no credential-bearing OFF request, saved ON drift refuses, rollback retained, no Main UP; SDK actors')
