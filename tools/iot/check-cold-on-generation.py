"""Actual snapshot/generator journal/scanner/restore under private ON admission."""
from pathlib import Path
import ast, subprocess, tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-profile.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets)).split('int main(int argc',1)[0]
body+=r'''
#include "cold-on-generation.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,down=1,generator_calls,partial;
static struct wr_iot_request desired={.enabled=1,.ssid="IoT",.password="iot-password"};
static unsigned char nonce[16]={1};
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request *r){memset(r,0,sizeof(*r));return 0;}
int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode *m){m->router=m->radio=1;m->mode=0;return 1;}
int wr_iot_request_initial_off_current(void){return 1;}
unsigned int if_nametoindex(const char*n){assert(!strcmp(n,"br-iot"));return 0;}
int wr_iot_bss_is_down(void){return down;}
int wr_iot_dns_activation_recovery_state(void){return 0;}
int wr_iot_restart_main_down(void){return down;}
int wr_iot_driver_initial_down_read(const unsigned char*n,struct wr_iot_down_result*r){assert(n&&n[0]==1);*r=(struct wr_iot_down_result){4,2,7};return down;}
#include "precreated-down-observe.c"
int wr_iot_rc_off_profile_current(void){return wr_iot_restart_profile_current(&desired);}
int wr_iot_rc_restart_generate(int arg){assert(depth&&!arg);generator_calls++;if(partial){replace_file("partial\n",8);return partial==2?0:-1;}make_profile();return 0;}
#include "cold-on-admission.c"
#include "radio-stop-fence.c"
#include "driver-api-client.h"
static int idle_delivery=1;static unsigned long long idle_serial;
int wr_iot_driver_initial_idle_read(const unsigned char*id,struct wr_iot_idle_result*out){
 assert(depth&&id[0]==1);if(!idle_delivery)return 0;
 *out=(struct wr_iot_idle_result){2,2,++idle_serial};return 1;
}
#include "check-generation-config-absent.h"
#include "cold-on-generation.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<7;fault++){
  struct wr_iot_cold_admission a={0};struct wr_iot_cold_generation g={0};
  generator_calls=0;partial=fault==2?1:fault==3?2:0;make_profile();
  FILE*f=fopen(profile_path,"a");assert(f&&fputs("# baseline\n",f)>=0&&!fclose(f));
  assert(wr_iot_cold_admission_begin(&a,nonce)&&a.phase==WR_COLD_CAPTURED);
  struct wr_iot_request malformed=desired;memset(malformed.gateway,'x',sizeof(malformed.gateway));
  assert(!wr_iot_cold_generation_begin(&g,&a,&malformed,1)&&!a.busy&&!g.owner);
  malformed=desired;malformed.enabled=0;malformed.ssid[0]=malformed.password[0]=0;strcpy(malformed.gateway,"192.168.30.1");
  assert(!wr_iot_cold_generation_begin(&g,&a,&malformed,1)&&!a.busy&&!g.owner);
  struct wr_iot_request wrong=desired;strcpy(wrong.ssid,"foreign");
  assert(!wr_iot_cold_generation_begin(&g,&a,&wrong,0)&&!a.busy&&!g.owner&&!g.admission);
  for(size_t i=0;i<sizeof(g.desired);i++)assert(!((unsigned char*)&g.desired)[i]);
  assert(wr_iot_cold_generation_begin(&g,&a,fault==6?&wrong:&desired,fault!=0)&&a.busy);
  assert(!wr_iot_cold_admission_cancel(&a)&&!wr_iot_cold_generation_begin(&g,&a,&desired,1));
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_cold_generation_step(&g)&&!generator_calls&&g.phase==WR_COLD_GEN_CAPTURED&&a.busy);
  wr_iot_rc_shutdown.pending=0; /* Fixture only: pending shutdown retains context. */
  down=0;assert(!wr_iot_cold_generation_step(&g)&&!generator_calls);down=1;
  assert(!wr_iot_cold_generation_step(&g)&&generator_calls==(fault!=0));
  if(fault==4){char foreign[1100];snprintf(foreign,sizeof(foreign),"%s/foreign",argv[1]);f=fopen(foreign,"w");assert(f&&fputs("foreign\n",f)>=0&&!fclose(f)&&!rename(foreign,profile_path));}
  if((fault>=2&&fault<=4)||fault==6){
   if(fault!=2)assert(!wr_iot_cold_generation_step(&g));
   assert(g.phase==WR_COLD_GEN_RESTORING);
   int result=wr_iot_cold_generation_step(&g);assert(result==(fault==4?0:-1));
   if(fault!=4){char bytes[4096];f=fopen(profile_path,"r");assert(f);size_t n=fread(bytes,1,sizeof(bytes)-1,f);bytes[n]=0;assert(!fclose(f)&&strstr(bytes,"# baseline\n"));assert(wr_iot_cold_generation_step(&g)==-1);}
  }else{
   assert(wr_iot_cold_generation_step(&g)==1&&g.phase==WR_COLD_GEN_VERIFIED);
   assert(wr_iot_cold_generation_step(&g)==1&&generator_calls==(fault!=0));
   if(fault==5){
    wr_iot_rc_shutdown.pending=SIGTERM;
    g.main_may_have_started=1;assert(!wr_iot_cold_generation_recover(&g));g.main_may_have_started=0;
    down=0;assert(!wr_iot_cold_generation_recover(&g));down=1;
    assert(!wr_iot_cold_generation_recover(&g)&&a.busy&&a.profile.active);
    wr_iot_rc_shutdown.pending=0;
    assert(wr_iot_cold_generation_recover(&g)==-1);
    assert(wr_iot_cold_generation_recover(&g)==-1&&generator_calls==1);
    wr_iot_rc_shutdown.pending=0;
   }
  }
  assert(generator_calls==(fault!=0)&&!wr_iot_cold_admission_cancel(&a));
  /* Fixture teardown of retained state; production retirement is not bound. */
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_cold_admission_cancel(&a)&&!depth&&!wr_iot_rc_shutdown.active);
  assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-generation-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS cold generation actual admission/snapshot/journal/scanner: reload0 no generator, reload1 once, partial/invalid output restores baseline, foreign inode retained, pre-UP restore and post-UP refusal, no capture cancellation during generation; no Main UP/RC binding')
