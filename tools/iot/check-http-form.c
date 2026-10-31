#include "http-form.h"
#include <assert.h>
#include <stdio.h>

static void refused(const char *body,size_t length)
{
 struct wr_iot_http_form result,before;
 memset(&result,0x5a,sizeof(result));before=result;
 assert(!wr_iot_http_form_parse(&result,body,length));
 assert(!memcmp(&result,&before,sizeof(result)));
}

int main(void)
{
 static const char valid[]=
  "wr_iot_request_enable=1&wr_iot_request_ssid=IoT+%D0%94%D1%96%D0%BC"
  "&wr_iot_request_psk=correct-horse-123&wr_iot_request_gateway=192.168.50.1"
  "&wr_iot_request_mask=255.255.255.0&wr_iot_request_start=192.168.50.20"
  "&wr_iot_request_end=192.168.50.200&token=0123456789abcdef0123456789ABCDEF";
 static const char disabled[]=
  "wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDEF";
 struct wr_iot_http_form result;
 char oversized[WR_IOT_HTTP_FORM_MAX+1];
 assert(wr_iot_http_form_parse(&result,valid,sizeof(valid)-1));
 assert(result.present==255U&&result.enable[0]=='1');
 assert(!strcmp(result.ssid,"IoT Дім")&&!strcmp(result.psk,"correct-horse-123"));
 assert(!strcmp(wr_iot_http_form_read(&result,"wr_iot_ssid"),"IoT Дім"));
 assert(!wr_iot_http_form_read(&result,"unknown"));
 assert(wr_iot_http_form_parse(&result,disabled,sizeof(disabled)-1));
 assert(result.present==129U&&result.enable[0]=='0'&&!result.ssid[0]);
 assert(!wr_iot_http_form_read(&result,"wr_iot_ssid"));
 refused("wr_iot_request_enable=0&wr_iot_request_psk=old-secret&token=0123456789abcdef0123456789ABCDEF",
         sizeof("wr_iot_request_enable=0&wr_iot_request_psk=old-secret&token=0123456789abcdef0123456789ABCDEF")-1);
 refused("wr_iot_request_enable=0&wr_iot_request_ssid=old-name&token=0123456789abcdef0123456789ABCDEF",
         sizeof("wr_iot_request_enable=0&wr_iot_request_ssid=old-name&token=0123456789abcdef0123456789ABCDEF")-1);
 refused("wr_iot_request_enable=1&token=0123456789abcdef0123456789ABCDEF",
         sizeof("wr_iot_request_enable=1&token=0123456789abcdef0123456789ABCDEF")-1);
 refused("wr_iot_request_enable=0&wr_iot_request_enable=1&token=0123456789abcdef0123456789ABCDEF",
         sizeof("wr_iot_request_enable=0&wr_iot_request_enable=1&token=0123456789abcdef0123456789ABCDEF")-1);
 refused("wr_iot_request_enable=0&unknown=1&token=0123456789abcdef0123456789ABCDEF",
         sizeof("wr_iot_request_enable=0&unknown=1&token=0123456789abcdef0123456789ABCDEF")-1);
 refused("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDE%00",
         sizeof("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDE%00")-1);
 refused("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDE%GG",
         sizeof("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDE%GG")-1);
 refused("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDEG",
         sizeof("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDEG")-1);
 refused("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDEF&",
         sizeof("wr_iot_request_enable=0&token=0123456789abcdef0123456789ABCDEF&")-1);
 memset(oversized,'x',sizeof(oversized));
 refused(oversized,sizeof(oversized));
 puts("PASS IoT HTTP form: fixed fields, bounded decoding, duplicate/malformed refusal, no writes");
 return 0;
}
