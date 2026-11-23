"""Exercise actual extracted Main worker with ARM identity guard; host only."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'physical-stop-main-binding.py'))['compose']
initial=runpy.run_path(str(here/'physical-initial-main-binding.py'))['compose']
def compose(source):return initial(base(source))
source=(here/'main-close-checked.inc').read_text()
changed=compose(source)
try:compose(changed)
except ValueError:pass
else:raise AssertionError('duplicate binding accepted')
with tempfile.TemporaryDirectory(prefix='wr-stop-main-binding-') as d:
 root=Path(d);candidate=root/'candidate';(candidate/'os/linux').mkdir(parents=True)
 (candidate/'os/linux/rt_main_dev.c').write_text(changed)
 inc=root/'include';inc.mkdir()
 for p in here.glob('*.h'):shutil.copy2(p,inc/p.name)
 radio=(inc/'radio-transition.h').read_text()
 radio=radio.replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
 (inc/'radio-transition.h').write_text(radio)
 api=inc/'radio-transition-api.h'
 api.write_text(api.read_text().replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;'))
 c=root/'check.c'
 subprocess.run(['python3',str(here/'prepare-main-close-check.py'),str(c),'--candidate',str(candidate)],check=True)
 s=c.read_text().replace('#include "main-stop-owned.h"','#include "radio-transition-api.h"\n#include "main-stop-owned.h"').replace('#include "main-stop-owned.h"','#include "main-stop-owned.h"\n#include "physical-stop-lifetime.h"\n#include "physical-stop-record.h"\n#include "physical-initial-record.h"\n#include "physical-stop-pin-types.h"')
 s=s.replace(' int wr_iot_ticket_wait;',' int MacTabLock;\n struct wr_iot_physical_initial_record wr_iot_physical_initial;\n struct wr_iot_physical_stop_record wr_iot_physical_stop;\n struct wr_iot_physical_stop_pins wr_iot_physical_pins;\n struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;\n int wr_iot_ticket_wait;')
 anchor=' puts("PASS partial main close:'
 test=''' {
  struct adapter ad={0};struct net_device dev={0};int extra_peer=0;
  unsigned before;
  setup(&ad,&dev,&extra_peer,1);
  assert(wr_iot_physical_stop_lifetime_begin_main(&ad.wr_iot_physical_lifetime,
    &ad.wr_iot_transition,&ad.wr_iot_main_recovery,
    &ad.wr_iot_interface_refs[0],&dev));
  {struct wr_iot_physical_stop_request req={.action=WR_STOP_ARM,.epoch=1,
     .generation=2,.open_token=3,.closed_serial=4,.nonce={9}};
   struct wr_iot_peer_close_executor executor={0};
   ad.wr_iot_physical_lifetime.arm_request=req;
   assert(wr_iot_physical_stop_arm(&ad.wr_iot_physical_stop,1,2,3,4,
     req.nonce,&extra_peer,&executor));
   ad.wr_iot_physical_pins.task=(struct task_struct *)&extra_peer;
   ad.wr_iot_physical_pins.device=&dev;ad.wr_iot_physical_pins.module=1;
  }
  assert(wr_iot_main_recovery_queue(&ad.wr_iot_main_recovery,
    &ad.wr_iot_transition,&ad.wr_iot_interface_refs[0],
    WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
  assert(wr_iot_main_recovery_schedule_result(&ad.wr_iot_main_recovery,1));
  before=down_calls;
  ad.wr_iot_physical_lifetime.main_open_token++;
  assert(wr_iot_main_recovery_execute(&ad)==-1);
  assert((unsigned)down_calls==before&&pins==1);
  assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_RETAINED);
  ad.wr_iot_physical_lifetime.main_open_token--;
  assert(wr_iot_main_recovery_requeue(&ad.wr_iot_main_recovery,3,1));
  assert(wr_iot_main_recovery_schedule_result(&ad.wr_iot_main_recovery,1));
  {struct adapter alternative=ad;
   assert(wr_iot_physical_stop_cancel(&ad.wr_iot_physical_stop,1,1,2,
     ad.wr_iot_physical_lifetime.arm_request.nonce,&extra_peer));
   assert(wr_iot_main_recovery_execute(&ad)==-1);
   assert((unsigned)down_calls==before&&pins==1);
   ad=alternative; /* separate schedule alternative, not driver rollback */
  }
  assert(wr_iot_main_recovery_execute(&ad)==0);
  assert((unsigned)down_calls==before+1&&pins==0);
  assert(ad.wr_iot_physical_stop.phase==WR_PHYS_STOP_RUNNING);
  assert(!wr_iot_physical_stop_cancel(&ad.wr_iot_physical_stop,1,1,2,
    ad.wr_iot_physical_lifetime.arm_request.nonce,&extra_peer));
  assert(ad.wr_iot_physical_lifetime.main_ticket_valid);
  assert(ad.wr_iot_physical_lifetime.main_ticket.serial==
    ad.wr_iot_main_recovery.close_ticket.serial);
 }
'''
 test+=''' {
  struct adapter ad={0};struct net_device dev={0};int peer=0;
  unsigned before;
  setup(&ad,&dev,&peer,1);
  /* Binding fixture starts after an accepted idle observation; origin/probe
   * admission itself is exercised by check-physical-initial-origin.py. */
  ad.wr_iot_transition.serial=ad.wr_iot_transition.retired_serial=1;
  assert(wr_iot_physical_stop_lifetime_begin_main(&ad.wr_iot_physical_lifetime,
    &ad.wr_iot_transition,&ad.wr_iot_main_recovery,
    &ad.wr_iot_interface_refs[0],&dev));
  {struct wr_iot_physical_initial_record *r=&ad.wr_iot_physical_initial;
   struct wr_iot_physical_stop_lifetime *l=&ad.wr_iot_physical_lifetime;
   r->serial=1;r->task=&peer;r->status=WR_STOP_ARMED;
   r->request.action=WR_STOP_ARM;r->request.epoch=l->arm_radio_epoch;
   r->request.generation=2;r->request.idle_serial=l->arm_radio_serial;
   r->request.nonce[0]=9;r->request.attempt=1;
   r->origin.main_device=&dev;r->origin.iot_device=&peer;
   r->origin.epoch=l->arm_radio_epoch;r->origin.generation=2;
   r->origin.idle_serial=l->arm_radio_serial;
   r->origin.main_generation=l->main_generation;
   r->origin.main_open_token=l->main_open_token;
   r->origin.lifetime_serial=l->serial;
   ad.wr_iot_physical_pins.task=(struct task_struct *)&peer;
   ad.wr_iot_physical_pins.device=&dev;ad.wr_iot_physical_pins.module=1;
  }
  assert(wr_iot_main_recovery_queue(&ad.wr_iot_main_recovery,
    &ad.wr_iot_transition,&ad.wr_iot_interface_refs[0],
    WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
  assert(wr_iot_main_recovery_schedule_result(&ad.wr_iot_main_recovery,1));
  before=down_calls;
  ad.wr_iot_physical_initial.origin.main_open_token++;
  assert(wr_iot_main_recovery_execute(&ad)==-1);
  assert((unsigned)down_calls==before&&pins==1);
  ad.wr_iot_physical_initial.origin.main_open_token--;
  assert(wr_iot_main_recovery_requeue(&ad.wr_iot_main_recovery,3,1));
  assert(wr_iot_main_recovery_schedule_result(&ad.wr_iot_main_recovery,1));
  assert(wr_iot_main_recovery_execute(&ad)==0);
  assert((unsigned)down_calls==before+1&&pins==0);
  assert(ad.wr_iot_physical_initial.status==WR_STOP_RUNNING);
  assert(ad.wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE);
 }
'''
 assert s.count(anchor)==1;s=s.replace(anchor,test+anchor);c.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-DWR_TEST_RECOVERY_LOG','-fno-pie','-no-pie','-I'+str(inc),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual Main worker initial-origin and legacy branches: initial wrong-token refusal then exact RUNNING/DOWN once, legacy wrong ARM token/cancelled record retain before DOWN, valid record becomes RUNNING and closes once; endpoint/target unverified')
