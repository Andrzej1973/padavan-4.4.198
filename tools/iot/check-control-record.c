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
 puts("PASS IoT control records: bounded portable request, delimiter/overflow refusal, ID-bound fresh explicit result states");
 return 0;
}
