"""Read-only cold selection distinguishes absent proof from observed drift."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include "cold-on-select.h"
#include "rc-backend.h"
#include "physical-stop-wire.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,enters,leaves,guard_ok=1,mode_ok=1,router=1,radio=1,mode,mode_reads,main_down=1,policy=1,bridge,bss=1,dns,history,reads,fault;
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);enters++;if(!guard_ok)return 0;depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth==1);depth--;leaves++;}
int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request*r){memset(r,0,sizeof(*r));return history;}
int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode*r){assert(depth);mode_reads++;*r=(struct wr_iot_rc_mode){router,radio,mode};if(fault==9&&mode_reads==2)r->radio=0;return mode_ok;}
int wr_iot_request_initial_off_current(void){assert(depth);return policy;}
unsigned int if_nametoindex(const char*n){assert(depth&&!strcmp(n,"br-iot"));return bridge;}
int wr_iot_bss_is_down(void){assert(depth);return bss;}
int wr_iot_dns_activation_recovery_state(void){assert(depth);return dns;}
int wr_iot_restart_main_down(void){assert(depth);return main_down;}
int wr_iot_driver_initial_down_read(const unsigned char*n,struct wr_iot_down_result*out){
 assert(depth&&n[0]==1);reads++;*out=(struct wr_iot_down_result){4,2,7};
 if(fault==1)return 0;
 if(fault==2&&reads==2)return 0;
 if(reads==2){if(fault==3)out->epoch++;if(fault==4)out->generation++;if(fault==5)out->main_close_serial++;if(fault==6)history=1;if(fault==7)wr_iot_rc_shutdown.pending=SIGTERM;}
 if(fault==8)out->epoch=0;
 if(fault==10)policy=0;
 return 1;
}
#include "cold-on-select.c"
int main(void){
 unsigned char nonce[16]={1},zero[16]={0};struct wr_iot_down_result out;
 for(fault=0;fault<=10;fault++){
  reads=mode_reads=history=0;policy=1;memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));memset(&out,0x55,sizeof(out));
  enum wr_iot_cold_selection result=wr_iot_cold_select(nonce,&out);
  assert(result==(fault==0?WR_COLD_SELECT_ELIGIBLE:fault==1?WR_COLD_SELECT_NATIVE:WR_COLD_SELECT_REFUSED));
  assert(!depth&&enters==leaves);
  if(!fault)assert(reads==2&&out.epoch==4&&out.generation==2&&out.main_close_serial==7);
  else assert(!out.epoch&&!out.generation&&!out.main_close_serial);
 }
 fault=0;policy=1;history=0;memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));reads=mode_reads=0;
 main_down=0;assert(wr_iot_cold_select(nonce,&out)==WR_COLD_SELECT_NATIVE&&!reads);main_down=1;
 router=0;assert(wr_iot_cold_select(nonce,&out)==WR_COLD_SELECT_NATIVE&&!reads);router=1;
 mode_ok=0;assert(wr_iot_cold_select(nonce,&out)==WR_COLD_SELECT_REFUSED&&!reads);mode_ok=1;
 for(int gate=0;gate<9;gate++){
  wr_iot_rc_shutdown.active=gate==0;wr_iot_rc_shutdown.pending=gate==1?SIGTERM:0;
  wr_iot_rc_shutdown.radio_off_owned=gate==2;wr_iot_rc_shutdown.radio_on_owned=gate==3;
  history=gate==4;policy=gate!=5;bridge=gate==6;bss=gate!=7;dns=gate==8;
  assert(wr_iot_cold_select(nonce,&out)==WR_COLD_SELECT_REFUSED&&!reads&&!depth&&!out.epoch);
 }
 memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));history=bridge=dns=0;policy=bss=1;
 int old_enters=enters;assert(wr_iot_cold_select(zero,&out)==WR_COLD_SELECT_REFUSED&&enters==old_enters);
 assert(wr_iot_cold_select(NULL,&out)==WR_COLD_SELECT_REFUSED&&enters==old_enters);
 assert(wr_iot_cold_select(nonce,NULL)==WR_COLD_SELECT_REFUSED&&enters==old_enters);
 guard_ok=0;assert(wr_iot_cold_select(nonce,&out)==WR_COLD_SELECT_REFUSED&&!depth&&!reads);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-select-') as d:
 p=Path(d)/'check.c';p.write_text(body);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS read-only cold selector: exact double DOWN tuple, absent first proof/Main-UP preserves native guard, partial proof/drift/mode/policy/history/pending refuses, zero failure output and balanced guard; transport/policy actors, no admission or restart')
