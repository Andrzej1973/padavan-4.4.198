"""Actual ARM admission + reference publication composition; host only."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-arm-admission.py'))
context=base['context'].split('int main(void)',1)[0]
context=context.replace(' struct wr_iot_physical_stop_record wr_iot_physical_stop;',
 ' struct wr_iot_physical_stop_record wr_iot_physical_stop;\n struct wr_iot_peer_close_executor wr_iot_peer_close_executor;')
context+=r'''
struct task_struct {int unused;};struct net_device {int unused;};
static struct task_struct task;static struct task_struct *current=&task;
static int modules=1,tasks=1,devices=1;
#define THIS_MODULE ((void *)1)
static int try_module_get(void *m){assert(m==THIS_MODULE&&!held);modules++;return 1;}
static void module_put(void *m){assert(m==THIS_MODULE&&!held);modules--;}
static void get_task_struct(struct task_struct *t){assert(t==current&&!held);tasks++;}
static void put_task_struct(struct task_struct *t){assert(t==current&&!held);tasks--;}
static void dev_hold(struct net_device *d){assert(d&&!held);devices++;}
static void dev_put(struct net_device *d){assert(d&&!held);devices--;}
#include "physical-stop-pins.inc"
#include "physical-stop-arm-publication.inc"
int main(void){
'''
body=base['setup'].replace('int main_dev,device;','int main_dev=0,device=0;')+r'''
 assert(wr_iot_driver_close_release_reference(&close,&open,&request,&radio,
  slots,2,&main_dev,&device,1,&probe,&producer,7));
 RTMP_ADAPTER ad={0};unsigned long serial=0;unsigned long long attempt=77;
 struct wr_iot_physical_stop_pins detached={0};
 struct wr_iot_physical_stop_request arm={.action=WR_STOP_ARM,.epoch=1,
   .generation=2,.open_token=3,.closed_serial=4,.nonce={9}},bad;
 ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&device;
 ad.VirtualIfCnt=1;ad.wr_iot_close_owner=close;ad.wr_iot_driver_owner=open;
 radio.serial=radio.retired_serial;ad.wr_iot_transition=radio;
 memcpy(ad.wr_iot_interface_refs,slots,sizeof(slots));
 ad.wr_iot_closed_probe=probe;ad.wr_iot_beacon_gates[2]=producer;
 wr_iot_main_recovery_init(&ad.wr_iot_main_recovery);
 assert(!wr_iot_physical_stop_arm_admit(&ad,&main_dev,&arm,&serial));
 assert(wr_iot_physical_stop_pins_acquire(&ad.wr_iot_physical_pending_pins,current,(struct net_device *)&main_dev));
 bad=arm;bad.nonce[0]++;
 assert(wr_iot_physical_stop_arm_publish_owned(&ad,&main_dev,&bad,serial,
   &ad.wr_iot_physical_pins,&ad.wr_iot_physical_pending_pins,&attempt)==-EBUSY);
 assert(ad.wr_iot_physical_pending_pins.module&&!ad.wr_iot_physical_pins.module&&attempt==77&&!held);
 bad=arm;bad.generation++;
 assert(wr_iot_physical_stop_arm_publish_owned(&ad,&main_dev,&bad,serial,
   &ad.wr_iot_physical_pins,&ad.wr_iot_physical_pending_pins,&attempt)==-EBUSY);
 assert(!wr_iot_physical_stop_arm_publish_owned(&ad,&main_dev,&arm,serial,
   &ad.wr_iot_physical_pins,&ad.wr_iot_physical_pending_pins,&attempt));
 assert(attempt==1&&!ad.wr_iot_physical_pending_pins.module&&ad.wr_iot_physical_pins.module&&modules==2&&tasks==2&&devices==2);
 assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,serial)==-EBUSY);
 held=2;
 assert(wr_iot_physical_stop_pins_detach(&ad.wr_iot_physical_pins,&detached,&ad.wr_iot_physical_stop,
   attempt,arm.epoch,arm.generation,arm.nonce,1));
 held=0;
 assert(wr_iot_physical_stop_pins_drop(&detached));
 assert(modules==1&&tasks==1&&devices==1);
 assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,serial)==-EBUSY);
 assert(wr_iot_physical_stop_lifetime_end(&ad.wr_iot_physical_lifetime,serial,
   ad.wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE,
   !detached.module&&!detached.task&&!detached.device));
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-stop-arm-publish-') as d:
 c=Path(d)/'check.c';c.write_text(base['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual ARM publication: exact retained request, failed publish keeps local refs, transfer once, cancel returns extras; no endpoint/target/runtime claim')
