"""Actual disabled profile generation under existing OFF receipt admission."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-main.py')}
exec((here/'check-radio-on-main.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_on_admission a={0};struct wr_iot_on_generation g={0};struct wr_iot_on_main m={0};
 struct wr_iot_request off={0};unsigned char id[16]={1};
 make_profile();membership=1;up_result=WR_RESTART_UP_RETURNED;
 assert(wr_iot_on_admission_begin_reload(&a,1));assert(wr_iot_on_generation_begin(&g,&a,&off,1));
 assert(!wr_iot_on_generation_step(&g)&&wr_iot_on_generation_step(&g)==1);
 assert(wr_iot_on_main_begin(&m,&g,id)&&ups==1);
 assert(wr_iot_on_main_lan_step(&m)&&attaches==1&&g.desired.enabled==0);
 strcpy(saved_enabled,"1");assert(!wr_iot_on_main_lan_step(&m)&&ups==1&&attaches==1);strcpy(saved_enabled,"0");
 assert(wr_iot_on_main_lan_step(&m)&&ups==1&&attaches==1);
 wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
 assert(wr_iot_on_admission_cancel(&a)&&!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-generation-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual disabled-profile Main/LAN: one UP/attach, saved ON drift blocks readiness, no ra2 OPEN submitted; SDK identity/transport actors, terminal cleanup separate')
