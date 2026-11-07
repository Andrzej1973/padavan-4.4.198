#include "http-request.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
 const char *token="0123456789abcdef0123456789abcdef";
 const char *type="application/x-www-form-urlencoded";
 const char *body="wr_iot_request_enable=1&wr_iot_request_ssid=IoT"
  "&wr_iot_request_psk=correct-horse-123&wr_iot_request_gateway=192.168.50.1"
  "&wr_iot_request_mask=255.255.255.0&wr_iot_request_start=192.168.50.20"
  "&wr_iot_request_end=192.168.50.200&token=0123456789abcdef0123456789abcdef";
 const char *disabled="wr_iot_request_enable=0&token=0123456789abcdef0123456789abcdef";
 struct wr_iot_request result,before;
 struct wr_iot_request range_source;
 struct wr_iot_range occupied;
 assert(wr_iot_http_request_read(&result,1,"POST",type,token,body,strlen(body),1,1,0,NULL,0));
 assert(result.enabled&&!strcmp(result.ssid,"IoT"));
 range_source=result;
 /* A supplied live range overlapping this proposed subnet must refuse. */
 occupied.first=range_source.subnet.network;
 occupied.last=range_source.subnet.broadcast;
 memset(&result,0x5a,sizeof(result));before=result;
#define REFUSED(auth,method,mime,csrf,router,radio,mode,ranges,n) do { \
 assert(!wr_iot_http_request_read(&result,auth,method,mime,csrf,body,strlen(body),router,radio,mode,ranges,n)); \
 assert(!memcmp(&result,&before,sizeof(result))); } while(0)
 REFUSED(0,"POST",type,token,1,1,0,NULL,0);
 REFUSED(1,"GET",type,token,1,1,0,NULL,0);
 REFUSED(1,"POST","application/x-www-form-urlencoded.evil",token,1,1,0,NULL,0);
 REFUSED(1,"POST",type,"1123456789abcdef0123456789abcdef",1,1,0,NULL,0);
 REFUSED(1,"POST",type,"",1,1,0,NULL,0);
 REFUSED(1,"POST",type,token,0,1,0,NULL,0);
 REFUSED(1,"POST",type,token,1,0,0,NULL,0);
 REFUSED(1,"POST",type,token,1,1,3,NULL,0);
 REFUSED(1,"POST",type,token,1,1,0,&occupied,1);
#undef REFUSED
 assert(wr_iot_http_request_read(&result,1,"POST",type,token,disabled,strlen(disabled),0,0,3,NULL,0));
 assert(!result.enabled);
 puts("PASS IoT HTTP request: authentication, POST/type, CSRF, live-mode/subnet refusal, unchanged output on refusal");
 return 0;
}
