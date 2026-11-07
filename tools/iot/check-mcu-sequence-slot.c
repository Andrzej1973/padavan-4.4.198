#include "mcu-sequence-slot.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 unsigned int mask,previous;
 for(mask=0;mask<32768;mask++)for(previous=0;previous<=15;previous++){
  unsigned int occupied=mask<<1,slot=wr_iot_mcu_sequence_slot(previous,occupied);
  if(mask==32767)assert(slot==0);
  else {
   unsigned int n=previous,steps=0;
   assert(slot>=1&&slot<=15&&!(occupied&(1u<<slot)));
   do {n=n>=15?1:n+1;steps++;}while(occupied&(1u<<n));
   assert(steps<=15&&slot==n);
  }
 }
 assert(wr_iot_mcu_sequence_slot(~0u,0)==1);
 puts("PASS all 32768 occupancy masks and 16 cursors; exhaustion returns zero; reservation/freshness unproved");
 return 0;
}
