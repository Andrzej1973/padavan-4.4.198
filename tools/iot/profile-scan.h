/* Shared no-write structural preflight for stream and captured profile bytes. */
#ifndef WR_IOT_PROFILE_SCAN_H
#define WR_IOT_PROFILE_SCAN_H
#include "profile-line.h"
static const char *const wr_iot_profile_required[]={"BssidNum","SSID1","SSID2","SSID3","WPAPSK1","WPAPSK2","WPAPSK3","AuthMode","EncrypType","WmmCapable","DLSCapable","NoForwarding","HideSSID","StationKeepAlive","PreAuth","IEEE8021X","FixedTxMode","HT_MCS"};
struct wr_iot_profile_scan {unsigned char seen[sizeof(wr_iot_profile_required)/sizeof(wr_iot_profile_required[0])];};
static inline int wr_iot_profile_scan_line(struct wr_iot_profile_scan *s,const char *line,
 const char *ssid,const char *password,int enabled,int removing){
 char transformed[4096];const char *eq;size_t key_size,i;
 if(!wr_iot_profile_line_direction(transformed,sizeof(transformed),line,ssid,password,enabled,removing))return 0;
 if(enabled&&(eq=strchr(line,'='))!=NULL){
  key_size=(size_t)(eq-line);
  for(i=0;i<sizeof(s->seen);i++)if(strlen(wr_iot_profile_required[i])==key_size&&!strncmp(line,wr_iot_profile_required[i],key_size)){
   if(s->seen[i])return 0;
   s->seen[i]=1;break;
  }
 }
 return 1;
}
static inline int wr_iot_profile_scan_complete(const struct wr_iot_profile_scan *s,int enabled){
 size_t i;if(enabled)for(i=0;i<sizeof(s->seen);i++)if(!s->seen[i])return 0;
 return 1;
}
static inline int wr_iot_profile_disable_buffer(const unsigned char *data,size_t length,
 const char *ssid,const char *password){
 struct wr_iot_profile_scan scan={{0}};char line[2048];size_t i,used=0;
 if(!data||!length||length>256U*1024U||memchr(data,0,length))return 0;
 for(i=0;i<length;i++){
  if(used+1>=sizeof(line))return 0;
  line[used++]=(char)data[i];
  if(data[i]=='\n'){
   line[used]=0;
   if(!wr_iot_profile_scan_line(&scan,line,ssid,password,1,1))return 0;
   used=0;
  }
 }
 if(used){line[used]=0;if(!wr_iot_profile_scan_line(&scan,line,ssid,password,1,1))return 0;}
 return wr_iot_profile_scan_complete(&scan,1);
}
#endif
