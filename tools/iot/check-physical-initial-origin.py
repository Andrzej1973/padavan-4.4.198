"""Actual initial idle probe and Main lifetime provenance; not physical ARM."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "physical-initial-record.h"
int main(void){
 struct wr_iot_radio_transition radio;struct wr_iot_interface_ref slots[3]={0};
 struct wr_iot_precreated_idle_probe probe={0};
 struct wr_iot_physical_stop_lifetime life={0};
 struct wr_iot_main_recovery_owner owner={0};
 struct wr_iot_physical_initial_origin origin={0};
 unsigned long sequence=0;int main_dev=0,iot_dev=0;
 wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
 struct wr_iot_interface_ref *main=wr_iot_registry_add_family(slots,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
 struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(slots,3,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
 main->published=iot->published=1;main->phase=WR_REF_OWNED;main->last_token=1;
 assert(!wr_iot_physical_initial_capture(&origin,&probe,&life,&radio,slots,3,&main_dev,&iot_dev,2,1));
 assert(wr_iot_precreated_idle_probe_begin(&probe,&radio,slots,3,&main_dev,&iot_dev,2,1));
 assert(wr_iot_precreated_idle_probe_finish(&probe,&radio,slots,3,1,1));
 assert(wr_iot_physical_stop_lifetime_begin_main(&life,&radio,&owner,main,&main_dev));
 main->last_token++;
 assert(!wr_iot_physical_initial_capture(&origin,&probe,&life,&radio,slots,3,&main_dev,&iot_dev,2,1));
 main->last_token--;
 assert(wr_iot_physical_initial_capture(&origin,&probe,&life,&radio,slots,3,&main_dev,&iot_dev,2,1));
 assert(!wr_iot_physical_initial_capture(&origin,&probe,&life,&radio,slots,3,&main_dev,&iot_dev,2,1));
 assert(wr_iot_physical_initial_history(&origin,iot));
 assert(wr_iot_physical_initial_main_binding(&origin,&life));
 struct wr_iot_physical_initial_record attempt={0};int task=0,other=0;
 struct wr_iot_physical_initial_request request={.action=WR_STOP_ARM,.epoch=origin.epoch,
  .generation=origin.generation,.idle_serial=origin.idle_serial,.nonce={7}};
 unsigned char wire[64];struct wr_iot_physical_initial_response response={0};
 assert(wr_iot_physical_initial_record_arm(&attempt,&request,&task,&origin,&life,iot));
 assert(!wr_iot_physical_initial_record_arm(&attempt,&request,&task,&origin,&life,iot));
 assert(wr_iot_physical_initial_record_reply(&attempt,&request,&task,wire,64));
 assert(wr_iot_physical_initial_decode(&response,wire,64,1)&&response.status==WR_STOP_ARMED);
 assert(!wr_iot_physical_initial_record_reply(&attempt,&request,&other,wire,64));
 request.action=WR_STOP_QUERY;request.attempt=attempt.serial+1;
 assert(!wr_iot_physical_initial_record_reply(&attempt,&request,&task,wire,64));
 request.attempt=attempt.serial;
 assert(!wr_iot_physical_initial_record_running(&attempt,&request,&task,&life));
 assert(wr_iot_physical_initial_cancel_current(&origin,&life,&probe,&owner,&radio,slots,3,1));
 {struct wr_iot_main_recovery_owner busy=owner;busy.deferred_owners=1;
  assert(!wr_iot_physical_initial_cancel_current(&origin,&life,&probe,&busy,&radio,slots,3,1));}
 {struct wr_iot_radio_transition busy=radio;busy.active_tx=1;
  assert(!wr_iot_physical_initial_cancel_current(&origin,&life,&probe,&owner,&busy,slots,3,1));}
 struct wr_iot_radio_ticket ticket,captured={0};
 assert(!wr_iot_physical_initial_main_released(&origin,&life,&owner,&radio,main,iot,1));
 assert(wr_iot_radio_begin_main_stop(&radio,1,&ticket));
 assert(!wr_iot_physical_initial_cancel_current(&origin,&life,&probe,&owner,&radio,slots,3,1));
 assert(wr_iot_ref_begin_close(main,&main_dev,main->generation,main->last_token));
 assert(wr_iot_main_close_claim_preclose(&radio,main,slots,3,&ticket,1));
 assert(wr_iot_main_close_claim_void_preclose(main,&ticket));
 assert(wr_iot_main_close_finish_preclose(main,&ticket));
 assert(wr_iot_main_recovery_queue_close(&owner,&radio,main,slots,3,&ticket,1,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_physical_stop_lifetime_capture_main(&life,life.serial,&owner,&radio,main,&captured));
 assert(wr_iot_physical_initial_record_running(&attempt,&request,&task,&life));
 assert(!wr_iot_physical_initial_record_running(&attempt,&request,&task,&life));
 assert(wr_iot_physical_initial_record_reply(&attempt,&request,&task,wire,64));
 assert(wr_iot_physical_initial_decode(&response,wire,64,1)&&response.status==WR_STOP_RUNNING);
 request.action=WR_STOP_RELEASE;
 assert(!wr_iot_physical_initial_record_reply(&attempt,&request,&task,wire,64));
 request.action=WR_STOP_QUERY;
 assert(wr_iot_main_recovery_begin(&owner));
 assert(wr_iot_main_close_note_checked_down(main,&ticket,1,1));
 {int release=0;assert(wr_iot_main_stop_complete(&radio,main,&main_dev,main->generation,main->last_token,&ticket,1,1,&release));assert(release);}
 assert(wr_iot_main_recovery_mark_completed(&owner,main));
 assert(wr_iot_main_recovery_mark_module_pin_released(&owner,1,1));
 assert(wr_iot_main_recovery_begin_netdev_release(&owner,1));
 assert(!wr_iot_physical_initial_main_released(&origin,&life,&owner,&radio,main,iot,0));
 assert(wr_iot_main_recovery_finish_netdev_release(&owner,&main_dev,&radio,1));
 assert(wr_iot_physical_initial_main_released(&origin,&life,&owner,&radio,main,iot,0));
 /* Main receipt alone cannot publish full initial physical completion. */
 assert(wr_iot_physical_initial_record_reply(&attempt,&request,&task,wire,64));
 assert(wr_iot_physical_initial_decode(&response,wire,64,1)&&response.status==WR_STOP_RUNNING);
 assert(!wr_iot_physical_initial_main_released(&origin,&life,&owner,&radio,main,iot,1));
 assert(wr_iot_physical_initial_history(&origin,iot));
 assert(wr_iot_physical_initial_main_binding(&origin,&life));
 struct wr_iot_interface_ref saved=*iot;
 for(unsigned fault=0;fault<12;fault++){
  *iot=saved;
  switch(fault){
   case 0:iot->last_token=1;break;case 1:iot->close_serial=1;break;
   case 2:iot->close_epoch=1;break;case 3:iot->generation++;break;
   case 4:iot->device=&main_dev;break;case 5:iot->published=0;break;
   case 6:iot->removing=1;break;case 7:iot->phase=WR_REF_OWNED;break;
   case 8:iot->open_unmutated=1;break;case 9:iot->close_running=1;break;
   case 10:iot->close_verified_stage=1;break;case 11:iot->close_prior_ready=1;break;
  }
  assert(!wr_iot_physical_initial_history(&origin,iot));
 }
 *iot=saved;life.main_open_token++;assert(!wr_iot_physical_initial_main_binding(&origin,&life));
 life.main_open_token--;life.serial++;assert(!wr_iot_physical_initial_main_binding(&origin,&life));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-physical-origin-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=10)
print('PASS actual idle probe/Main lifetime initial origin: no fake CLOSE, capture once, zero-history refusal, actual Main close/recovery/netdev-release sequence, pre-release/count/foreign refusal; no ARM endpoint or device claim')
