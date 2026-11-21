"""Actual initial completion fragment with real Main owner transitions; IO actors."""
from pathlib import Path
import subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-origin.py')}
s=(here/'check-physical-initial-origin.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<initial origin fixture>','exec'),ns)
code=ns['code']
hooks=r'''
#include <errno.h>
#include "physical-stop-pin-types.h"
#include "peer-close-executor.h"
#include "peer-table-owner.h"
typedef int INT;typedef unsigned long ULONG;typedef void *PNET_DEV;
#define WDEV_NUM_MAX 2
struct mock_bss {struct {void *if_dev;} wdev;};
typedef struct {
 int MacTabLock,wr_iot_transition_lock;unsigned vendor_count;
 struct {struct mock_bss MBSSID[3];} ApCfg;
 struct wr_iot_physical_initial_record wr_iot_physical_initial;
 struct wr_iot_physical_stop_pins wr_iot_physical_pins;
 struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[3];
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
} RTMP_ADAPTER;
static int locked,rtnl=1;
static int rtnl_is_locked(void){return rtnl;}
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);(void)(flags);assert(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);(void)(flags);assert(locked);locked=0;}while(0)
#define VIRTUAL_IF_NUM(ad) ((ad)->vendor_count)
#include "physical-initial-main-completion.inc"
'''
code=code.replace('int main(void){',hooks+'\nint main(void){',1)
needle=' assert(!wr_iot_physical_initial_main_released(&origin,&life,&owner,&radio,main,iot,1));'
test=r'''
 RTMP_ADAPTER ad={0};
 ad.wr_iot_physical_initial=attempt;ad.wr_iot_physical_lifetime=life;
 ad.wr_iot_main_recovery=owner;ad.wr_iot_transition=radio;
 memcpy(ad.wr_iot_interface_refs,slots,sizeof(slots));
 ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
 ad.wr_iot_transition.shutdown_stage=2;ad.wr_iot_transition.mt_radio_off_stage=4;
 ad.wr_iot_transition.virtual_down_stage=2;
 ad.wr_iot_physical_pins.module=1;ad.wr_iot_physical_pins.task=(struct task_struct *)&task;
 ad.wr_iot_physical_pins.device=(struct net_device *)&main_dev;
 /* Main receipt without the actual table close seal still refuses. */
 assert(wr_iot_physical_initial_main_complete(&ad,&main_dev,attempt.serial)==-EAGAIN);
 unsigned long table_serial=wr_iot_peer_table_begin(&ad.wr_iot_peer_table_owner);
 assert(table_serial&&wr_iot_peer_table_close_seal(&ad.wr_iot_peer_table_owner,table_serial));
 for(unsigned fault=0;fault<8;fault++){
  RTMP_ADAPTER changed=ad;
  switch(fault){case 0:changed.wr_iot_physical_pins.module=0;break;
   case 1:changed.wr_iot_physical_pins.task=0;break;
   case 2:changed.wr_iot_transition.mt_radio_off_stage=3;break;
   case 3:changed.wr_iot_peer_table_owner.transactions=1;break;
   case 4:changed.wr_iot_peer_close_executor.running=1;break;
   case 5:changed.wr_iot_interface_refs[1].last_token=99;break;
   case 6:changed.wr_iot_physical_lifetime.serial++;break;
   case 7:changed.vendor_count=1;break;}
  assert(wr_iot_physical_initial_main_complete(&changed,&main_dev,attempt.serial)==-EAGAIN);
  assert(changed.wr_iot_physical_initial.status==WR_STOP_RUNNING&&!locked);
 }
 rtnl=0;assert(wr_iot_physical_initial_main_complete(&ad,&main_dev,attempt.serial)==-EBUSY);rtnl=1;
 assert(!wr_iot_physical_initial_main_complete(&ad,&main_dev,attempt.serial));
 assert(ad.wr_iot_physical_initial.status==WR_STOP_COMPLETE&&!locked);
 assert(!wr_iot_physical_initial_main_complete(&ad,&main_dev,attempt.serial));
 ad.wr_iot_transition.epoch++;
 assert(wr_iot_physical_initial_main_complete(&ad,&main_dev,attempt.serial)==-EAGAIN);
'''
assert needle in code;before,after=code.rsplit(needle,1)
code=before+needle+test+after
with tempfile.TemporaryDirectory(prefix='wr-initial-completion-') as d:
 root=Path(d)
 # Prepared driver adds this checked vendor stage; preserve remaining real header.
 (root/'radio-transition.h').write_text((here/'radio-transition.h').read_text().replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;'))
 for p in here.glob('*.h'):
  if p.name not in ('radio-transition.h','radio-transition-api.h'):shutil.copyfile(p,root/p.name)
 (root/'radio-transition-api.h').write_text((here/'radio-transition-api.h').read_text().replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;'))
 unit=root/'check.c';unit.write_text(code);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual initial completion fragment: real idle/Main reference lifecycle, table seal required, disjoint locks, stage/pins/table/executor/history/epoch refusal, duplicate read; SDK adapters injected, not installed')
