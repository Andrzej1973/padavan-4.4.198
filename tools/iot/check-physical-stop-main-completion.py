"""Compose actual Main release predicate and checked physical record bridge."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-arm-publication.py'))
context=base['context'].replace(' struct wr_iot_peer_close_executor wr_iot_peer_close_executor;',
 ' struct wr_iot_peer_close_executor wr_iot_peer_close_executor;\n struct wr_iot_peer_table_owner wr_iot_peer_table_owner;')
context=context.replace('int main(void){','#include "physical-stop-main-completion.inc"\nint main(void){')
body=base['body'];anchor=' assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,serial)==-EBUSY);'
a=body.index(anchor)
scenario=r'''
 {RTMP_ADAPTER alternative=ad;
  struct wr_iot_radio_ticket ticket,captured;
  struct wr_iot_interface_ref *record=&ad.wr_iot_interface_refs[0];
  int release=0;
  assert(wr_iot_physical_stop_main_complete(&ad,&main_dev,serial)==-EAGAIN);
  assert(wr_iot_radio_begin_main_stop(&ad.wr_iot_transition,1,&ticket));
  assert(wr_iot_ref_begin_close(record,&main_dev,1,1));
  assert(wr_iot_main_close_claim_preclose(&ad.wr_iot_transition,record,
    ad.wr_iot_interface_refs,2,&ticket,1));
  assert(wr_iot_main_close_claim_void_preclose(record,&ticket));
  assert(wr_iot_main_close_finish_preclose(record,&ticket));
  assert(wr_iot_main_recovery_queue_close(&ad.wr_iot_main_recovery,
    &ad.wr_iot_transition,record,ad.wr_iot_interface_refs,2,&ticket,1,1,1,
    WR_MAIN_QUEUE_NORMAL,0));
  assert(wr_iot_main_recovery_schedule_result(&ad.wr_iot_main_recovery,1));
  assert(wr_iot_main_recovery_begin(&ad.wr_iot_main_recovery));
  assert(wr_iot_physical_stop_lifetime_capture_main(&ad.wr_iot_physical_lifetime,
    serial,&ad.wr_iot_main_recovery,&ad.wr_iot_transition,record,&captured));
  assert(wr_iot_physical_stop_begin(&ad.wr_iot_physical_stop,attempt,1,2,arm.nonce,current));
  assert(wr_iot_main_close_note_checked_down(record,&ticket,1,1));
  assert(wr_iot_main_stop_complete(&ad.wr_iot_transition,record,&main_dev,1,1,
    &ticket,1,1,&release));
  ad.VirtualIfCnt=0;
  assert(wr_iot_main_recovery_mark_completed(&ad.wr_iot_main_recovery,record));
  assert(wr_iot_main_recovery_mark_module_pin_released(&ad.wr_iot_main_recovery,1,1));
  assert(wr_iot_main_recovery_begin_netdev_release(&ad.wr_iot_main_recovery,1));
  assert(wr_iot_physical_stop_main_complete(&ad,&main_dev,serial)==-EAGAIN);
  assert(wr_iot_main_recovery_finish_netdev_release(&ad.wr_iot_main_recovery,
    &main_dev,&ad.wr_iot_transition,1));
  ad.wr_iot_transition.shutdown_stage=2;
  ad.wr_iot_transition.mt_radio_off_stage=4;
  ad.wr_iot_transition.virtual_down_stage=2;
  ad.wr_iot_peer_table_owner.closed=1;
  assert(!wr_iot_physical_stop_main_complete(&ad,&main_dev,serial));
  assert(ad.wr_iot_physical_stop.phase==WR_PHYS_STOP_COMPLETE);
  assert(ad.wr_iot_physical_stop.completion_epoch==ad.wr_iot_transition.epoch);
  assert(!wr_iot_physical_stop_main_complete(&ad,&main_dev,serial));
  ad.wr_iot_peer_table_owner.poisoned=1;
  assert(wr_iot_physical_stop_main_complete(&ad,&main_dev,serial)==-EUCLEAN);
  ad.wr_iot_peer_table_owner.poisoned=0;
  ad.wr_iot_transition.epoch++;
  assert(wr_iot_physical_stop_main_complete(&ad,&main_dev,serial)==-EAGAIN);
  ad=alternative; /* independent schedule branch, not runtime rollback */
 }
'''
body=body[:a]+scenario+body[a:]
with tempfile.TemporaryDirectory(prefix='wr-stop-main-completion-') as d:
 root=Path(d);inc=root/'include';inc.mkdir()
 for p in here.glob('*.h'):shutil.copyfile(p,inc/p.name)
 for name in ('radio-transition.h','radio-transition-api.h'):
  radio=(inc/name).read_text().replace('virtual_down_stage,virtual_up_stage;', 'virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
  (inc/name).write_text(radio)
 c=root/'check.c';c.write_text(base['base']['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(inc),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual checked completion bridge: incomplete refs refuse, exact released Main plus stages/table/executor complete, duplicate read and stale epoch; hardware receipts injected')
