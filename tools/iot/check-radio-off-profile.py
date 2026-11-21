from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-profile.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets)).split('int main(int argc',1)[0]
body+=r'''
#include "radio-off-profile.h"
static int depth,observed=1,generator_calls,partial;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
static int revision_current=1,capture_ok=1,enter_calls,leave_calls;
static const struct wr_iot_generation_config *bound_revision;
static char capture_record[WR_IOT_SAVED_CONFIG_MAX];
int wr_iot_generation_config_capture(struct wr_iot_generation_config *p,const char *id,
 unsigned long long created,struct wr_iot_saved_config *out){
 assert(depth&&p&&!p->owner&&!p->self&&out&&id&&created);
 if(!capture_ok)return 0;
 p->owner=getpid();p->self=(uintptr_t)p;p->created=created;
 memcpy(p->id,id,sizeof(p->id));
 if(capture_record[0]){p->present=1;memcpy(p->record,capture_record,sizeof(p->record));}
 return 1;
}
int wr_iot_generation_config_owned(const struct wr_iot_generation_config *p){
 return p&&p->owner==getpid()&&p->self==(uintptr_t)p&&p->created;
}
int wr_iot_generation_config_release(struct wr_iot_generation_config *p){
 assert(p&&p->owner==getpid()&&p->self==(uintptr_t)p&&bound_revision!=p);
 memset(p,0,sizeof(*p));return 1;
}
int wr_iot_generation_profile_enter(const struct wr_iot_generation_config *p){
 assert(depth&&!bound_revision);enter_calls++;
 if(!revision_current)return 0;
 assert(p->owner==getpid()&&p->self==(uintptr_t)p);bound_revision=p;return 1;
}
int wr_iot_generation_profile_leave(const struct wr_iot_generation_config *p){
 assert(depth&&bound_revision==p);leave_calls++;bound_revision=NULL;return 1;
}
#endif

int wr_iot_service_guard_enter(int on){assert(on==1&&!depth);if(!guard)return 0;depth=1;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth=0;}
int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request*r){assert(depth&&r->action==WR_STOP_RELEASE);return observed;}
int wr_iot_rc_restart_generate(int arg){assert(depth&&!arg);generator_calls++;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
assert(bound_revision);
if(bound_revision->present){
 struct wr_iot_saved_config config={0};FILE *in=tmpfile(),*out=fopen(profile_path,"w");
 assert(in&&out&&wr_iot_saved_config_decode(&config,bound_revision->record,strlen(bound_revision->record)));
 assert(fputs(baseline,in)>=0);rewind(in);
 assert(wr_iot_precreated_profile(in,out,config.profile.ssid,config.profile.password,0));
 assert(!fclose(in)&&!fclose(out));wr_iot_saved_wipe(&config,sizeof(config));return 0;
}
#endif
if(partial){replace_file("partial\n",8);return partial==2?0:-1;}make_profile();return 0;}
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
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  if(!fault){
   off.profile_binding.kind=WR_PROFILE_BACKEND_ACTIVE;strcpy(off.profile_binding.id,"01000000000000000000000000000000");
   off.profile_binding.created=1;off.profile_binding.identity=(struct wr_iot_driver_identity){1,2};
   assert(!wr_iot_off_profile_begin(&s,&off)&&!s.baseline.active); /* Missing proof. */
   strcpy(off.profile_receipt.path,profile_path);off.profile_receipt.owner=getpid();off.profile_receipt.valid=1;
   assert(wr_iot_generated_capture(&off.profile_receipt.file,profile_path));
   off.profile_binding.identity.adapter_epoch++;assert(!wr_iot_off_profile_begin(&s,&off));off.profile_binding.identity.adapter_epoch--;
  }
#endif
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
  wr_iot_bundle_release(&s.baseline.files);
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  if(s.config_revision.owner)assert(wr_iot_generation_config_release(&s.config_revision));
  assert(!bound_revision);
#endif
assert(!unlink(profile_path));
 }
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 /* Failed capture cannot claim files; revision drift never reaches generator. */
 struct wr_iot_radio_off_owner off={.owner=getpid(),.result=1,.policy_ready=1,
  .policy={.reload=1},.released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
 struct wr_iot_off_profile s={0};make_profile();capture_ok=0;
 assert(!wr_iot_off_profile_begin(&s,&off)&&!s.owner&&!s.baseline.active&&!depth);
 capture_ok=1;assert(wr_iot_off_profile_begin(&s,&off));
 revision_current=0;int generated_before=generator_calls,entered_before=enter_calls,left_before=leave_calls;
 assert(!wr_iot_off_profile_step(&s)&&s.phase==WR_OFF_PROFILE_RESTORING);
 assert(generator_calls==generated_before&&enter_calls==entered_before+1&&leave_calls==left_before&&!bound_revision);
 assert(wr_iot_off_profile_step(&s)==-1);
 assert(wr_iot_off_profile_step(&s)==-1&&generator_calls==generated_before);
 wr_iot_bundle_release(&s.baseline.files);assert(wr_iot_generation_config_release(&s.config_revision));
 assert(!unlink(profile_path));revision_current=1;
 struct wr_iot_saved_config desired={.profile={.enabled=0,.ssid="IoT-B",.password="password-B",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.10",.last="192.168.50.30"}};
 assert(wr_iot_saved_config_encode(capture_record,sizeof(capture_record),&desired));
 memset(&s,0,sizeof(s));make_profile();partial=0;
 assert(wr_iot_off_profile_begin(&s,&off));
 assert(!wr_iot_off_profile_step(&s)&&s.phase==WR_OFF_PROFILE_GENERATED);
 assert(wr_iot_off_profile_step(&s)==1&&s.phase==WR_OFF_PROFILE_VERIFIED);
 assert(!wr_iot_rc_off_profile_current()); /* Legacy A is deliberately unchanged. */
 strcpy(desired.profile.ssid,"IoT-C");
 assert(wr_iot_saved_config_encode(capture_record,sizeof(capture_record),&desired));
 assert(wr_iot_off_profile_step(&s)==1); /* Later desired C cannot retarget B. */
 struct wr_iot_off_profile duplicate=s;assert(!wr_iot_off_profile_current(&duplicate));
 make_profile();assert(!wr_iot_off_profile_step(&s)); /* Foreign file no longer matches B. */
 wr_iot_bundle_release(&s.baseline.files);assert(wr_iot_generation_config_release(&s.config_revision));
 assert(!unlink(profile_path));memset(capture_record,0,sizeof(capture_record));
#endif
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
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 {struct wr_iot_radio_off_owner off={.owner=getpid(),.result=1,.policy_ready=1,.policy={.reload=0},
   .released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
  struct wr_iot_off_profile s={0};
  off.profile_binding.kind=WR_PROFILE_BACKEND_REBIND_ACTIVE;strcpy(off.profile_binding.id,"02000000000000000000000000000000");
  off.profile_binding.created=2;off.profile_binding.identity=(struct wr_iot_driver_identity){1,2};
  off.profile_receipt.valid=1;off.profile_receipt.owner=getpid();strcpy(off.profile_receipt.path,profile_path);
  assert(wr_iot_generated_capture(&off.profile_receipt.file,profile_path));
  int before=generator_calls;assert(wr_iot_off_profile_begin(&s,&off));
  assert(!wr_iot_off_profile_step(&s)&&wr_iot_off_profile_step(&s)==1&&generator_calls==before);
  assert(wr_iot_off_profile_current(&s)); /* Historical file, legacy A differs. */
  s.history_binding.identity.device_generation++;assert(!wr_iot_off_profile_current(&s));s.history_binding.identity.device_generation--;
  assert(wr_iot_off_profile_current(&s));
  FILE*f=fopen(profile_path,"a");assert(f&&fputs("# changed after capture\n",f)>=0&&!fclose(f));
  assert(!wr_iot_off_profile_current(&s));wr_iot_bundle_release(&s.baseline.files);
  /* Fixture restores original text only for the independent scanner check. */
  FILE *in=tmpfile(),*out=fopen(profile_path,"w");assert(in&&out&&fputs(baseline,in)>=0);rewind(in);
  assert(wr_iot_precreated_profile(in,out,next.ssid,next.password,0));assert(!fclose(in)&&!fclose(out));
 }
#endif
 assert(wr_iot_restart_profile_file_current(&next));
 assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-profile-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 for prepared in (0,1):
  subprocess.run(['gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(prepared),'-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
  subprocess.run([str(b),d],check=True,timeout=15)
print('PASS OFF profile actual snapshot/journal: copied owner refused, reload0 no generation/inode writes, generate once, retained verified baseline, partial restores bytes, foreign inode retained/no replay; SDK and DOWN actors injected, unbound')

print('PASS legacy scanner separation: historical file differs from saved keys; prepared reload0 uses frozen receipt, loaded-key evidence separate')

print('PASS OFF revision binding prepared0/1: capture/drift refuse generation; frozen reload0 missing/epoch/file proof refuses; no legacy fallback')

print('PASS owned OFF observer: generated disabled B accepted with unchanged legacy A; later desired C does not retarget B; copy and foreign file refused')
