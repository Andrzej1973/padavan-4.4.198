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
 s=(struct wr_iot_mcu_sequence_reservation){0};
 unsigned int timed_out=wr_iot_mcu_sequence_reserve(&s);assert(timed_out==1);
 assert(wr_iot_mcu_sequence_finish(&s,timed_out,1));
 assert(!s.occupied&&(s.quarantined&(1u<<timed_out)));
 for(i=0;i<14;i++){
  ids[i]=wr_iot_mcu_sequence_reserve(&s);
  assert(ids[i]&&ids[i]!=timed_out);
 }
 assert(!wr_iot_mcu_sequence_reserve(&s));
 for(i=0;i<14;i++)assert(wr_iot_mcu_sequence_finish(&s,ids[i],0));
 for(i=0;i<30;i++){
  unsigned int id=wr_iot_mcu_sequence_reserve(&s);assert(id&&id!=timed_out);
  assert(wr_iot_mcu_sequence_finish(&s,id,0));
 }
 puts("PASS reservation/release, timeout ID quarantine across wrap, exhaustion and invalid/double release; firmware epoch unproved");
 return 0;
}
