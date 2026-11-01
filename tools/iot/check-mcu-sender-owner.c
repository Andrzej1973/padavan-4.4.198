#include "mcu-sender-owner.h"
#include <assert.h>
int main(void){struct wr_iot_mcu_sender_owner s;
 wr_iot_mcu_sender_init(&s);assert(!wr_iot_mcu_sender_drained(&s));assert(wr_iot_mcu_sender_enter(&s));
 assert(!wr_iot_mcu_sender_close(&s,0));assert(wr_iot_mcu_sender_close(&s,7));
 assert(!wr_iot_mcu_sender_enter(&s));assert(!wr_iot_mcu_sender_drained(&s));assert(!wr_iot_mcu_sender_release_claim(&s));assert(!wr_iot_mcu_sender_off_begin(&s,7));
 assert(wr_iot_mcu_sender_leave(&s));assert(wr_iot_mcu_sender_drained(&s));assert(!wr_iot_mcu_sender_off_begin(&s,8));
 assert(wr_iot_mcu_sender_off_begin(&s,7));assert(!wr_iot_mcu_sender_drained(&s));assert(!wr_iot_mcu_sender_release_claim(&s));assert(!wr_iot_mcu_sender_off_begin(&s,7));
 assert(!wr_iot_mcu_sender_off_finish(&s,8,1)&&s.off_active);
 assert(wr_iot_mcu_sender_off_finish(&s,7,0));assert(s.uncertain&&!wr_iot_mcu_sender_drained(&s));assert(!wr_iot_mcu_sender_release_claim(&s));
 assert(!wr_iot_mcu_sender_off_begin(&s,7));assert(!wr_iot_mcu_sender_close(&s,8));
 wr_iot_mcu_sender_init(&s);assert(wr_iot_mcu_sender_close(&s,9));
 assert(wr_iot_mcu_sender_off_begin(&s,9));assert(wr_iot_mcu_sender_off_finish(&s,9,1));
 assert(s.off_done&&wr_iot_mcu_sender_drained(&s)&&!wr_iot_mcu_sender_off_begin(&s,9));
 assert(!wr_iot_mcu_sender_off_finish(&s,9,1));
 wr_iot_mcu_sender_init(&s);assert(wr_iot_mcu_sender_close(&s,11));
 assert(wr_iot_mcu_sender_off_begin(&s,11));
 assert(!wr_iot_mcu_sender_leave(&s)&&s.poisoned);
 assert(!wr_iot_mcu_sender_off_finish(&s,11,1)&&!s.off_done&&!wr_iot_mcu_sender_drained(&s));
 wr_iot_mcu_sender_init(&s);s.inflight=~0U;assert(!wr_iot_mcu_sender_enter(&s)&&s.poisoned);
 wr_iot_mcu_sender_init(&s);assert(!wr_iot_mcu_sender_leave(&s)&&s.poisoned);
 wr_iot_mcu_sender_init(&s);assert(wr_iot_mcu_sender_enter(&s));assert(wr_iot_mcu_sender_enter(&s));
 assert(wr_iot_mcu_sender_close(&s,12));assert(wr_iot_mcu_sender_leave(&s));
 assert(!wr_iot_mcu_sender_drained(&s));assert(wr_iot_mcu_sender_leave(&s));
 assert(wr_iot_mcu_sender_drained(&s));
 assert(wr_iot_mcu_sender_release_claim(&s));
 assert(!wr_iot_mcu_sender_release_claim(&s));
 assert(!wr_iot_mcu_sender_off_begin(&s,12));
 assert(!wr_iot_mcu_sender_enter(&s));assert(!wr_iot_mcu_sender_close(&s,12));
 return 0;}
