#include <assert.h>
#include <string.h>
#include "physical-stop-origin.h"
int main(void)
{
 int device;
 struct wr_iot_physical_stop_origin original={.main_generation=2,.main_open_token=3,
  .arm_epoch=5,.ticket_serial=7,.ticket_epoch=6,.completion_epoch=6,.valid=1};
 struct wr_iot_main_recovery_release_receipt receipt={.device=&device,.generation=2,
  .open_token=3,.close_serial=9,.ticket={.serial=7,.epoch=6,.operation=WR_RADIO_CLOSE},
  .completion_epoch=6,.valid=1};
 assert(wr_iot_physical_stop_origin_matches(&original,&receipt));
 assert(!wr_iot_physical_stop_origin_matches(0,&receipt));
 assert(!wr_iot_physical_stop_origin_matches(&original,0));
 for(unsigned i=0;i<14;i++){
  struct wr_iot_physical_stop_origin s=original;
  struct wr_iot_main_recovery_release_receipt r=receipt;
  switch(i){
   case 0:s.valid=0;break;case 1:r.valid=0;break;case 2:r.device=0;break;
   case 3:s.main_generation++;break;case 4:s.main_open_token++;break;
   case 5:s.ticket_serial++;break;case 6:s.ticket_epoch++;break;
   case 7:s.completion_epoch++;break;case 8:r.close_serial=0;break;
   case 9:r.ticket.operation=WR_RADIO_START;break;case 10:r.ticket.reset_kind=1;break;
   case 11:s.arm_epoch=s.ticket_epoch;break;case 12:s.main_generation=0;r.generation=0;break;
   case 13:s.completion_epoch=5;r.completion_epoch=5;break;
  }
  struct wr_iot_physical_stop_origin before=s;
  struct wr_iot_main_recovery_release_receipt old=r;
  assert(!wr_iot_physical_stop_origin_matches(&s,&r));
  assert(!memcmp(&s,&before,sizeof(s))&&!memcmp(&r,&old,sizeof(r)));
 }
 return 0;
}
