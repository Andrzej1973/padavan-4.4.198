#include "aux-close-claim.h"
#include <assert.h>
#include <string.h>
int main(void){
 struct wr_iot_interface_ref slots[3];
 struct wr_iot_radio_transition radio;
 struct wr_iot_radio_ticket ticket;
 unsigned long generation;int devices[3];
 for(int family=WR_REF_FAMILY_APCLI;family<=WR_REF_FAMILY_MONITOR;family++){
  memset(slots,0,sizeof slots);
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  for(int i=0;i<2;i++){
   wr_iot_ref_init(&slots[i],&devices[i],i+1);slots[i].published=1;
   slots[i].phase=WR_REF_OWNED;slots[i].last_token=i+1;
  }
  slots[0].family=WR_REF_FAMILY_MAIN;slots[1].family=(enum wr_iot_ref_family)family;
  assert(wr_iot_registry_begin_remove(&slots[1],&devices[1],2));
  assert(!wr_iot_registry_count_matches(slots,3,2)); /* Old path rejects. */
  slots[0].removing=1;
  assert(!wr_iot_aux_close_reserve(&radio,slots,3,&devices[1],slots[1].family,2,&ticket,&generation));
  slots[0].removing=0;slots[2]=slots[1];
  assert(!wr_iot_aux_close_reserve(&radio,slots,3,&devices[1],slots[1].family,3,&ticket,&generation));
  memset(&slots[2],0,sizeof slots[2]);slots[1].removal_stage=1;
  assert(!wr_iot_aux_close_reserve(&radio,slots,3,&devices[1],slots[1].family,2,&ticket,&generation));
  slots[1].removal_stage=0;
  assert(!wr_iot_aux_close_reserve(&radio,slots,3,&devices[1],slots[1].family,3,&ticket,&generation));
  assert(!radio.busy&&slots[1].phase==WR_REF_OWNED);
  assert(wr_iot_aux_close_reserve(&radio,slots,3,&devices[1],slots[1].family,2,&ticket,&generation));
  assert(generation==2&&slots[1].removing&&slots[1].phase==WR_REF_CLOSING);
  assert(slots[1].close_serial==ticket.serial);
  assert(!wr_iot_aux_close_reserve(&radio,slots,3,&devices[1],slots[1].family,2,&ticket,&generation));
 }
 return 0;
}
