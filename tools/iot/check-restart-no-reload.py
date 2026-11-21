"""Actual no-reload profile generation path, inode/content retained before UP."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-generation.py').read_text();ns={'__file__':str(here/'check-restart-generation.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<generation fixture>','exec'),ns)
code=ns['body'].split('int main(int argc',1)[0]+r'''
int main(int argc,char**argv){
 assert(argc==2);(void)check;(void)restored;
 snprintf(profile_path,sizeof(profile_path),"%s/RT2860AP.dat",argv[1]);make_profile();
 origin=(struct wr_iot_rc_physical_resume){.intent={1,1,0},.physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}},.resume_needed=1,.desired={.enabled=1,.ssid="IoT",.password="iot-password"}};
 struct stat before,after;char bytes[4096];size_t n;struct wr_iot_restart_generation g={0};
 capture_baseline(bytes,&n);assert(!stat(profile_path,&before));wr_iot_rc_shutdown.active=1;
 assert(wr_iot_restart_generation_begin(&g));assert(!wr_iot_restart_generation_step(&g));
 assert(g.phase==WR_RESTART_GEN_GENERATED&&!generator_calls);
 for(int i=0;i<3;i++)assert(wr_iot_restart_generation_step(&g)&&!generator_calls);
 assert(!stat(profile_path,&after));
 assert(before.st_dev==after.st_dev&&before.st_ino==after.st_ino&&before.st_size==after.st_size);
 assert(before.st_mtim.tv_sec==after.st_mtim.tv_sec&&before.st_mtim.tv_nsec==after.st_mtim.tv_nsec);
 assert(before.st_ctim.tv_sec==after.st_ctim.tv_sec&&before.st_ctim.tv_nsec==after.st_ctim.tv_nsec);
 restored(bytes,n);g.main_may_have_started=1;
 assert(!wr_iot_restart_generation_abort(&g)&&!wr_iot_restart_generation_step(&g)&&!generator_calls);
 /* Fixture-only teardown after proving retained ownership; no production cleanup modeled. */
 wr_iot_bundle_release(&g.profile.files);assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-no-reload-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'test.c';p.write_text(code);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual no-reload generation: zero generator calls, original bytes/device/inode/size/mtime/ctime unchanged through repeated verification, post-UP abort blocked; SDK/physical/Main actors injected')
