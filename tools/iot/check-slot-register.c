#include <assert.h>
#include <stdio.h>
#include "mcu-config-timing-pending.h"
#include "mac/mac_mt/wf_tmac.h"
int main(void)
{
 unsigned char tuple[8]={9,10,2,0,84,0,0,0};
 unsigned value=0;
 assert(wr_iot_config_slot_register(tuple,8,&value));
 assert(value==0x090a0854U);
 tuple[0]=127;tuple[1]=127;tuple[2]=31;tuple[4]=255;tuple[5]=1;
 assert(wr_iot_config_slot_register(tuple,8,&value)&&value==0x7f7f7dffU);
 for(unsigned i=0;i<8;i++){
  unsigned char bad[8]={9,10,2,0,84,0,0,0};
  unsigned char invalid[8]={128,128,32,1,0,2,1,1};
  if(i==4)continue; /* Every low EIFS byte is representable. */
  bad[i]=invalid[i];value=0x12345678;
  assert(!wr_iot_config_slot_register(bad,8,&value)&&value==0x12345678);
 }
 for(unsigned n=0;n<12;n++)if(n!=8){
  value=42;assert(!wr_iot_config_slot_register(tuple,n,&value)&&value==42);
 }
 assert(!wr_iot_config_slot_register(NULL,8,&value));
 assert(!wr_iot_config_slot_register(tuple,8,NULL));
 assert(TMAC_ICR==0x216a4U);
 for(unsigned i=0;i<512;i++){
  unsigned char sample[8]={(unsigned char)(i%128),(unsigned char)((i*3)%128),
   (unsigned char)(i%32),0,(unsigned char)i,(unsigned char)(i>>8),0,0};
  assert(wr_iot_config_slot_register(sample,8,&value));
  assert(value==(ICR_EIFS_TIME(i)|ICR_RIFS_TIME(sample[2])|
                 ICR_SIFS_TIME(sample[1])|ICR_SLOT_TIME(sample[0])));
  assert(GET_ICR_EIFS_TIME(value)==i&&GET_ICR_RIFS_TIME(value)==sample[2]&&
         GET_ICR_SIFS_TIME(value)==sample[1]&&GET_ICR_SLOT_TIME(value)==sample[0]);
 }
 puts("PASS SDK slot register encoding: exact fields, maxima, range/reserved/length/null refusal, output preservation; no execution proof");
}
