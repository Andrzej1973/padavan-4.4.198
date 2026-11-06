#include <assert.h>
#include <stdio.h>
#include "mcu-config-result.h"
static void store32(unsigned char *p,unsigned v)
{p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
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
 {
 unsigned char unaligned[13]={0},*p=unaligned+1;
 store32(p,0x12345678U);store32(p+4,0x89abcdefU);store32(p+8,0xfedcba98U);
 assert(wr_iot_config_rf_read_matches(0xed,2,1,0xed,2,p,12,24,24,12,0x12345678U,0x89abcdefU,0xfedcba98U));
 for(i=0;i<12;i++){
 p[i]^=1;assert(!wr_iot_config_rf_read_matches(0xed,2,1,0xed,2,p,12,24,24,12,0x12345678U,0x89abcdefU,0xfedcba98U));p[i]^=1;
 }
 for(len=0;len<24;len++)if(len!=12)
 assert(!wr_iot_config_rf_read_matches(0xed,2,1,0xed,2,p,len,24,24,12,0x12345678U,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_rf_read_matches(0xed,2,0,0xed,2,p,12,24,24,12,0x12345678U,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_rf_read_matches(0xed,2,1,0xed,3,p,12,24,24,12,0x12345678U,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_rf_read_matches(0xed,2,1,0xed,2,NULL,12,24,24,12,0x12345678U,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_rf_read_matches(0xed,2,1,0xed,2,p,12,24,23,12,0x12345678U,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_rf_read_matches(0xed,2,1,0xed,2,p,12,24,24,~0U,0x12345678U,0x89abcdefU,0xfedcba98U));
 puts("PASS RF readback parser: unaligned LE words, exact stream/address/value, query/envelope/length gates; no sequence/ticket or ledger grant");
 }
 puts("PASS config MAC-write result: exact envelope/set direction, all status bytes, length/null/overflow refusal; pure parser only");
 {
 unsigned char b[33]={0},*p=b+1;store32(p+24,0x89abcdefU);store32(p+28,0xfedcba98U);
 assert(wr_iot_config_mac_read_matches(0xed,0x0e,1,0xed,0x0e,p,32,44,44,12,0x89abcdefU,0xfedcba98U));
 for(i=20;i<32;i++){p[i]^=1;assert(!wr_iot_config_mac_read_matches(0xed,0x0e,1,0xed,0x0e,p,32,44,44,12,0x89abcdefU,0xfedcba98U));p[i]^=1;}
 for(len=0;len<48;len++)if(len!=32)assert(!wr_iot_config_mac_read_matches(0xed,0x0e,1,0xed,0x0e,p,len,44,44,12,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_mac_read_matches(0xed,0x0e,0,0xed,0x0e,p,32,44,44,12,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_mac_read_matches(0xed,0x0e,1,0xed,2,p,32,44,44,12,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_mac_read_matches(0xed,0x0e,1,0xed,0x0e,NULL,32,44,44,12,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_mac_read_matches(0xed,0x0e,1,0xed,0x0e,p,32,44,43,12,0x89abcdefU,0xfedcba98U));
 assert(!wr_iot_config_mac_read_matches(0xed,0x0e,1,0xed,0x0e,p,32,44,44,~0U,0x89abcdefU,0xfedcba98U));
 puts("PASS MAC multi-read parser: unaligned LE record, MAC type/address/full value, query/envelope/length; no proof retirement");
 }
 return 0;
}
