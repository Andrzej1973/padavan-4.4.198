from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "rc-backend.h"
#include "radio-off-current.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,guard=1,closed=1,down=1,reads,drift;
static unsigned index_reads;
int wr_iot_service_guard_enter(int on){assert(on==1&&!depth);if(!guard)return 0;depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth==1);depth--;}
unsigned if_nametoindex(const char*n){assert(depth&&!strcmp(n,"ra0"));index_reads++;return drift==5&&index_reads==2?8:7;}
int wr_iot_restart_main_down(void){assert(depth);return down;}
int wr_iot_rc_backend_closed(struct wr_iot_driver_closed_result*c){
 assert(depth);reads++;*c=(struct wr_iot_driver_closed_result){1,2,3,4};
 if(reads==2){if(drift==1)c->adapter_epoch++;if(drift==2)c->device_generation++;if(drift==3)c->open_token++;if(drift==4)c->close_serial++;if(drift==6)wr_iot_rc_shutdown.pending=SIGTERM;}
 return closed;
}
#include "radio-off-current.c"
int main(void){
 struct wr_iot_physical_stop_request r={WR_STOP_RELEASE,1,2,3,4,5,{1}};
 assert(!wr_iot_radio_off_current(&r));wr_iot_rc_shutdown.radio_off_owned=1;
 for(int fault=0;fault<=6;fault++){
  drift=fault;reads=index_reads=0;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_radio_off_current(&r)==!fault&&!depth);
 }
 drift=0;wr_iot_rc_shutdown.pending=0;
 guard=0;assert(!wr_iot_radio_off_current(&r)&&!depth);guard=1;
 down=0;assert(!wr_iot_radio_off_current(&r)&&!depth);down=1;
 closed=0;assert(!wr_iot_radio_off_current(&r)&&!depth);closed=1;
 r.action=WR_STOP_QUERY;assert(!wr_iot_radio_off_current(&r));r.action=WR_STOP_RELEASE;
 wr_iot_rc_shutdown.active=1;assert(!wr_iot_radio_off_current(&r));
 assert(!wr_iot_radio_off_current(0));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-current-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS OFF current observer: exact RELEASE tuple, fresh CLOSED/Main DOWN, ifindex and pending drift, guard/owner/admission refusal; backend/interface actors injected, unbound')
