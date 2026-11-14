#include <assert.h>
#include <stdio.h>
#include "physical-stop-lifetime.h"
int main(void){
 struct wr_iot_radio_transition radio;wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 for(unsigned fault=0;fault<10;fault++){
  struct wr_iot_radio_transition observed=radio;
  struct wr_iot_physical_stop_lifetime s={0};
  if(fault==1)observed.retiring=1;
  if(fault==2)observed.busy=1;
  if(fault==3)observed.reset_pending=1;
  if(fault==4)observed.pm_suspending=1;
  if(fault==5)observed.pm_suspended=1;
  if(fault==6)observed.exhausted=1;
  if(fault==7)observed.phase=WR_RADIO_FAULT;
  if(fault==8)observed.main_ready=0;
  if(fault==9)observed.active_tx=1;
  assert(wr_iot_physical_stop_lifetime_begin(&s,&observed)==(fault?0:1));
  if(fault){assert(!s.serial&&!s.active);continue;}
  assert(wr_iot_physical_stop_lifetime_blocks(&s));
  assert(!wr_iot_physical_stop_lifetime_begin(&s,&radio));
  assert(!wr_iot_physical_stop_lifetime_end(&s,2,1,1));
  assert(!wr_iot_physical_stop_lifetime_end(&s,1,0,1));
  assert(!wr_iot_physical_stop_lifetime_end(&s,1,1,0));
  assert(s.active&&wr_iot_physical_stop_lifetime_end(&s,1,1,1));
  assert(!wr_iot_physical_stop_lifetime_blocks(&s));
  assert(!wr_iot_physical_stop_lifetime_end(&s,1,1,1));
  assert(wr_iot_physical_stop_lifetime_begin(&s,&radio)==2);
  assert(!wr_iot_physical_stop_lifetime_end(&s,1,1,1));
 }
 struct wr_iot_physical_stop_lifetime exhausted={.serial=~0UL};
 assert(!wr_iot_physical_stop_lifetime_begin(&exhausted,&radio));
 {
  int dev;
  struct wr_iot_main_recovery_owner owner;
  struct wr_iot_interface_ref record;
  struct wr_iot_physical_stop_lifetime s={0};
  wr_iot_main_recovery_init(&owner);
  wr_iot_ref_init(&record,&dev,9);record.family=WR_REF_FAMILY_MAIN;
  record.published=1;
  assert(wr_iot_ref_reserve(&record,&dev,9,17));
  assert(wr_iot_ref_open_finish(&record,&dev,9,17,1));
  {struct wr_iot_radio_transition exhausted=radio;
   exhausted.serial=~0UL;
   assert(!wr_iot_physical_stop_lifetime_begin_main(&s,&exhausted,&owner,&record,&dev));
   assert(!s.active&&!s.serial);
   exhausted=radio;exhausted.epoch=~0UL-1UL;
   assert(!wr_iot_physical_stop_lifetime_begin_main(&s,&exhausted,&owner,&record,&dev));
   assert(!s.active&&!s.serial);
  }
  assert(wr_iot_physical_stop_lifetime_begin_main(&s,&radio,&owner,&record,&dev));
  assert(s.main_device==&dev&&s.main_generation==9&&s.main_open_token==17&&
         s.arm_radio_serial==radio.serial);
  {struct wr_iot_radio_ticket ticket,captured={0};
   assert(wr_iot_radio_begin_main_stop(&radio,1,&ticket));
   assert(wr_iot_ref_begin_close(&record,&dev,9,17));
   assert(wr_iot_main_close_claim_preclose(&radio,&record,&record,1,&ticket,1));
   assert(wr_iot_main_close_claim_void_preclose(&record,&ticket));
   assert(wr_iot_main_close_finish_preclose(&record,&ticket));
   assert(wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
     &ticket,1,1,1,WR_MAIN_QUEUE_NORMAL,0));
   assert(wr_iot_main_recovery_schedule_result(&owner,1));
   assert(wr_iot_physical_stop_lifetime_capture_main(&s,s.serial,&owner,
     &radio,&record,&captured));
   assert(captured.serial==ticket.serial);
   assert(!wr_iot_physical_stop_lifetime_capture_main(&s,s.serial+1,&owner,
     &radio,&record,&captured));
   s.main_open_token++;
   assert(!wr_iot_physical_stop_lifetime_capture_main(&s,s.serial,&owner,
     &radio,&record,&captured));
   s.main_open_token--;
   assert(!wr_iot_physical_stop_lifetime_main_released(&s,s.serial,&owner,
     &radio,&record,0));
   assert(wr_iot_main_recovery_begin(&owner));
   assert(wr_iot_main_close_note_checked_down(&record,&ticket,1,1));
   {int release=0;
    assert(wr_iot_main_stop_complete(&radio,&record,&dev,9,17,&ticket,1,1,&release));
    assert(release);
   }
   assert(wr_iot_main_recovery_mark_completed(&owner,&record));
   assert(wr_iot_main_recovery_mark_module_pin_released(&owner,1,1));
   assert(wr_iot_main_recovery_begin_netdev_release(&owner,1));
   assert(!wr_iot_physical_stop_lifetime_main_released(&s,s.serial,&owner,
     &radio,&record,0));
   assert(wr_iot_main_recovery_finish_netdev_release(&owner,&dev,&radio,1));
   assert(wr_iot_physical_stop_lifetime_main_released(&s,s.serial,&owner,
     &radio,&record,0));
   assert(!wr_iot_physical_stop_lifetime_main_released(&s,s.serial,&owner,
     &radio,&record,1));
   s.main_ticket.serial++;
   assert(!wr_iot_physical_stop_lifetime_main_released(&s,s.serial,&owner,
     &radio,&record,0));
   assert(!wr_iot_physical_stop_lifetime_capture_released_main(&s,s.serial,
     &owner,&radio,&record,0)); /* never replace an existing different ticket */
   s.main_ticket_valid=0; /* simulate first QUERY after already-completed work */
   s.main_open_token++;
   assert(!wr_iot_physical_stop_lifetime_capture_released_main(&s,s.serial,
     &owner,&radio,&record,0));
   assert(!s.main_ticket_valid);
   s.main_open_token--;
   assert(wr_iot_physical_stop_lifetime_capture_released_main(&s,s.serial,
     &owner,&radio,&record,0));
   assert(wr_iot_physical_stop_lifetime_main_released(&s,s.serial,&owner,
     &radio,&record,0));
  }
  assert(wr_iot_physical_stop_lifetime_end(&s,s.serial,1,1));
  assert(!s.main_device&&!s.main_generation&&!s.main_open_token);
  record.removing=1;
  assert(!wr_iot_physical_stop_lifetime_begin_main(&s,&radio,&owner,&record,&dev));
  assert(!s.active&&!s.main_device);
 }
 puts("PASS transition-lock physical stop lifetime: retirement/reset/PM/uncertain refusal, serial-bound fence retained through record and reference return, duplicate/stale refusal; actual binding pending");
}
