"""Read-only INITIAL restart selection; driver/software state actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include "initial-restart-select.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int held,guard_ok=1,idle=1,policy=1,bridge,bss=1,dns,reads,fault,mode_reads;
int wr_iot_service_guard_enter(int on){assert(on==1&&!held);if(!guard_ok)return 0;held=1;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&held);held=0;}
int wr_iot_service_guard_dup(void){assert(held);return open("/dev/null",O_RDONLY);}
int wr_iot_rc_boot_idle(void){return idle;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode *m){assert(held);mode_reads++;*m=(struct wr_iot_rc_mode){1,1,0};if(fault==1)m->radio=0;if(fault==2&&mode_reads==2)m->mode=1;return fault!=3;}
int wr_iot_request_initial_off_current(void){assert(held);return policy;}
unsigned if_nametoindex(const char *name){assert(held&&!strcmp(name,"br-iot"));return bridge;}
int wr_iot_bss_is_down(void){assert(held);return bss;}
int wr_iot_dns_activation_recovery_state(void){assert(held);return dns;}
int wr_iot_driver_initial_idle_read(const unsigned char *n,struct wr_iot_idle_result *out){assert(held&&n[0]==7);reads++;*out=(struct wr_iot_idle_result){2,3,(unsigned long long)reads};if(fault==4)return 0;if(fault==5&&reads==2)out->epoch++;if(fault==6)out->serial=1;if(fault==7&&reads==2)wr_iot_rc_shutdown.pending=SIGTERM;if(fault==8&&reads==2)idle=0;return 1;}
int main(void){
 unsigned char nonce[16]={7};struct wr_iot_idle_result out={0};
 for(int scenario=0;scenario<15;scenario++){
  fault=0;guard_ok=idle=policy=bss=1;bridge=dns=reads=mode_reads=0;memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));
  if(scenario<=8)fault=scenario;
  if(scenario==9)guard_ok=0;
  if(scenario==10)policy=0;
  if(scenario==11)bridge=1;
  if(scenario==12)bss=0;
  if(scenario==13)dns=1;
  if(scenario==14)idle=0;
  memset(&out,0xa5,sizeof(out));int result=wr_iot_initial_restart_select(nonce,&out);assert(!held);
  if(!scenario)assert(result==WR_INITIAL_SELECT_ELIGIBLE&&out.epoch==2&&out.generation==3&&out.serial==2);
  else{assert(result==(scenario==1?WR_INITIAL_SELECT_NATIVE:WR_INITIAL_SELECT_REFUSED));struct wr_iot_idle_result zero={0};assert(!memcmp(&zero,&out,sizeof(out)));}
 }
 fault=0;guard_ok=idle=policy=bss=1;bridge=dns=reads=mode_reads=0;
 memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));
 assert(wr_iot_initial_restart_select(nonce,&out)==WR_INITIAL_SELECT_ELIGIBLE);
 held=1;wr_iot_rc_shutdown.active=1;
 assert(wr_iot_initial_restart_selected_current(nonce,&out));
 struct wr_iot_idle_result wrong=out;wrong.epoch++;
 assert(!wr_iot_initial_restart_selected_current(nonce,&wrong));
 wrong=out;wrong.generation++;assert(!wr_iot_initial_restart_selected_current(nonce,&wrong));
 wrong=out;wrong.serial=~0ULL;assert(!wr_iot_initial_restart_selected_current(nonce,&wrong));
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_initial_restart_selected_current(nonce,&out));
 wr_iot_rc_shutdown.pending=0;idle=0;assert(!wr_iot_initial_restart_selected_current(nonce,&out));
 idle=1;assert(wr_iot_initial_restart_selected_current(nonce,&out));held=0;

}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-select-') as d:
 p=Path(d)/'test.c';p.write_text(body);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'initial-restart-select.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=10)
print('PASS INITIAL read-only selector: fresh double idle, mode drift, stale/failed proof, pending shutdown, ownership/policy/bridge/BSS/DNS refusal; no ARM/OPEN or SDK fallback permission')
