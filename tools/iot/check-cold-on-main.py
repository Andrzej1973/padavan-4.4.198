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
static int idle_fault,idle_reads,up_calls,up_result;static unsigned long long idle_serial;
int wr_iot_driver_initial_idle_read(const unsigned char*id,struct wr_iot_idle_result*out){
 assert(depth&&id[0]==1);idle_reads++;
 *out=(struct wr_iot_idle_result){5,2,++idle_serial};
 if(idle_fault==1)out->epoch=4;
 if(idle_fault==2)out->generation=3;
 if(idle_fault==3&&idle_reads==2)out->epoch++;
 if(idle_fault==4)out->serial=1;
 if(idle_fault==5)wr_iot_rc_shutdown.pending=SIGTERM;
 return idle_fault!=6;
}
#include "restart-main-up.h"
enum wr_iot_restart_up_result wr_iot_restart_main_up(void){assert(down);up_calls++;down=0;return up_result;}
#include "cold-on-generation.c"
#include "cold-on-main.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<=8;fault++){
  struct wr_iot_cold_admission a={0};struct wr_iot_cold_generation g={0};struct wr_iot_cold_main m={0};
  down=1;partial=0;generator_calls=up_calls=idle_reads=0;idle_serial=0;make_profile();
  assert(wr_iot_cold_admission_begin(&a,nonce)&&a.phase==WR_COLD_CAPTURED);
  assert(wr_iot_cold_generation_begin(&g,&a,&desired,1));
  assert(!wr_iot_cold_generation_step(&g)&&wr_iot_cold_generation_step(&g)==1);
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_cold_main_begin(&m,&g)&&!up_calls&&!m.owner);
  wr_iot_rc_shutdown.pending=0;
  up_result=fault==7?WR_RESTART_UP_NOT_SUBMITTED:fault==8?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_RETURNED;
  assert(wr_iot_cold_main_begin(&m,&g)==(up_result==WR_RESTART_UP_RETURNED));
  assert(up_calls==1&&g.main_may_have_started&&!wr_iot_cold_main_begin(&m,&g));
  assert(!wr_iot_cold_generation_recover(&g));
  idle_fault=fault<=6?fault:0;
  assert(wr_iot_cold_main_step(&m)==(fault==0||fault==8));
  if(fault==7)assert(!idle_reads);
  if(!fault){
   assert(m.identity.adapter_epoch==5&&m.identity.device_generation==2);
   idle_reads=0;assert(wr_iot_cold_main_step(&m));
   FILE*f=fopen(profile_path,"a");assert(f&&fputs("# foreign change\n",f)>=0&&!fclose(f));
   assert(!wr_iot_cold_main_step(&m)&&up_calls==1);
   g.phase=WR_COLD_GEN_RESTORED;assert(!wr_iot_cold_main_step(&m));
  }
  /* Fixture-only teardown: post-UP production retirement is not implemented. */
  wr_iot_rc_shutdown.pending=0;wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
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
print('PASS cold Main startup: one UP attempt, no old rollback, new READY/never-opened ra2 identity via two IDLE probes; drift/stale/timeout/pending/NOT_SUBMITTED retained')
