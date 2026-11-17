/* Synchronous admitted-generator credential view; no native writes. */
#ifndef WR_IOT_GENERATION_PROFILE_H
#define WR_IOT_GENERATION_PROFILE_H
#include "precreated-profile-request.h"
struct wr_iot_generation_config;
/* Synchronous borrowed view; caller proves radio/file ownership before enter
 * and keeps the pin at its stable address until leave. No nested binding. */
int wr_iot_generation_profile_enter(const struct wr_iot_generation_config *);
int wr_iot_generation_profile_leave(const struct wr_iot_generation_config *);
/* 1 private admitted profile, 0 no override, -1 invalid retained context. */
int wr_iot_generation_profile_request(struct wr_iot_precreated_profile_request *);
static inline int wr_iot_generation_boot_request_read(
 struct wr_iot_precreated_profile_request *out,
 const char *(*read)(void *,const char *),void *context,
 int (*entropy)(void *,unsigned char *,unsigned int),void *entropy_context)
{
 struct wr_iot_precreated_profile_request candidate={0};int selected,ok=0;
 volatile unsigned char *wipe;size_t length;
 if(!out)return 0;
 selected=wr_iot_generation_profile_request(&candidate);
 if(selected==1){
  if((candidate.requested_enabled==0||candidate.requested_enabled==1)&&
     candidate.provisioned==1&&memchr(candidate.ssid,0,sizeof(candidate.ssid))&&
     memchr(candidate.password,0,sizeof(candidate.password))&&
     wr_iot_precreated_profile_request_valid(&candidate)){*out=candidate;ok=1;}
 }else if(selected==0)
  ok=wr_iot_precreated_boot_request_read(out,read,context,entropy,entropy_context);
 wipe=(volatile unsigned char *)&candidate;length=sizeof(candidate);
 while(length--)*wipe++=0;
 return ok;
}
#endif
