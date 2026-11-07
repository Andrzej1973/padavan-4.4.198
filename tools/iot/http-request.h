/* No-write boundary for the dedicated authenticated IoT POST handler.
 * Caller supplies authentication and its server-owned CSRF token, then holds
 * the service lock while obtaining live mode/range inputs and submitting the
 * validated request. This helper neither dispatches RC nor acknowledges Apply. */
#ifndef WR_IOT_HTTP_REQUEST_H
#define WR_IOT_HTTP_REQUEST_H
#include "http-form.h"
#include "request.h"

static int wr_iot_http_request_read(struct wr_iot_request *out,int authenticated,
 const char *method,const char *content_type,const char *expected_token,
 const char *body,size_t length,int router_mode,int radio_on,int radio_mode,
 const struct wr_iot_range *reserved,size_t count)
{
 struct wr_iot_http_form form;
 unsigned int difference=0;size_t i;
 if(!out||authenticated!=1||!method||strcmp(method,"POST")||
    !content_type||strcmp(content_type,"application/x-www-form-urlencoded")||
    !expected_token||strlen(expected_token)!=32||
    !wr_iot_http_form_parse(&form,body,length))return 0;
 for(i=0;i<32;i++){
  if(wr_iot_http_hex((unsigned char)expected_token[i])<0)return 0;
  difference|=(unsigned char)expected_token[i]^(unsigned char)form.token[i];
 }
 if(difference)return 0;
 return wr_iot_request_read(out,wr_iot_http_form_read,&form,router_mode,
                            radio_on,radio_mode,reserved,count);
}
#endif
