"""A restored generation is cancellation, never readiness for RAM ON."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-restore.py').read_text();ns={'__file__':str(here/'check-radio-on-restore.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_on_admission a={0};struct wr_iot_on_restore restore={0};unsigned char id[16]={1};
 make_profile();partial=1;assert(wr_iot_on_admission_begin(&a));
 assert(wr_iot_on_restore_begin(&restore,&a,&desired,1,id));
 for(int tick=0;tick<6;tick++)assert(!wr_iot_on_restore_step(&restore));
 assert(restore.generation.phase==WR_ON_GEN_RESTORED&&!ram_calls&&!ups&&!restore.main.owner);
 wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
 assert(wr_iot_on_admission_cancel(&a)&&!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-restored-result-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS restored generation never enables RAM ON or starts Main; actual restore composition, SDK actors')
