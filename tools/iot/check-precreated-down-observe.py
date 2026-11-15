"""Actual RC double DOWN observation; external read-only adapters injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <string.h>
#include "precreated-down-observe.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guard=1,policy=1,bridge,bss=1,dns,main_down=1,reads,fault;
int wr_iot_service_guard_dup(void){return guard?open("/dev/null",O_RDONLY):-1;}
int wr_iot_request_initial_off_current(void){return policy;}
unsigned int if_nametoindex(const char*n){assert(!strcmp(n,"br-iot"));return bridge;}
int wr_iot_bss_is_down(void){return bss;}
int wr_iot_dns_activation_recovery_state(void){return dns;}
int wr_iot_restart_main_down(void){return main_down;}
int wr_iot_driver_initial_down_read(const unsigned char*n,struct wr_iot_down_result*out){
 assert(n&&n[0]==1);reads++;*out=(struct wr_iot_down_result){4,2,7};
 if(reads==2){if(fault==1)out->epoch++;if(fault==2)out->generation++;if(fault==3)out->main_close_serial++;if(fault==4)wr_iot_rc_shutdown.pending=SIGTERM;if(fault==6)out->epoch=0;if(fault==7)out->generation=0;if(fault==8)out->main_close_serial=0;}
 return fault!=5;
}
#include "precreated-down-observe.c"
int main(void){unsigned char nonce[16]={1};struct wr_iot_down_result out;
 wr_iot_rc_shutdown.active=1;
 for(fault=0;fault<=8;fault++){
  reads=0;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_initial_down_observe(nonce,&out)==!fault);
  if(fault)assert(!out.epoch&&!out.generation&&!out.main_close_serial);
  else assert(reads==2&&out.main_close_serial==7);
 }
 fault=0;wr_iot_rc_shutdown.pending=0;
 reads=0;wr_iot_rc_shutdown.active=0;
 assert(!wr_iot_initial_down_observe(nonce,&out)&&!reads&&!out.epoch);
 wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_initial_down_observe(nonce,&out)&&!reads);
 wr_iot_rc_shutdown.pending=0;
 assert(!wr_iot_initial_down_observe(nonce,0)&&!reads);
 for(int gate=0;gate<6;gate++){
  reads=0;guard=gate!=0;policy=gate!=1;bridge=gate==2;bss=gate!=3;dns=gate==4;main_down=gate!=5;
  assert(!wr_iot_initial_down_observe(nonce,&out)&&!reads&&!out.epoch);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-down-observe-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS RC double DOWN observation: exact epoch/generation/Main serial, pending/read failure clears output; guard/policy/bridge/BSS/DNS/Main gates precede transport; no mutation or restart')
