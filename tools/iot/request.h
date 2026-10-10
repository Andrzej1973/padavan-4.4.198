/* Copy each borrowed NVRAM value before reading the next. Caller holds the
 * configuration/service lock. This snapshot never changes live configuration. */
#ifndef WR_IOT_REQUEST_H
#define WR_IOT_REQUEST_H
#include "subnet.h"
#include "../shared-wifi/validate.h"
struct wr_iot_request {
 int enabled;
 char ssid[33],password[65],gateway[16],mask[16],first[16],last[16];
 struct wr_iot_subnet subnet;
};
static inline int wr_iot_request_copy(char *out,size_t capacity,const char *value){
 size_t n;if(!value)return 0;n=strlen(value);if(n>=capacity)return 0;
 memcpy(out,value,n+1);return 1;
}
static inline int wr_iot_request_read(struct wr_iot_request *out,const char *(*read)(void *,const char *),void *context,
 int router_mode,int radio_on,int radio_mode,const struct wr_iot_range *reserved,size_t count){
 struct wr_iot_request candidate;struct wr_shared_wifi_fields credentials;const char *value;
 if(!out||!read)return 0;
 memset(&candidate,0,sizeof(candidate));value=read(context,"wr_iot_enable");
 if(!value)return 0;
 if(!strcmp(value,"0")){*out=candidate;return 1;}
 if(strcmp(value,"1")||router_mode!=1||radio_on!=1||radio_mode!=0)return 0;
 candidate.enabled=1;
#define COPY(field,key) do {if(!wr_iot_request_copy(candidate.field,sizeof(candidate.field),read(context,key)))return 0;} while(0)
 COPY(ssid,"wr_iot_ssid");COPY(password,"wr_iot_psk");
 COPY(gateway,"wr_iot_gateway");COPY(mask,"wr_iot_mask");
 COPY(first,"wr_iot_start");COPY(last,"wr_iot_end");
#undef COPY
 credentials.ssid=candidate.ssid;credentials.auth="psk";credentials.wep="0";
 credentials.wpa_mode="2";credentials.crypto="aes";credentials.password=candidate.password;
 if(wr_shared_wifi_validate(&credentials)!=WR_SHARED_WIFI_OK||
    !wr_iot_subnet_plan(&candidate.subnet,candidate.gateway,candidate.mask,candidate.first,candidate.last,reserved,count))return 0;
 *out=candidate;return 1;
}
#endif
