/* Cold profile credentials, independent of runtime activation/network state.
 * Caller serializes NVRAM/config reads; borrowed values copied immediately.
 * No config writes, generated credentials, fallback profile or radio actions. */
#ifndef WR_IOT_PRECREATED_PROFILE_REQUEST_H
#define WR_IOT_PRECREATED_PROFILE_REQUEST_H
#include "request.h"
struct wr_iot_precreated_profile_request {
 int requested_enabled;
 char ssid[33],password[65];
};
static inline int wr_iot_precreated_profile_request_read(
 struct wr_iot_precreated_profile_request *out,
 const char *(*read)(void *,const char *),void *context)
{
 struct wr_iot_precreated_profile_request candidate;
 struct wr_shared_wifi_fields fields;const char *value;
 if(!out||!read)return 0;
 memset(&candidate,0,sizeof(candidate));
 value=read(context,"wr_iot_enable");
 if(!value)return 0;
 if(!*value||!strcmp(value,"0"))candidate.requested_enabled=0;
 else if(!strcmp(value,"1"))candidate.requested_enabled=1;
 else return 0;
 if(!wr_iot_request_copy(candidate.ssid,sizeof(candidate.ssid),read(context,"wr_iot_ssid"))||
    !wr_iot_request_copy(candidate.password,sizeof(candidate.password),read(context,"wr_iot_psk")))return 0;
 fields.ssid=candidate.ssid;fields.auth="psk";fields.wep="0";
 fields.wpa_mode="2";fields.crypto="aes";fields.password=candidate.password;
 if(wr_shared_wifi_validate(&fields)!=WR_SHARED_WIFI_OK)return 0;
 *out=candidate;return 1;
}
#endif
