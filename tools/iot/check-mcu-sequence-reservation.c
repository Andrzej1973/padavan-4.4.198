#include "mcu-sequence-reservation.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 struct wr_iot_mcu_sequence_reservation s={0};unsigned int ids[15],i,j;
 /* Every ID remains private, not yet in ACK queue. Reservation must still
  * prevent duplicate allocation through an entire cursor wrap. */
 for(i=0;i<15;i++){
  ids[i]=wr_iot_mcu_sequence_reserve(&s);assert(ids[i]);
  for(j=0;j<i;j++)assert(ids[i]!=ids[j]);
 }
 assert(!wr_iot_mcu_sequence_reserve(&s));
 for(i=0;i<15;i++){
  assert(wr_iot_mcu_sequence_release(&s,ids[i]));
  assert(wr_iot_mcu_sequence_reserve(&s)==ids[i]);
 }
 assert(!wr_iot_mcu_sequence_release(&s,0)&&s.poisoned);
 assert(!wr_iot_mcu_sequence_reserve(&s));
 s=(struct wr_iot_mcu_sequence_reservation){0};
 assert(wr_iot_mcu_sequence_reserve(&s)==1);
 assert(wr_iot_mcu_sequence_release(&s,1));
 assert(!wr_iot_mcu_sequence_release(&s,1)&&s.poisoned);
 puts("PASS private pre-ACK reservations, exhaustion, release/reuse, invalid/double release quarantine; lifetime binding and freshness unproved");
 return 0;
}
