"""Actual snapshot/generator journal/scanner/restore under private ON admission."""
from pathlib import Path
import ast, subprocess, tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-profile.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets)).split('int main(int argc',1)[0]
body+=r'''
#include "radio-on-generation.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,down=1,generator_calls,partial;
static struct wr_iot_request desired={.enabled=1,.ssid="IoT",.password="iot-password"};
static struct wr_iot_physical_stop_request receipt={WR_STOP_RELEASE,1,2,3,4,5,{1}};
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request *r){*r=receipt;return 1;}
int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode *m){m->router=m->radio=1;m->mode=0;return 1;}
int wr_iot_radio_resume_down_observed(const struct wr_iot_physical_stop_request*r){assert(depth&&wr_iot_rc_shutdown.active&&r->action==WR_STOP_RELEASE);return down;}
int wr_iot_rc_off_profile_current(void){return wr_iot_restart_profile_current(&desired);}
int wr_iot_rc_restart_generate(int arg){assert(depth&&!arg);generator_calls++;if(partial){replace_file("partial\n",8);return partial==2?0:-1;}make_profile();return 0;}
#include "radio-on-admission.c"
#include "radio-stop-fence.c"
#include "radio-on-generation.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<6;fault++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_generation g={0};
  generator_calls=0;partial=fault==2?1:fault==3?2:0;make_profile();
  FILE*f=fopen(profile_path,"a");assert(f&&fputs("# baseline\n",f)>=0&&!fclose(f));
  assert(wr_iot_on_admission_begin(&a)&&a.phase==WR_ON_ADMISSION_CAPTURED);
  struct wr_iot_request wrong=desired;strcpy(wrong.ssid,"foreign");
  assert(!wr_iot_on_generation_begin(&g,&a,&wrong,1)&&!a.busy&&!g.owner&&!g.admission);
  for(size_t i=0;i<sizeof(g.desired);i++)assert(!((unsigned char*)&g.desired)[i]);
  assert(wr_iot_on_generation_begin(&g,&a,&desired,fault!=0)&&a.busy);
  assert(!wr_iot_on_admission_cancel(&a)&&!wr_iot_on_generation_begin(&g,&a,&desired,1));
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_on_generation_step(&g)&&!generator_calls&&g.phase==WR_ON_GEN_CAPTURED&&a.busy);
  wr_iot_rc_shutdown.pending=0; /* Fixture only: pending shutdown retains context. */
  down=0;assert(!wr_iot_on_generation_step(&g)&&!generator_calls);down=1;
  assert(!wr_iot_on_generation_step(&g)&&generator_calls==(fault!=0));
  if(fault==4){char foreign[1100];snprintf(foreign,sizeof(foreign),"%s/foreign",argv[1]);f=fopen(foreign,"w");assert(f&&fputs("foreign\n",f)>=0&&!fclose(f)&&!rename(foreign,profile_path));}
  if(fault>=2&&fault<=4){
   if(fault!=2)assert(!wr_iot_on_generation_step(&g));
   assert(g.phase==WR_ON_GEN_RESTORING);
   int result=wr_iot_on_generation_step(&g);assert(result==(fault==4?0:-1));
   if(fault!=4){char bytes[4096];f=fopen(profile_path,"r");assert(f);size_t n=fread(bytes,1,sizeof(bytes)-1,f);bytes[n]=0;assert(!fclose(f)&&strstr(bytes,"# baseline\n"));assert(wr_iot_on_generation_step(&g)==-1);}
  }else{
   assert(wr_iot_on_generation_step(&g)==1&&g.phase==WR_ON_GEN_VERIFIED);
   assert(wr_iot_on_generation_step(&g)==1&&generator_calls==(fault!=0));
   if(fault==5){assert(wr_iot_on_generation_abort(&g));assert(wr_iot_on_generation_step(&g)==-1);}
  }
  assert(generator_calls==(fault!=0)&&!wr_iot_on_admission_cancel(&a));
  /* Fixture teardown of retained state; production retirement is not bound. */
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_on_admission_cancel(&a)&&!depth&&!wr_iot_rc_shutdown.active);
  assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-generation-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON generation actual admission/snapshot/journal/scanner: reload0 no generator, reload1 once, partial/invalid output restores baseline, foreign inode retained, abort restores, no capture cancellation during generation; no Main UP/RC binding')
