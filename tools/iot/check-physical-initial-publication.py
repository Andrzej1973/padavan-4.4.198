"""Actual INITIAL_OFF ARM publication, real origin/lifetime; kernel refs actors."""
from pathlib import Path
import subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-completion.py')}
s=(here/'check-physical-initial-completion.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<completion fixture>','exec'),ns)
code=ns['code']
code=code.replace('int MacTabLock,wr_iot_transition_lock;unsigned vendor_count;',r'''
 int MacTabLock,wr_iot_transition_lock;unsigned vendor_count;void *net_dev;
 unsigned wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed;
 struct {int active,poisoned;} wr_iot_driver_owner;
 struct {int active;} wr_iot_close_owner;
 struct wr_iot_precreated_idle_probe wr_iot_idle_probe;
 struct wr_iot_physical_stop_record wr_iot_physical_stop;
 struct wr_iot_physical_stop_pins wr_iot_physical_pending_pins;
''',1).replace('struct {struct mock_bss MBSSID[3];} ApCfg;','struct {struct mock_bss MBSSID[3];unsigned BssidNum;} ApCfg;',1)
code=code.replace('#include "physical-stop-pin-types.h"','#include "physical-stop-pin-types.h"\n#include "physical-stop-record.h"',1)
code=code.replace('#include "physical-initial-main-completion.inc"',r'''
static struct task_struct *current;
static int modules=1,tasks=1,devices=1,fail_module;
#define THIS_MODULE ((void *)1)
static int try_module_get(void *module){assert(module==THIS_MODULE&&!locked);if(fail_module)return 0;modules++;return 1;}
static void get_task_struct(struct task_struct *task){assert(task==current&&!locked);tasks++;}
static void dev_hold(struct net_device *device){assert(device&&!locked);devices++;}
static void dev_put(struct net_device *device){assert(device&&!locked&&devices>1);devices--;}
static void put_task_struct(struct task_struct *task){assert(task==current&&!locked&&tasks>1);tasks--;}
static void module_put(void *module){assert(module==THIS_MODULE&&!locked&&modules>1);modules--;}
#include "physical-stop-pins.inc"
#include "physical-initial-pins.inc"
#define IS_MT7603(ad) ((ad)!=NULL)
#include "physical-initial-arm-publication.inc"
#include "physical-initial-main-completion.inc"
''',1)
needle=' assert(wr_iot_physical_initial_record_arm(&attempt,&request,&task,&origin,&life,iot));'
test=r'''
 RTMP_ADAPTER arm_ad={0};unsigned long long published=0;
 current=(struct task_struct *)&task;
 arm_ad.net_dev=&main_dev;arm_ad.ApCfg.BssidNum=3;
 arm_ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;arm_ad.vendor_count=1;
 arm_ad.wr_iot_idle_probe=probe;arm_ad.wr_iot_physical_lifetime=life;
 arm_ad.wr_iot_transition=radio;memcpy(arm_ad.wr_iot_interface_refs,slots,sizeof(slots));
 fail_module=1;
 assert(!wr_iot_physical_stop_pins_acquire(&arm_ad.wr_iot_physical_pending_pins,current,(struct net_device *)&main_dev));
 assert(modules==1&&tasks==1&&devices==1&&!arm_ad.wr_iot_physical_pending_pins.module);
 fail_module=0;
 assert(wr_iot_physical_stop_pins_acquire(&arm_ad.wr_iot_physical_pending_pins,current,(struct net_device *)&main_dev));
 assert(modules==2&&tasks==2&&devices==2);
 /* Real pre-publication refusal and native unwind, with no lock held. */
 arm_ad.wr_iot_control_users=1;
 assert(wr_iot_physical_initial_arm_publish(&arm_ad,&main_dev,&request,&arm_ad.wr_iot_physical_pending_pins,&published)==-EAGAIN);
 assert(wr_iot_physical_stop_pins_drop(&arm_ad.wr_iot_physical_pending_pins));
 assert(!wr_iot_physical_stop_pins_drop(&arm_ad.wr_iot_physical_pending_pins));
 assert(modules==1&&tasks==1&&devices==1);
 arm_ad.wr_iot_control_users=0;
 assert(wr_iot_physical_stop_pins_acquire(&arm_ad.wr_iot_physical_pending_pins,current,(struct net_device *)&main_dev));
 for(unsigned fault=0;fault<7;fault++){
  RTMP_ADAPTER changed=arm_ad;
  switch(fault){case 0:changed.wr_iot_control_users=1;break;
   case 1:changed.wr_iot_idle_probe.accepted=0;break;
   case 2:changed.wr_iot_interface_refs[1].last_token=1;break;
   case 3:changed.wr_iot_physical_pins.module=1;break;
   case 4:changed.wr_iot_peer_table_owner.transactions=1;break;
   case 5:changed.wr_iot_peer_close_executor.running=1;break;
   case 6:changed.wr_iot_physical_stop.phase=WR_PHYS_STOP_RUNNING;break;}
  assert(wr_iot_physical_initial_arm_publish(&changed,&main_dev,&request,&changed.wr_iot_physical_pending_pins,&published)==-EAGAIN);
  assert(!published&&changed.wr_iot_physical_pending_pins.module==1&&
   changed.wr_iot_physical_pending_pins.task==current&&!changed.wr_iot_physical_initial.task&&!locked);
 }
 assert(!wr_iot_physical_initial_arm_publish(&arm_ad,&main_dev,&request,&arm_ad.wr_iot_physical_pending_pins,&published));
 assert(published==1&&arm_ad.wr_iot_physical_initial.status==WR_STOP_ARMED&&
  !arm_ad.wr_iot_physical_pending_pins.module&&arm_ad.wr_iot_physical_pins.task==current);
 assert(wr_iot_physical_initial_arm_publish(&arm_ad,&main_dev,&request,&arm_ad.wr_iot_physical_pending_pins,&published)==-EAGAIN);
 assert(arm_ad.wr_iot_physical_initial.serial==1&&!locked);
 assert(modules==2&&tasks==2&&devices==2);
 assert(!wr_iot_physical_stop_pins_drop(&arm_ad.wr_iot_physical_pending_pins));
 /* Wrong action/task/attempt never detaches. */
 struct wr_iot_physical_stop_pins detached={0};
 struct wr_iot_physical_initial_request terminal=request;
 terminal.action=WR_STOP_RELEASE;terminal.attempt=published;
 assert(!wr_iot_physical_initial_pins_detach(&arm_ad.wr_iot_physical_pins,&detached,&arm_ad.wr_iot_physical_initial,&terminal));
 struct net_device *saved_device=arm_ad.wr_iot_physical_pins.device;
 arm_ad.wr_iot_physical_pins.device=(struct net_device *)&other;
 terminal.action=WR_STOP_CANCEL;terminal.attempt=published;
 assert(!wr_iot_physical_initial_pins_detach(&arm_ad.wr_iot_physical_pins,&detached,&arm_ad.wr_iot_physical_initial,&terminal));
 assert(!detached.module&&arm_ad.wr_iot_physical_initial.task==current);
 arm_ad.wr_iot_physical_pins.device=saved_device;
 terminal.action=WR_STOP_CANCEL;terminal.attempt++;
 assert(!wr_iot_physical_initial_pins_detach(&arm_ad.wr_iot_physical_pins,&detached,&arm_ad.wr_iot_physical_initial,&terminal));
 terminal.attempt=published;
 locked=1;
 assert(wr_iot_physical_initial_cancel_current(&arm_ad.wr_iot_physical_initial.origin,
  &arm_ad.wr_iot_physical_lifetime,&arm_ad.wr_iot_idle_probe,&arm_ad.wr_iot_main_recovery,
  &arm_ad.wr_iot_transition,arm_ad.wr_iot_interface_refs,3,1));
 locked=0;locked=1; /* RTNL/lifetime retained, transition and MacTab disjoint. */
 assert(wr_iot_physical_initial_pins_detach(&arm_ad.wr_iot_physical_pins,&detached,&arm_ad.wr_iot_physical_initial,&terminal));
 locked=0;
 assert(!arm_ad.wr_iot_physical_initial.task&&modules==2&&tasks==2&&devices==2);
 assert(!wr_iot_physical_initial_pins_detach(&arm_ad.wr_iot_physical_pins,&arm_ad.wr_iot_physical_pending_pins,&arm_ad.wr_iot_physical_initial,&terminal));
 assert(wr_iot_physical_stop_pins_drop(&detached));
 assert(modules==1&&tasks==1&&devices==1);
 /* Lifetime and terminal reply are deliberately not acknowledged here. */
'''
assert needle in code;code=code.replace(needle,test+needle,1)
with tempfile.TemporaryDirectory(prefix='wr-initial-publish-') as d:
 root=Path(d)
 for p in here.glob('*.h'):
  text=p.read_text()
  if p.name in ('radio-transition.h','radio-transition-api.h'):
   text=text.replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
  (root/p.name).write_text(text)
 unit=root/'check.c';unit.write_text(code);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual initial ARM publication: real idle/Main lifetime, seven refusal gates preserve acquired local refs, exact slot transfer once, old CLOSE owner exclusion, disjoint locks; actual native acquire/unpublished drop, module failure and balanced unwind; kernel ref primitives injected, published CANCEL detach plus native return once; terminal acknowledgement unbound')
