/* Cold profile credentials, independent of runtime activation/network state.
 * Caller serializes NVRAM/config reads; borrowed values copied immediately.
 * No config writes or radio actions. Factory boot-only credentials require
 * explicit initialized entropy; normal saved-request parsing has no fallback. */
#ifndef WR_IOT_PRECREATED_PROFILE_REQUEST_H
#define WR_IOT_PRECREATED_PROFILE_REQUEST_H
#include "request.h"
struct wr_iot_precreated_profile_request {
 int requested_enabled,provisioned;
 char ssid[33],password[65];
};
static inline int wr_iot_precreated_profile_snapshot(
 struct wr_iot_precreated_profile_request *out,
 const char *(*read)(void *,const char *),void *context)
{
 struct wr_iot_precreated_profile_request candidate;
 const char *value;
 if(!out||!read)return 0;
 memset(&candidate,0,sizeof(candidate));
 value=read(context,"wr_iot_enable");
 if(!value)return 0;
 if(!*value||!strcmp(value,"0"))candidate.requested_enabled=0;
 else if(!strcmp(value,"1"))candidate.requested_enabled=1;
 else return 0;
 if(!wr_iot_request_copy(candidate.ssid,sizeof(candidate.ssid),read(context,"wr_iot_ssid"))||
    !wr_iot_request_copy(candidate.password,sizeof(candidate.password),read(context,"wr_iot_psk")))return 0;
 *out=candidate;return 1;
}
static inline int wr_iot_precreated_profile_request_valid(
 struct wr_iot_precreated_profile_request *candidate)
{
 struct wr_shared_wifi_fields fields;
 fields.ssid=candidate->ssid;fields.auth="psk";fields.wep="0";
 fields.wpa_mode="2";fields.crypto="aes";fields.password=candidate->password;
 return wr_shared_wifi_validate(&fields)==WR_SHARED_WIFI_OK;
}
static inline int wr_iot_precreated_profile_request_read(
 struct wr_iot_precreated_profile_request *out,
 const char *(*read)(void *,const char *),void *context)
{
 struct wr_iot_precreated_profile_request candidate;
 if(!out||!wr_iot_precreated_profile_snapshot(&candidate,read,context)||
    !wr_iot_precreated_profile_request_valid(&candidate))return 0;
 candidate.provisioned=1;*out=candidate;return 1;
}
/* Factory-only cold reservation. Entropy callback must supply exactly32bytes
 * from an initialized CSPRNG, refusing unavailable/short reads. It is never a
 * predictable PRNG fallback. The returned credential is boot-profile-only:
 * do not save it as requested configuration or allow runtime ON from it. */
static inline int wr_iot_precreated_boot_request_read(
 struct wr_iot_precreated_profile_request *out,
 const char *(*read)(void *,const char *),void *context,
 int (*entropy)(void *,unsigned char *,unsigned int),void *entropy_context)
{
 struct wr_iot_precreated_profile_request candidate;
 unsigned char bytes[32]={0};volatile unsigned char *wipe;
 unsigned int i,nonzero=0;int ok=0;static const char hex[]="0123456789abcdef";
 if(!out||!wr_iot_precreated_profile_snapshot(&candidate,read,context))return 0;
 if(wr_iot_precreated_profile_request_valid(&candidate)){
  candidate.provisioned=1;*out=candidate;return 1;
 }
 /* Do not silently replace invalid or partially configured saved credentials. */
 if(candidate.requested_enabled||candidate.ssid[0]||candidate.password[0]||!entropy)return 0;
 if(entropy(entropy_context,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto done;
 for(i=0;i<sizeof(bytes);i++)nonzero|=bytes[i];
 if(!nonzero)goto done;
 memcpy(candidate.ssid,"WR1200JS-IoT",sizeof("WR1200JS-IoT"));
 for(i=0;i<sizeof(bytes);i++){
  candidate.password[2*i]=hex[bytes[i]>>4];
  candidate.password[2*i+1]=hex[bytes[i]&15];
 }
 candidate.password[64]=0;
 if(!wr_iot_precreated_profile_request_valid(&candidate))goto done;
 candidate.provisioned=0;*out=candidate;ok=1;
 done:
 wipe=bytes;for(i=0;i<sizeof(bytes);i++)wipe[i]=0;
 return ok;
}

#endif
