#include <assert.h>
#include <stdio.h>
#include "mcu-config-result.h"
int main(void)
{
 unsigned char payload[32]={0};unsigned i,len;
 assert(wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0e,payload,32,44,44,12));
 for(i=20;i<24;i++){
  payload[i]=1;assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0e,payload,32,44,44,12));payload[i]=0;
 }
 for(len=0;len<64;len++)if(len!=32)
  assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0e,payload,len,44,44,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0e,0,0xed,0x0e,payload,32,44,44,12));
 assert(!wr_iot_config_multi_write_success(0xec,0x0e,1,0xed,0x0e,payload,32,44,44,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0f,1,0xed,0x0e,payload,32,44,44,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xec,0x0e,payload,32,44,44,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0f,payload,32,44,44,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0e,NULL,32,44,44,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0e,payload,32,43,44,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0e,payload,32,44,45,12));
 assert(!wr_iot_config_multi_write_success(0xed,0x0e,1,0xed,0x0e,payload,32,44,44,~0U));
 puts("PASS config MAC-write result: exact envelope/set direction, all status bytes, length/null/overflow refusal; pure parser only");
 return 0;
}
