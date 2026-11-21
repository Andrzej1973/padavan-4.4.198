#ifndef WR_IOT_HTTP_VIEW_REQUEST_H
#define WR_IOT_HTTP_VIEW_REQUEST_H
#include "control-record-common.h"
static inline int wr_iot_http_view_request_read(int authenticated,const char *method,
 const char *content_type,const char *expected_token,const char *body,size_t length)
{
 size_t index;unsigned int difference=0;
 if(authenticated!=1||!method||strcmp(method,"POST")||!content_type||
    strcmp(content_type,"application/x-www-form-urlencoded")||!expected_token||
    !wr_iot_control_id(expected_token)||!body||length!=38||memcmp(body,"token=",6))return 0;
 for(index=0;index<32;index++){
  if(wr_iot_saved_hex((unsigned char)body[index+6])<0)return 0;
  difference|=(unsigned char)expected_token[index]^(unsigned char)body[index+6];
 }
 return difference==0;
}
#endif
