#include "control-record.h"
#include <assert.h>
int main(void){
 struct wr_iot_control_request record={0},decoded,before;
 struct wr_iot_control_result result={0};char body[512],copy[512];int n;
 strcpy(record.id,"0123456789abcdef0123456789abcdef");record.created=123;
 record.request.enabled=1;strcpy(record.request.ssid,"IoT &=%%");
 strcpy(record.request.password,"password&=123");strcpy(record.request.gateway,"192.168.50.1");
 strcpy(record.request.mask,"255.255.255.0");strcpy(record.request.first,"192.168.50.20");
 strcpy(record.request.last,"192.168.50.200");
 n=wr_iot_control_encode(body,sizeof(body),&record);assert(n>0);
 assert(wr_iot_control_decode(&decoded,body,(size_t)n));
 assert(!strcmp(decoded.id,record.id)&&decoded.created==123&&
  !strcmp(decoded.request.ssid,record.request.ssid)&&
  !strcmp(decoded.request.password,record.request.password));
 memset(&decoded,0x5a,sizeof(decoded));before=decoded;
 assert(!wr_iot_control_decode(&decoded,body,(size_t)n-1));
 assert(!memcmp(&decoded,&before,sizeof(decoded)));
 memcpy(copy,body,(size_t)n);copy[0]='X';
 assert(!wr_iot_control_decode(&decoded,copy,(size_t)n));
 memcpy(copy,body,(size_t)n);copy[12]=0;
 assert(!wr_iot_control_decode(&decoded,copy,(size_t)n));
 strcpy(record.request.ssid,"injected\nSSID");assert(!wr_iot_control_encode(body,sizeof(body),&record));
 memset(record.request.ssid,'x',sizeof(record.request.ssid));
 assert(!wr_iot_control_encode(body,sizeof(body),&record));
 memset(&record.request,0,sizeof(record.request));
 n=wr_iot_control_encode(body,sizeof(body),&record);assert(n>0);
 assert(wr_iot_control_decode(&decoded,body,(size_t)n)&&!decoded.request.enabled);
 /* Wire enable must remain explicit even though persistent default is OFF. */
 {
  char *enable=strchr(body,'\n');assert(enable);
  enable=strchr(enable+1,'\n');assert(enable);
  enable=strchr(enable+1,'\n');assert(enable&&enable[1]=='0');
  size_t offset=(size_t)(enable+1-body);
  memcpy(copy,body,offset);memcpy(copy+offset,body+offset+1,(size_t)n-offset-1);
  before=decoded;
  assert(!wr_iot_control_decode(&decoded,copy,(size_t)n-1));
  assert(!memcmp(&decoded,&before,sizeof(decoded)));
 }
 strcpy(record.request.password,"hidden-secret");assert(!wr_iot_control_encode(body,sizeof(body),&record));
 assert(!wr_iot_control_time("18446744073709551616",&record.created));
 assert(!wr_iot_control_time("0123",&record.created));
 strcpy(result.id,record.id);result.created=100;result.observed=120;
 for(result.state=WR_IOT_RESULT_QUEUED;result.state<=WR_IOT_RESULT_RECOVERY;result.state++)
  assert(wr_iot_control_result_current(&result,record.id,125,10));
 result.state=WR_IOT_RESULT_APPLIED;
 assert(!wr_iot_control_result_current(&result,record.id,131,10));
 assert(!wr_iot_control_result_current(&result,record.id,119,10));
 assert(!wr_iot_control_result_current(&result,"1123456789abcdef0123456789abcdef",125,10));
 result.state=99;assert(!wr_iot_control_result_current(&result,record.id,125,10));
 memset(&record.request,0,sizeof(record.request));record.operation=WR_IOT_OPERATION_CONFIG;
 record.request.enabled=0;strcpy(record.request.ssid,"Saved disabled IoT");
 strcpy(record.request.password,"saved-password");strcpy(record.request.gateway,"192.168.50.1");
 strcpy(record.request.mask,"255.255.255.0");strcpy(record.request.first,"192.168.50.20");
 strcpy(record.request.last,"192.168.50.200");record.created=123;
 n=wr_iot_control_encode(body,sizeof(body),&record);assert(n>0);
 assert(!strncmp(body,"WR-IOT-CONFIG-REQUEST-1\n",24));
 assert(wr_iot_control_decode(&decoded,body,(size_t)n));
 assert(decoded.operation==WR_IOT_OPERATION_CONFIG&&!decoded.request.enabled&&
  !strcmp(decoded.request.password,"saved-password")&&decoded.request.subnet.network==0xc0a83200);
 before=decoded;assert(!wr_iot_control_decode(&decoded,body,(size_t)n-1));
 assert(!memcmp(&decoded,&before,sizeof(decoded)));
 record.operation=99;assert(!wr_iot_control_encode(body,sizeof(body),&record));
 record.operation=WR_IOT_OPERATION_CONFIG;record.request.password[0]=0;
 assert(!wr_iot_control_encode(body,sizeof(body),&record));
 result.state=WR_IOT_RESULT_STORED_RAM;
 assert(!strcmp(wr_iot_control_state(result.state),"stored_in_ram"));
 puts("PASS IoT control records: runtime v1 preserved, typed complete disabled configuration, malformed/partial refusal, distinct RAM outcome");
 return 0;
}
