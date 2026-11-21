from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-profile.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets)).split('int main(int argc',1)[0]
body+=r'''
#include "radio-off-profile.h"
static int depth,observed=1,generator_calls,partial;
int wr_iot_service_guard_enter(int on){assert(on==1&&!depth);if(!guard)return 0;depth=1;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth=0;}
int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request*r){assert(depth&&r->action==WR_STOP_RELEASE);return observed;}
int wr_iot_rc_restart_generate(int arg){assert(depth&&!arg);generator_calls++;if(partial){replace_file("partial\n",8);return partial==2?0:-1;}make_profile();return 0;}
#include "radio-off-profile-check.c"
#include "radio-off-profile.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<5;fault++){
  struct wr_iot_radio_off_owner off={.owner=getpid(),.result=1,.policy_ready=1,.policy={.reload=fault!=0},.released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
  struct wr_iot_off_profile s={0};generator_calls=0;partial=fault==4?2:fault>=2;
  make_profile();FILE*f=fopen(profile_path,"a");assert(f&&fputs("# baseline\n",f)>=0&&!fclose(f));
  char before[4096];f=fopen(profile_path,"r");assert(f);size_t n=fread(before,1,sizeof(before),f);assert(!fclose(f));
  struct stat st;assert(!stat(profile_path,&st));
  assert(wr_iot_off_profile_begin(&s,&off)&&s.baseline.active&&!depth);
  assert(!wr_iot_off_profile_begin(&s,&off));
  /* A copied owner must not enter the generator or touch shared journal data. */
  struct wr_iot_off_profile copied=s;
  assert(!wr_iot_off_profile_step(&copied)&&!generator_calls&&!depth);
  assert(s.phase==WR_OFF_PROFILE_CAPTURED&&s.self==&s);
  observed=0;assert(!wr_iot_off_profile_step(&s)&&!generator_calls&&!depth);observed=1;
  assert(!wr_iot_off_profile_step(&s));
  assert(generator_calls==(fault!=0));
  if(fault<2){
   assert(wr_iot_off_profile_step(&s)==1&&s.phase==WR_OFF_PROFILE_VERIFIED&&s.baseline.active);
   assert(wr_iot_off_profile_step(&s)==1&&generator_calls==(fault!=0));
   if(!fault){struct stat after;assert(!stat(profile_path,&after)&&st.st_ino==after.st_ino&&st.st_mtime==after.st_mtime&&st.st_ctime==after.st_ctime);}
  }else{
   if(fault==4){assert(s.phase==WR_OFF_PROFILE_GENERATED);assert(!wr_iot_off_profile_step(&s));}
   assert(s.phase==WR_OFF_PROFILE_RESTORING);
   if(fault==3){char path[1100];snprintf(path,sizeof(path),"%s/foreign",argv[1]);f=fopen(path,"w");assert(f&&fputs("foreign\n",f)>=0&&!fclose(f)&&!rename(path,profile_path));assert(!wr_iot_off_profile_step(&s)&&s.baseline.active);}
   else{assert(wr_iot_off_profile_step(&s)==-1&&s.phase==WR_OFF_PROFILE_RESTORED);char now[4096];f=fopen(profile_path,"r");assert(f);size_t size=fread(now,1,sizeof(now),f);assert(!fclose(f)&&size==n&&!memcmp(before,now,n));}
   assert(generator_calls==1);
  }
  /* Fixture-only free of retained RAM after checking non-retirement. */
  wr_iot_bundle_release(&s.baseline.files);assert(!unlink(profile_path));
 }
 /* A versioned desired generation can differ from unchanged legacy keys.
  * File provenance succeeds; the current OFF observer still refuses it.
  * This records the unbound handoff, not a loaded-PMK or device receipt. */
 struct wr_iot_request next={.enabled=1,.ssid="IoT-next",.password="next-password"};
 FILE *in=tmpfile(),*out=fopen(profile_path,"w");assert(in&&out);
 assert(fputs(baseline,in)>=0);rewind(in);
 assert(wr_iot_precreated_profile(in,out,next.ssid,next.password,0));
 assert(!fclose(in)&&!fclose(out));
 assert(wr_iot_restart_profile_file_current(&next));
 assert(!strcmp(saved_ssid,"IoT")&&!strcmp(saved_password,"iot-password"));
 assert(!wr_iot_rc_off_profile_current());
 assert(wr_iot_restart_profile_file_current(&next));
 assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-profile-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS OFF profile actual snapshot/journal: copied owner refused, reload0 no generation/inode writes, generate once, retained verified baseline, partial restores bytes, foreign inode retained/no replay; SDK and DOWN actors injected, unbound')

print('PASS source-gap reproduction: new desired file valid; unchanged legacy OFF observer refuses; loaded handoff remains unbound')
