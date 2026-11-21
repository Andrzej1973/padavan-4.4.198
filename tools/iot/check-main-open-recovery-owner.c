#include "main-open-recovery-owner.h"
#include "pci-retirement-owner.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void set_owned(struct wr_iot_interface_ref *r,const void *dev,
                      enum wr_iot_ref_family family,unsigned long generation,
                      unsigned long token){
 wr_iot_ref_init(r,dev,generation);r->family=family;r->published=1;
 assert(wr_iot_ref_reserve(r,dev,generation,token));
 assert(wr_iot_ref_open_finish(r,dev,generation,token,1));
}
int main(void){
 struct wr_iot_interface_ref refs[2]={{0}};
 struct wr_iot_interface_ref budget_ref;
 struct wr_iot_radio_transition radio,budget_radio;
 struct wr_iot_radio_ticket ticket,copy,bad;
 struct wr_iot_main_recovery_owner owner,budget_owner;
 struct wr_iot_pci_retirement pci_owner;
 struct wr_child_teardown children;
 int main_dev,guest_dev,budget_dev;
 memset(&radio,0,sizeof(radio));wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_UNVERIFIED;
 set_owned(&refs[0],&main_dev,WR_REF_FAMILY_MAIN,4,7);
 wr_iot_ref_init(&refs[1],&guest_dev,5);refs[1].published=1;
 refs[1].family=WR_REF_FAMILY_MBSS;
 wr_iot_main_recovery_init(&owner);
 assert(!wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,0,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,0,WR_MAIN_QUEUE_NORMAL,0));
 radio.retiring=1;
 assert(!wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,
        WR_MAIN_QUEUE_RETIREMENT_CLOSE,0));
 assert(!wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_UNCERTAIN,1,1,
        WR_MAIN_QUEUE_RETIREMENT_CLOSE,1));
 assert(wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,
        WR_MAIN_QUEUE_RETIREMENT_CLOSE,1));
 wr_iot_main_recovery_init(&owner);
 radio.retiring=0;
 assert(!wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,
        WR_MAIN_QUEUE_RETIREMENT_CLOSE,1));
 assert(wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_complete(&owner,1));
 assert(!wr_iot_main_recovery_begin(&owner));
 assert(!wr_iot_main_recovery_rtnl_unavailable(&owner));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(!wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_rtnl_unavailable(&owner));
 assert(owner.phase==WR_MAIN_OWNER_RETAINED&&owner.attempts==0&&
        owner.deferred_owners==1&&!owner.module_pin_released);
 assert(!wr_iot_main_recovery_begin(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,2,0));
 assert(wr_iot_main_recovery_requeue(&owner,2,1));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_begin(&owner));
 assert(!wr_iot_main_recovery_rtnl_unavailable(&owner));
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,2)==
        WR_MAIN_RECOVERY_NONE);
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,1)==
        WR_MAIN_RECOVERY_BEGIN_CLOSE);
 assert(wr_iot_radio_begin_main_stop(&radio,1,&ticket));
 assert(ticket.operation==WR_RADIO_CLOSE);
 assert(wr_iot_ref_begin_close(&refs[0],&main_dev,4,7));
 assert(wr_iot_main_close_claim_preclose(&radio,&refs[0],refs,2,&ticket,1));
 bad=ticket;bad.serial++;
 assert(!wr_iot_main_recovery_bind_close(&owner,&refs[0],&radio,&bad));
 assert(wr_iot_main_recovery_bind_close(&owner,&refs[0],&radio,&ticket));
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,1)==
        WR_MAIN_RECOVERY_NONE); /* void preclose may still be in progress */
 assert(wr_iot_main_close_claim_void_preclose(&refs[0],&ticket));
 assert(!wr_iot_main_close_claim_void_preclose(&refs[0],&ticket));
 assert(wr_iot_main_close_finish_preclose(&refs[0],&ticket));
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,2)==
        WR_MAIN_RECOVERY_NONE); /* vendor count drift */
 set_owned(&refs[1],&guest_dev,WR_REF_FAMILY_MBSS,5,11);
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,1)==
        WR_MAIN_RECOVERY_NONE); /* registry drift */
 wr_iot_ref_init(&refs[1],&guest_dev,5);refs[1].published=1;
 refs[1].family=WR_REF_FAMILY_MBSS;
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,1)==
        WR_MAIN_RECOVERY_CONTINUE_CLOSE);
 assert(wr_iot_main_recovery_copy_close_ticket(&owner,&refs[0],&radio,
        refs,2,1,&copy)&&copy.serial==ticket.serial);
 assert(wr_iot_main_recovery_capture_physical_ticket(&owner,&radio,&refs[0],
   ticket.serial-1,4,7,&copy));
 assert(copy.serial==ticket.serial&&copy.epoch==ticket.epoch);
 assert(!wr_iot_main_recovery_capture_physical_ticket(&owner,&radio,&refs[0],
   ticket.serial-1,5,7,&copy));
 assert(!wr_iot_main_recovery_capture_physical_ticket(&owner,&radio,&refs[0],
   ticket.serial-1,4,8,&copy));
 assert(!wr_iot_main_recovery_capture_physical_ticket(&owner,&radio,&refs[0],
   ticket.serial,4,7,&copy));
 {struct wr_iot_interface_ref stale=refs[0];stale.generation++;
  assert(!wr_iot_main_recovery_capture_physical_ticket(&owner,&radio,&stale,
    ticket.serial-1,4,7,&copy));
 }
 {struct wr_iot_main_recovery_owner changed;
  struct wr_iot_radio_transition altered;
  struct wr_iot_radio_ticket sentinel={0};
  unsigned fault;
  sentinel.serial=12345;
  for(fault=0;fault<8;fault++){
   changed=owner;altered=radio;copy=sentinel;
   switch(fault){
    case 0:changed.schedule_recorded=0;break;
    case 1:changed.completed=1;break;
    case 2:changed.stop_requested=1;break;
    case 3:changed.source=WR_MAIN_RECOVERY_CLOSE_UNCERTAIN;break;
    case 4:changed.close_ticket_valid=0;break;
    case 5:altered.retiring=1;break;
    case 6:altered.pm_suspending=1;break;
    case 7:altered.reset_pending=1;break;
   }
   assert(!wr_iot_main_recovery_capture_physical_ticket(&changed,&altered,
     &refs[0],ticket.serial-1,4,7,&copy));
   assert(copy.serial==sentinel.serial); /* refused read cannot publish ticket */
  }
 }

 assert(!wr_iot_main_recovery_mark_completed(&owner,&refs[0]));
 assert(!wr_iot_main_close_note_checked_down(&refs[0],&ticket,1,0));
 assert(wr_iot_main_close_note_checked_down(&refs[0],&ticket,1,1));
 {int release=0;
  assert(wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,4,7,
                                  &ticket,1,1,&release)&&release);
 }
 assert(wr_iot_main_recovery_mark_completed(&owner,&refs[0]));
 /* The callback releases its own module pin before it can be joined. */
 assert(!wr_iot_main_recovery_mark_module_pin_released(&owner,0,1));
 assert(!wr_iot_main_recovery_mark_module_pin_released(&owner,1,0));
 assert(wr_iot_main_recovery_mark_module_pin_released(&owner,1,1));
 assert(!wr_iot_main_recovery_mark_module_pin_released(&owner,1,1));
 assert(owner.phase==WR_MAIN_OWNER_RUNNING&&owner.module_pin_released);
 assert(!wr_iot_main_recovery_complete(&owner,0));
 assert(!owner.last_release.valid);
 assert(wr_iot_main_recovery_begin_netdev_release(&owner,1));
 assert(!owner.last_release.valid);
 assert(!wr_iot_main_recovery_complete(&owner,1));
 assert(wr_iot_main_recovery_finish_netdev_release(&owner,&main_dev,&radio,1));
 assert(owner.phase==WR_MAIN_OWNER_IDLE&&!owner.deferred_owners);
 assert(owner.last_release.valid&&owner.last_release.device==&main_dev&&
        owner.last_release.generation==4&&owner.last_release.open_token==7&&
        owner.last_release.close_serial==refs[0].close_serial&&
        owner.last_release.ticket.serial==ticket.serial&&
        owner.last_release.ticket.epoch==ticket.epoch);

 assert(wr_iot_main_recovery_release_current(&owner,&radio,&refs[0],0));
 assert(wr_iot_main_recovery_release_for_ticket(&owner,&radio,&refs[0],0,
   &ticket,4,7));
 {struct wr_iot_radio_ticket other=ticket;
  other.serial++;
  assert(!wr_iot_main_recovery_release_for_ticket(&owner,&radio,&refs[0],0,
    &other,4,7));
  other=ticket;other.epoch++;
  assert(!wr_iot_main_recovery_release_for_ticket(&owner,&radio,&refs[0],0,
    &other,4,7));
  other=ticket;other.operation=WR_RADIO_BSS_CLOSE;
  assert(!wr_iot_main_recovery_release_for_ticket(&owner,&radio,&refs[0],0,
    &other,4,7));
  assert(!wr_iot_main_recovery_release_for_ticket(&owner,&radio,&refs[0],0,
    &ticket,5,7));
  assert(!wr_iot_main_recovery_release_for_ticket(&owner,&radio,&refs[0],0,
    &ticket,4,8));
 }

 {struct wr_iot_radio_transition changed=radio;
  struct wr_iot_interface_ref stale=refs[0];
  assert(!wr_iot_main_recovery_release_current(&owner,&radio,&refs[0],1));
  changed.epoch++;
  assert(!wr_iot_main_recovery_release_current(&owner,&changed,&refs[0],0));
  changed=radio;changed.serial++;
  assert(!wr_iot_main_recovery_release_current(&owner,&changed,&refs[0],0));
  changed=radio;changed.active_tx=1;
  assert(!wr_iot_main_recovery_release_current(&owner,&changed,&refs[0],0));
  stale.generation++;
  assert(!wr_iot_main_recovery_release_current(&owner,&radio,&stale,0));
  stale=refs[0];stale.last_token++;
  assert(!wr_iot_main_recovery_release_current(&owner,&radio,&stale,0));
  stale=refs[0];stale.removing=1;
  assert(!wr_iot_main_recovery_release_current(&owner,&radio,&stale,0));
  stale=refs[0];stale.published=0;
  assert(!wr_iot_main_recovery_release_current(&owner,&radio,&stale,0));
  changed=radio;changed.retiring=1;
  assert(!wr_iot_main_recovery_release_current(&owner,&changed,&refs[0],0));
  changed=radio;changed.reset_pending=1;
  assert(!wr_iot_main_recovery_release_current(&owner,&changed,&refs[0],0));
 }

 /* An uncertain main open never authorizes an unproven virtual DOWN. */
 wr_iot_main_recovery_init(&owner);
 assert(!owner.last_release.valid);
 refs[0].phase=WR_REF_UNCERTAIN_OPEN;refs[0].last_token=8;
 assert(wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_UNCERTAIN,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_begin(&owner));
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,1)==
        WR_MAIN_RECOVERY_RECONCILE);
 assert(!wr_iot_main_recovery_mark_completed(&owner,&refs[0]));
 assert(wr_iot_main_recovery_retain(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,2,1));
 assert(!wr_iot_main_recovery_complete(&owner,1));

 /* A bounded acquired-open retry retains the same owner and references. */
 wr_iot_main_recovery_init(&owner);
 set_owned(&refs[0],&main_dev,WR_REF_FAMILY_MAIN,9,10);
 wr_iot_radio_transition_init(&budget_radio);
 set_owned(&budget_ref,&budget_dev,WR_REF_FAMILY_MAIN,1,1);
 wr_iot_main_recovery_init(&budget_owner);
 assert(wr_iot_main_recovery_queue(&budget_owner,&budget_radio,&budget_ref,
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_schedule_result(&budget_owner,0));
 assert(!wr_iot_main_recovery_schedule_result(&budget_owner,0));
 assert(budget_owner.failed_submissions==1);
 assert(wr_iot_main_recovery_requeue(&budget_owner,2,1));
 assert(!wr_iot_main_recovery_schedule_result(&budget_owner,0));
 assert(budget_owner.failed_submissions==2);
 assert(!wr_iot_main_recovery_requeue(&budget_owner,2,1));
 assert(wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_schedule_result(&owner,0));
 assert(!wr_iot_main_recovery_schedule_result(&owner,0));
 assert(owner.failed_submissions==1);
 assert(owner.phase==WR_MAIN_OWNER_RETAINED&&owner.deferred_owners==1);
 assert(!wr_iot_main_recovery_begin(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,2,0));
 assert(wr_iot_main_recovery_requeue(&owner,3,1));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_begin(&owner));
 refs[0].generation++;
 assert(wr_iot_main_recovery_action(&owner,&refs[0],&radio,refs,2,1)==
        WR_MAIN_RECOVERY_NONE);
 refs[0].generation--;
 assert(wr_iot_main_recovery_retain(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,2,0));
 assert(owner.phase==WR_MAIN_OWNER_RETAINED);
 assert(wr_iot_main_recovery_requeue(&owner,3,1));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_begin(&owner));
 assert(wr_iot_main_recovery_retain(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,3,1));
 assert(wr_iot_main_recovery_request_stop(&owner));
 assert(owner.phase==WR_MAIN_OWNER_STOPPING);
 assert(!wr_iot_main_recovery_requeue(&owner,3,1));
 assert(!wr_iot_main_recovery_complete(&owner,1));
 wr_iot_main_recovery_init(&owner);
 assert(!wr_iot_main_recovery_request_stop(&owner));
 assert(wr_iot_main_recovery_queue(&owner,&radio,&refs[0],
        WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_request_stop(&owner));
 assert(owner.phase==WR_MAIN_OWNER_STOPPING);
 assert(!wr_iot_main_recovery_begin(&owner));
 assert(!wr_iot_main_recovery_complete(&owner,1));
 wr_iot_pci_retirement_init(&pci_owner);
 wr_child_teardown_init(&children);
 radio.retiring=1;
 assert(wr_iot_pci_retirement_begin(&pci_owner,&radio,1));
 assert(wr_iot_pci_retirement_drain_begin(&pci_owner));
 assert(!wr_iot_pci_retirement_drain_complete(&pci_owner,1,
                                              owner.deferred_owners));
 wr_iot_main_recovery_init(&owner);
 assert(wr_iot_pci_retirement_drain_complete(&pci_owner,1,0));
 assert(wr_iot_pci_retirement_stop_requested(&pci_owner,1));
 assert(wr_iot_pci_retirement_work_joined(&pci_owner,1));
 children.phase=WR_CHILD_DONE;
 assert(!wr_iot_pci_retirement_children_done(&pci_owner,&children,1));
 {
  struct wr_iot_radio_transition retiring_radio;
  struct wr_iot_interface_ref retiring_refs[2]={{0}};
  struct wr_iot_main_recovery_owner retiring_owner;
  struct wr_iot_radio_ticket retiring_close;
  int retiring_main;
  wr_iot_radio_transition_init(&retiring_radio);
  retiring_radio.phase=WR_RADIO_UNVERIFIED;
  set_owned(&retiring_refs[0],&retiring_main,WR_REF_FAMILY_MAIN,9,11);
  wr_iot_main_recovery_init(&retiring_owner);
  wr_iot_radio_retire(&retiring_radio);
  assert(wr_iot_main_recovery_queue(&retiring_owner,&retiring_radio,
    &retiring_refs[0],WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,
    WR_MAIN_QUEUE_RETIREMENT_CLOSE,1));
  assert(wr_iot_main_recovery_schedule_result(&retiring_owner,1));
  assert(wr_iot_main_recovery_begin(&retiring_owner));
  assert(wr_iot_main_recovery_action(&retiring_owner,&retiring_refs[0],
    &retiring_radio,retiring_refs,2,1)==WR_MAIN_RECOVERY_BEGIN_CLOSE);
  assert(wr_iot_radio_begin_main_stop(&retiring_radio,1,&retiring_close));
  assert(retiring_close.operation==WR_RADIO_CLOSE);
  assert(wr_iot_ref_begin_close(&retiring_refs[0],&retiring_main,9,11));
  assert(wr_iot_main_close_claim_preclose(&retiring_radio,
    &retiring_refs[0],retiring_refs,2,&retiring_close,1));
  assert(wr_iot_main_recovery_bind_close(&retiring_owner,&retiring_refs[0],
    &retiring_radio,&retiring_close));
  assert(retiring_owner.close_ticket_valid);
 }
 puts("PASS main failed-open recovery owner: acquired close receipt, exact identity, uncertain reconciliation, and joined lifetime gates");
 return 0;
}
