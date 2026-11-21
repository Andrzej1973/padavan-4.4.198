from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "physical-stop-origin.h"
#include "mbss-close-receipt.h"
int main(void){
 int dev;
 struct wr_iot_physical_stop_origin origin={2,3,5,7,6,6,1};
 struct wr_iot_main_recovery_owner owner={0};
 owner.last_release=(struct wr_iot_main_recovery_release_receipt){.device=&dev,.generation=2,.open_token=3,.close_serial=9,.ticket={.serial=7,.epoch=6,.operation=WR_RADIO_CLOSE},.completion_epoch=6,.valid=1};
 struct wr_iot_radio_transition radio={.epoch=6,.serial=7,.retired_serial=7,.phase=WR_RADIO_DOWN};
 struct wr_iot_interface_ref main={.device=&dev,.generation=2,.last_token=3,.published=1,.family=WR_REF_FAMILY_MAIN,.phase=WR_REF_IDLE,.close_stage=4,.close_serial=9,.close_epoch=6,.close_vendor_count=1};
 assert(wr_iot_physical_stop_origin_main_down(&origin,&owner,&radio,&main,0));
 for(int fault=0;fault<10;fault++){
  struct wr_iot_radio_transition r=radio;struct wr_iot_main_recovery_owner o=owner;struct wr_iot_interface_ref m=main;
  unsigned count=0;
  switch(fault){case 0:r.phase=WR_RADIO_READY;r.main_ready=1;break;case 1:r.epoch++;break;case 2:r.serial++;break;case 3:r.reset_pending=1;break;case 4:o.last_release.open_token++;break;case 5:m.generation++;break;case 6:m.phase=WR_REF_OWNED;break;case 7:count=1;break;case 8:m.close_epoch++;break;case 9:o.deferred_owners=1;break;}
  assert(!wr_iot_physical_stop_origin_main_down(&origin,&o,&r,&m,count));
 }
 assert(!wr_iot_physical_stop_origin_main_down(&origin,0,&radio,&main,0));
 /* Normal ra2 CLOSED preflight explicitly refuses DOWN before any BSS lookup. */
 assert(!wr_iot_mbss_closed_record_current(&radio,0,0,&dev,&owner,1,1,1,1));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-origin-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS exact physical OFF origin with existing Main release-current predicate; READY/epoch/registration/count drift refused, normal BSS CLOSED incompatible with DOWN; no ioctl binding')
