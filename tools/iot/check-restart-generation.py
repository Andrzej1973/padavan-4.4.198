#!/usr/bin/env python3
"""Actual retained generation/journal/restore/readback; SDK generator injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-profile.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets)).split('int main(int argc',1)[0]
body+=r'''
#include "restart-generation.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct wr_iot_rc_physical_resume origin;
static int main_down=1,generator_failure,generator_calls,origin_reads,fail_origin_at;
int wr_iot_restart_main_down(void){return main_down;}
int wr_iot_rc_physical_resume_read(struct wr_iot_rc_physical_resume*out){memset(out,0,sizeof(*out));if(++origin_reads==fail_origin_at)return 0;*out=origin;return 1;}
int wr_iot_rc_restart_generate(int disabled){assert(!disabled&&main_down&&guard);generator_calls++;if(generator_failure==2){assert(!unlink(profile_path)&&!mkfifo(profile_path,0600));return -1;}if(generator_failure){replace_file("partial\n",8);return -1;}make_profile();return 0;}
#include "restart-generation.c"
static void capture_baseline(char*out,size_t*size){make_profile();FILE*f=fopen(profile_path,"a");assert(f&&fputs("# baseline\n",f)>=0&&!fclose(f));f=fopen(profile_path,"r");assert(f);*size=fread(out,1,4096,f);assert(!fclose(f));}
static void restored(const char*bytes,size_t size){FILE*f=fopen(profile_path,"r");char now[4096];assert(f);size_t n=fread(now,1,sizeof(now),f);assert(!fclose(f)&&n==size&&!memcmp(bytes,now,n));}
int main(int argc,char**argv){
 assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 origin=(struct wr_iot_rc_physical_resume){.intent={1,1,1},.physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}},.resume_needed=1,.desired={.enabled=1,.ssid="IoT",.password="iot-password"}};
 wr_iot_rc_shutdown.active=1;
 for(int fault=0;fault<6;fault++){
  struct wr_iot_restart_generation s={0};char before[4096];size_t n;
  generator_calls=0;generator_failure=fault==5?2:fault==1;origin_reads=fail_origin_at=0;origin.intent.reload=fault==2?0:1;
  capture_baseline(before,&n);assert(check(&origin.desired));assert(wr_iot_restart_generation_begin(&s)&&s.profile.active);
  assert(!wr_iot_restart_generation_begin(&s));main_down=0;assert(!wr_iot_restart_generation_step(&s)&&!generator_calls&&s.profile.active);main_down=1;
  origin.physical.attempt++;assert(!wr_iot_restart_generation_step(&s)&&!generator_calls);origin.physical.attempt--;
  s.busy=1;assert(!wr_iot_restart_generation_step(&s)&&!generator_calls);s.busy=0;
  if(fault==4)wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_restart_generation_step(&s));
  assert(generator_calls==(fault==2||fault==4?0:1));
  if(fault==3||fault==5){
   if(fault==5)assert(s.profile.files.pending&&s.phase==WR_RESTART_GEN_RECOVERING);
   if(fault==3){char foreign[1100];snprintf(foreign,sizeof(foreign),"%s/foreign",argv[1]);FILE*f=fopen(foreign,"w");assert(f&&fputs("new writer\n",f)>=0&&!fclose(f)&&!rename(foreign,profile_path));}
   assert(!wr_iot_restart_generation_step(&s)&&s.phase==WR_RESTART_GEN_RECOVERING);
   assert(!wr_iot_restart_generation_step(&s)&&s.profile.active&&generator_calls==1);
   /* Fixture teardown frees only captured RAM after proving retention; it
    * does not restore the foreign file or model production permission. */
   wr_iot_bundle_release(&s.profile.files);assert(!unlink(profile_path));continue;
  }
  if(fault==0||fault==2){
   assert(wr_iot_restart_generation_step(&s)&&s.phase==WR_RESTART_GEN_VERIFIED&&s.profile.active);
   assert(wr_iot_restart_generation_step(&s)&&generator_calls==(fault==2?0:1));
   assert(wr_iot_restart_generation_abort(&s));
  }
  for(unsigned i=0;i<4&&s.phase!=WR_RESTART_GEN_ROLLED_BACK;i++)assert(!wr_iot_restart_generation_step(&s));
  assert(s.phase==WR_RESTART_GEN_ROLLED_BACK&&!s.profile.active&&!s.profile.files.count&&!s.origin.desired.password[0]);
  restored(before,n);assert(generator_calls==(fault==2||fault==4?0:1));
  assert(!wr_iot_restart_generation_step(&s));wr_iot_rc_shutdown.pending=0;assert(!unlink(profile_path));
 }
 struct wr_iot_restart_generation cancelled={0};make_profile();origin_reads=0;fail_origin_at=3;
 assert(!wr_iot_restart_generation_begin(&cancelled)&&cancelled.phase==WR_RESTART_GEN_ROLLED_BACK&&!cancelled.profile.active);
 assert(!unlink(profile_path));
 puts("PASS actual restart generation/profile journal: one generator call, no-reload skip, exact RELEASE/Main-DOWN gating, valid profile readback retains baseline, partial failure restores bytes, foreign inode/pending journal refuse overwrite or replay, pending shutdown cleanup, post-capture read-only cancellation; SDK/physical/Main state injected, no Main UP");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restart-generation-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 unit=root/'check.c';unit.write_text(body);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary),d],check=True,timeout=15)
