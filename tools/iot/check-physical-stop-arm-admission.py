"""Actual ARM adapter binding with existing released-CLOSE fixture; host only."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-driver-api-close-release.c').read_text()
prefix=source.split('int main(void)',1)[0]
setup=source[source.index('  int main_dev,device;'):source.index('  switch(fault)')]
context=r'''
#include <errno.h>
#include "physical-stop-lifetime.h"
#include "physical-stop-record.h"
#include "physical-stop-pin-types.h"
#include "physical-stop-terminal-types.h"
#define WR_IOT_RA2_NO_HOST_MODE 1
#define WDEV_NUM_MAX 1
typedef int INT;typedef unsigned long ULONG;typedef void *PNET_DEV;
typedef struct {
 int BcnRingLock,wr_iot_transition_lock,MacTabLock;
 struct wr_iot_physical_stop_record wr_iot_physical_stop;
 struct wr_iot_physical_stop_pins wr_iot_physical_pins,wr_iot_physical_pending_pins;
 struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;
 struct {unsigned BssidNum;struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];} ApCfg;
 PNET_DEV net_dev;
 unsigned VirtualIfCnt,wr_iot_control_users,wr_iot_control_poisoned;
 unsigned wr_iot_boot_active,wr_iot_boot_failed;
 struct wr_iot_beacon_producer_gate wr_iot_beacon_gates[3];
 struct wr_iot_driver_close_owner wr_iot_close_owner;
 struct wr_iot_driver_owner wr_iot_driver_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_mbss_closed_probe wr_iot_closed_probe;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;
} RTMP_ADAPTER;
static int held,rtnl=1;
#define rtnl_is_locked() (rtnl)
#define IS_MT7603(ad) ((void)(ad),1)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define RTMP_SEM_LOCK(l) do{(void)(l);assert(!held);held=1;}while(0)
#define RTMP_SEM_UNLOCK(l) do{(void)(l);assert(held==1);held=0;}while(0)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=2;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held==2);held=0;}while(0)
#include "physical-stop-arm-admission.inc"
int main(void){for(unsigned fault=0;fault<10;fault++){
'''
body=setup+r'''
 assert(wr_iot_driver_close_release_reference(&close,&open,&request,&radio,
  slots,2,&main_dev,&device,1,&probe,&producer,7));
 RTMP_ADAPTER ad={0};unsigned long serial=77;
 ad.wr_iot_physical_stop.serial=1ULL<<40;
 struct wr_iot_physical_stop_request arm={.action=WR_STOP_ARM,.epoch=1,
   .generation=2,.open_token=3,.closed_serial=4,.nonce={9}};
 ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&device;
 ad.VirtualIfCnt=1;ad.wr_iot_close_owner=close;ad.wr_iot_driver_owner=open;
 radio.serial=radio.retired_serial;
 ad.wr_iot_transition=radio;memcpy(ad.wr_iot_interface_refs,slots,sizeof(slots));
 ad.wr_iot_closed_probe=probe;ad.wr_iot_beacon_gates[2]=producer;
 wr_iot_main_recovery_init(&ad.wr_iot_main_recovery);
 rtnl=1;
 switch(fault){
  case 1:ad.wr_iot_beacon_gates[2].active=1;break;
  case 2:arm.open_token++;break;
  case 3:ad.wr_iot_boot_active=1;break;
  case 4:ad.wr_iot_interface_refs[0].removing=1;break;
  case 5:ad.wr_iot_transition.reset_pending=1;break;
  case 6:ad.wr_iot_physical_lifetime.active=1;break;
  case 7:rtnl=0;break;
  case 8:ad.wr_iot_transition.serial++;break;
  case 9:ad.wr_iot_physical_terminal.owner=(struct pid *)&main_dev;break;
 }
 int status=wr_iot_physical_stop_arm_admit(&ad,&main_dev,&arm,&serial);
 assert(!held);
 if(fault){assert(status<0&&serial==77);}
 else{
  assert(!status&&serial==1&&ad.wr_iot_physical_lifetime.active);
  assert(ad.wr_iot_physical_lifetime.arm_record_serial==(1ULL<<40));
  assert(ad.wr_iot_physical_lifetime.main_device==&main_dev);
  assert(ad.wr_iot_physical_lifetime.main_generation==main->generation);
  assert(ad.wr_iot_physical_lifetime.main_open_token==main->last_token);
  serial=77;
  assert(wr_iot_physical_stop_arm_admit(&ad,&main_dev,&arm,&serial)==-EAGAIN);
  assert(serial==77);
  {RTMP_ADAPTER before=ad;
   for(unsigned drift=0;drift<8;drift++){
    switch(drift){
     case 0:ad.wr_iot_interface_refs[0].generation++;break;
     case 1:ad.wr_iot_interface_refs[0].last_token++;break;
     case 2:ad.wr_iot_main_recovery.phase=WR_MAIN_OWNER_RUNNING;break;
     case 3:ad.wr_iot_physical_lifetime.main_ticket_valid=1;break;
     case 4:ad.wr_iot_transition.phase=WR_RADIO_CLOSING;break;
     case 5:ad.wr_iot_transition.epoch++;break;
     case 6:ad.wr_iot_physical_stop.phase=WR_PHYS_STOP_ARMED;break;
     case 7:ad.wr_iot_physical_pending_pins.module=1;break;
    }
    assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,1)==-EBUSY);
    assert(ad.wr_iot_physical_lifetime.active&&!held);
    ad=before;
   }
  }
  ad.wr_iot_physical_stop.serial++;
  assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,1)==-EBUSY);
  assert(ad.wr_iot_physical_lifetime.active);
  ad.wr_iot_physical_stop.serial--;
  assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,1)==0);
  assert(!ad.wr_iot_physical_lifetime.active);
  assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,1)==-EBUSY);
 }
}return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-stop-arm-binding-') as d:
 c=Path(d)/'check.c';c.write_text(prefix+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual ARM adapter admission: released ra2 CLOSE and Main registry snapshot with disjoint locks; nine refusals and duplicate; no endpoint/target/runtime proof')
