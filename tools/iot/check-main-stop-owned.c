#include "main-stop-owned.h"
#include <assert.h>
#include <stdio.h>
static void record_checked_down(struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *record,
 const struct wr_iot_interface_ref *slots,unsigned int slot_count,
 const struct wr_iot_radio_ticket *ticket,unsigned int count,
 int physical_verified){
 assert(wr_iot_main_close_claim_preclose(radio,record,slots,slot_count,ticket,count));
 assert(!wr_iot_main_close_claim_preclose(radio,record,slots,slot_count,ticket,count));
 assert(!wr_iot_main_close_note_checked_down(record,ticket,1,physical_verified));
 assert(!wr_iot_main_close_finish_preclose(record,ticket));
 assert(wr_iot_main_close_claim_void_preclose(record,ticket));
 assert(!wr_iot_main_close_claim_void_preclose(record,ticket));
 assert(wr_iot_main_close_finish_preclose(record,ticket));
 assert(!wr_iot_main_close_finish_preclose(record,ticket));
 if(ticket->operation==WR_RADIO_CLOSE)
  assert(!wr_iot_main_close_note_checked_down(record,ticket,1,0));
 assert(wr_iot_main_close_note_checked_down(record,ticket,1,physical_verified));
 assert(!wr_iot_main_close_note_checked_down(record,ticket,1,physical_verified));
}
int main(void)
{
 struct wr_iot_radio_transition radio;
 struct wr_iot_radio_ticket open,stop;
 struct wr_iot_interface_ref refs[2]={{0}};
 int main_dev=0,iot_dev=0;
 unsigned long epoch;
 unsigned long wait_serial=99;
 wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 wr_iot_ref_init(&refs[0],&main_dev,1);refs[0].published=1;
 refs[0].family=WR_REF_FAMILY_MAIN;
 wr_iot_ref_init(&refs[1],&iot_dev,2);refs[1].published=1;
 epoch=radio.epoch;
 assert(!wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,1,&stop));
 assert(radio.epoch==epoch&&!radio.main_inhibited);
 assert(wr_iot_main_stop_request(&radio,refs,2,&main_dev,&main_dev,1,
  &stop,&wait_serial)==WR_MAIN_STOP_INVALID&&wait_serial==99);
 assert(wr_iot_ref_reserve(&refs[0],&main_dev,1,1));
 assert(wr_iot_ref_open_finish(&refs[0],&main_dev,1,1,1));
 assert(!wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,2,&stop));
 assert(radio.epoch==epoch+1&&radio.main_inhibited&&!radio.main_ready);
 assert(wr_iot_main_stop_request(&radio,refs,2,&main_dev,&main_dev,2,
  &stop,&wait_serial)==WR_MAIN_STOP_NEEDS_RECOVERY&&wait_serial==0);
 assert(!wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,2,&stop));
 assert(radio.epoch==epoch+1);
 wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
 epoch=radio.epoch;
 assert(wr_iot_ref_reserve(&refs[1],&iot_dev,2,1));
 assert(!wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,1,&stop));
 assert(radio.epoch==epoch+1&&radio.main_inhibited&&!radio.main_ready);
 assert(!wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,1,&stop));
 assert(radio.epoch==epoch+1);
 assert(wr_iot_ref_open_finish(&refs[1],&iot_dev,2,1,1));
 wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
 epoch=radio.epoch;
 assert(!wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&iot_dev,2,&stop));
 assert(radio.epoch==epoch&&!radio.main_inhibited);
 assert(wr_iot_radio_begin(&radio,radio.epoch,WR_RADIO_BSS_OPEN,&open));
 assert(wr_iot_main_stop_request(&radio,refs,2,&main_dev,&main_dev,2,
  &stop,&wait_serial)==WR_MAIN_STOP_WAIT_TICKET&&wait_serial==open.serial);
 assert(radio.main_inhibited&&!radio.main_ready);
 epoch=radio.epoch;
 assert(!wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,2,&stop));
 assert(radio.epoch==epoch);
 assert(wr_iot_radio_finish_unverified(&radio,&open));
 assert(wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,2,&stop));
 assert(stop.operation==WR_RADIO_BSS_CLOSE);
 assert(wr_iot_ref_begin_close(&refs[0],&main_dev,1,1));
 {int release=-1;
  assert(!wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,1,1,
   &stop,1,0,&release)); /* no checked-DOWN receipt */
  assert(!wr_iot_main_close_claim_preclose(&radio,&refs[0],refs,2,&stop,1));
  record_checked_down(&radio,&refs[0],refs,2,&stop,2,0);
  assert(wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,1,1,
   &stop,1,0,&release));
  assert(release==1&&refs[0].phase==WR_REF_IDLE&&refs[0].close_stage==4U);
 }
 /* Last physical close needs actual verification before releasing the pin. */
 wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;
 wr_iot_ref_init(&refs[0],&main_dev,3);refs[0].published=1;
 refs[0].family=WR_REF_FAMILY_MAIN;
 wr_iot_ref_init(&refs[1],&iot_dev,4);refs[1].published=1;
 assert(wr_iot_ref_reserve(&refs[0],&main_dev,3,1));
 assert(wr_iot_ref_open_finish(&refs[0],&main_dev,3,1,1));
 assert(wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,1,&stop));
 assert(stop.operation==WR_RADIO_CLOSE);
 assert(wr_iot_ref_begin_close(&refs[0],&main_dev,3,1));
 {int release=-1;
  refs[1].phase=WR_REF_RESERVED;
  assert(!wr_iot_main_close_claim_preclose(&radio,&refs[0],refs,2,&stop,1));
  refs[1].phase=WR_REF_IDLE;
  record_checked_down(&radio,&refs[0],refs,2,&stop,1,1);
  refs[0].close_serial++;
  assert(!wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,3,1,
   &stop,1,1,&release)); /* stale receipt */
  refs[0].close_serial--;
  refs[0].close_vendor_count=2;
  assert(!wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,3,1,
   &stop,1,1,&release)); /* wrong CLOSE cardinality */
  refs[0].close_vendor_count=1;
  refs[0].close_epoch++;
  assert(!wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,3,1,
   &stop,1,1,&release)); /* wrong ticket epoch */
  refs[0].close_epoch--;
  assert(!wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,3,1,
   &stop,1,0,&release));
  assert(release==0&&refs[0].phase==WR_REF_CLOSING&&
   radio.busy==WR_RADIO_CLOSE&&radio.serial==stop.serial);
  assert(!wr_iot_ref_reserve(&refs[0],&main_dev,3,2));
  assert(!wr_iot_radio_begin(&radio,radio.epoch,WR_RADIO_VERIFY,&open));
  assert(wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,3,1,
   &stop,1,1,&release));
  assert(release==1&&refs[0].phase==WR_REF_IDLE&&
   refs[0].close_stage==4U&&radio.busy==0);
 }
 wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;
 wr_iot_ref_init(&refs[0],&main_dev,5);refs[0].published=1;
 refs[0].family=WR_REF_FAMILY_MAIN;
 assert(wr_iot_ref_reserve(&refs[0],&main_dev,5,1));
 assert(wr_iot_ref_open_finish(&refs[0],&main_dev,5,1,1));
 assert(wr_iot_main_stop_owned(&radio,refs,2,&main_dev,&main_dev,1,&stop));
 assert(wr_iot_ref_begin_close(&refs[0],&main_dev,5,1));
 {int release=-1;
  record_checked_down(&radio,&refs[0],refs,2,&stop,1,1);
  assert(wr_iot_main_stop_complete(&radio,&refs[0],&main_dev,5,1,
   &stop,1,1,&release));
  assert(release==1&&refs[0].phase==WR_REF_IDLE);
 }
 puts("PASS main-stop owner: all references matched before ticket claim");
 return 0;
}
