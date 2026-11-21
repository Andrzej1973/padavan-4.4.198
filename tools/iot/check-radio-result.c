#include "radio-result.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void){
 unsigned char storage[10]={0},before[10];unsigned char *response=storage+1;
 size_t length;unsigned int i;
 response[0]=WR_IOT_RADIO_EXT_COMMAND;
 response[1]=0x7f;response[2]=0x80;response[3]=0xff;
 memcpy(before,storage,sizeof(storage));
 assert(wr_iot_radio_result_success(response,8));
 assert(!memcmp(storage,before,sizeof(storage)));
 assert(!wr_iot_radio_result_success(NULL,8));
 for(length=0;length<=10;length++)if(length!=8)
  assert(!wr_iot_radio_result_success(response,length));
 for(i=0;i<256;i++){
  response[0]=(unsigned char)i;
  assert(wr_iot_radio_result_success(response,8)==(i==WR_IOT_RADIO_EXT_COMMAND));
 }
 response[0]=WR_IOT_RADIO_EXT_COMMAND;
 for(i=4;i<8;i++){
  response[i]=1;assert(!wr_iot_radio_result_success(response,8));response[i]=0;
  response[i]=0x80;assert(!wr_iot_radio_result_success(response,8));response[i]=0;
 }
 assert(wr_iot_radio_result_success(response,8));
 puts("PASS radio-result parser: exact length/command, firmware rejection, unaligned nonmutating read; no request-binding or RF proof");
 return 0;
}
