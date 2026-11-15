from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "physical-stop-client.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guard=1,depth,up,reads,drift,calls;
static enum wr_iot_physical_call_result outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;
int wr_iot_service_guard_enter(int on){assert(on==1&&!depth);if(!guard)return 0;depth=1;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth==1);depth=0;}
unsigned if_nametoindex(const char*n){assert(depth&&!strcmp(n,"ra0"));reads++;return drift==1&&reads==2?8:7;}
int wr_iot_restart_main_down(void){assert(depth);return !up;}
enum wr_iot_physical_call_result wr_iot_physical_stop_call(const struct wr_iot_physical_stop_request*q,struct wr_iot_physical_stop_response*r){
 assert(depth&&q->action==WR_STOP_QUERY&&q->attempt==5&&q->nonce[0]==1);calls++;
 r->identity=*q;r->status=WR_STOP_COMPLETE;
 switch(drift){case 2:r->identity.epoch++;break;case 3:r->identity.generation++;break;case 4:r->identity.open_token++;break;case 5:r->identity.closed_serial++;break;case 6:r->identity.attempt++;break;case 7:r->identity.nonce[0]++;break;case 8:r->status=WR_STOP_RUNNING;break;case 9:wr_iot_rc_shutdown.pending=SIGTERM;break;case 10:wr_iot_rc_shutdown.radio_off_owned=0;break;}
 return outcome;
}
#include "radio-off-observe.c"
int main(void){
 struct wr_iot_physical_stop_request r={WR_STOP_RELEASE,1,2,3,4,5,{1}},saved=r;
 assert(!wr_iot_radio_off_observed(&r)&&!calls);wr_iot_rc_shutdown.radio_off_owned=1;
 for(drift=0;drift<=10;drift++){
  reads=calls=0;wr_iot_rc_shutdown.pending=0;wr_iot_rc_shutdown.radio_off_owned=1;
  assert(wr_iot_radio_off_observed(&r)==!drift&&!depth&&calls==1&&!memcmp(&r,&saved,sizeof(r)));
 }
 drift=0;wr_iot_rc_shutdown.radio_off_owned=1;
 outcome=WR_PHYSICAL_CALL_UNCERTAIN;assert(!wr_iot_radio_off_observed(&r)&&!depth);
 outcome=WR_PHYSICAL_CALL_NOT_SUBMITTED;assert(!wr_iot_radio_off_observed(&r)&&!depth);outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;
 guard=0;assert(!wr_iot_radio_off_observed(&r));guard=1;
 up=1;int before=calls;assert(!wr_iot_radio_off_observed(&r)&&calls==before&&!depth);up=0;
 wr_iot_rc_shutdown.active=1;assert(!wr_iot_radio_off_observed(&r));wr_iot_rc_shutdown.active=0;
 r.action=WR_STOP_QUERY;assert(!wr_iot_radio_off_observed(&r));assert(!wr_iot_radio_off_observed(0));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-observe-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS RC OFF observation: QUERY only, exact COMPLETE tuple, uncertainty/stale/ifindex/pending/owner/Main drift refuses, guard balanced and input immutable; transport injected')
