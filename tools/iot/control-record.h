/* Bounded portable HTTPD/RC records. Never write native structs across the
 * process boundary: their padding and byte order are not a wire format. */
#ifndef WR_IOT_CONTROL_RECORD_H
#define WR_IOT_CONTROL_RECORD_H
#include <stdio.h>
#include "request.h"
#define WR_IOT_CONTROL_RECORD_MAX 512
enum wr_iot_result_state {
 WR_IOT_RESULT_QUEUED=1,WR_IOT_RESULT_RUNNING,WR_IOT_RESULT_APPLIED,
 WR_IOT_RESULT_REJECTED,WR_IOT_RESULT_RECOVERY
};
struct wr_iot_control_request {
 char id[33];unsigned long long created;
 struct wr_iot_request request;
};
struct wr_iot_control_result {
 char id[33];enum wr_iot_result_state state;
 unsigned long long created,observed;
};
static inline int wr_iot_control_id(const char *id){
 size_t i;if(!id||strlen(id)!=32)return 0;
 for(i=0;i<32;i++)if(!((id[i]>='0'&&id[i]<='9')||
    (id[i]>='a'&&id[i]<='f')))return 0;
 return 1;
}
static inline const char *wr_iot_control_state(enum wr_iot_result_state state){
 switch(state){
 case WR_IOT_RESULT_QUEUED:return "queued";
 case WR_IOT_RESULT_RUNNING:return "running";
 case WR_IOT_RESULT_APPLIED:return "applied";
 case WR_IOT_RESULT_REJECTED:return "rejected";
 case WR_IOT_RESULT_RECOVERY:return "recovery_required";
 default:return NULL;
 }
}
/* Missing, mismatched, future or stale observations never become success. */
static inline int wr_iot_control_result_current(const struct wr_iot_control_result *r,
 const char *id,unsigned long long now,unsigned long long max_age){
 return r&&wr_iot_control_id(id)&&memchr(r->id,0,sizeof(r->id))&&
  !strcmp(r->id,id)&&wr_iot_control_state(r->state)&&r->created&&r->observed&&
  r->created<=r->observed&&r->observed<=now&&now-r->observed<=max_age;
}
struct wr_iot_control_fields {char *values[7];};
static inline const char *wr_iot_control_read(void *context,const char *key){
 static const char *keys[]={"wr_iot_enable","wr_iot_ssid","wr_iot_psk",
  "wr_iot_gateway","wr_iot_mask","wr_iot_start","wr_iot_end"};
 struct wr_iot_control_fields *fields=context;size_t i;
 for(i=0;i<7;i++)if(!strcmp(key,keys[i]))return fields->values[i];
 return NULL;
}
/* Exact decimal, no signs, whitespace, overflow or leading zeroes. */
static inline int wr_iot_control_time(const char *text,unsigned long long *out){
 unsigned long long n=0,d;const unsigned long long limit=~0ULL;
 if(!text||!*text||*text=='0')return 0;
 for(;*text;text++){
  if(*text<'0'||*text>'9')return 0;
  d=(unsigned)(*text-'0');if(n>(limit-d)/10)return 0;n=n*10+d;
 }
 *out=n;return 1;
}
static inline int wr_iot_control_decode(struct wr_iot_control_request *out,
 const char *data,size_t length){
 char buffer[WR_IOT_CONTROL_RECORD_MAX],*lines[10];size_t i,start=0,count=0;
 struct wr_iot_control_request candidate={0};struct wr_iot_control_fields fields;
 if(!out||!data||!length||length>=sizeof(buffer)||memchr(data,0,length))return 0;
 memcpy(buffer,data,length);buffer[length]=0;
 for(i=0;i<length;i++)if(buffer[i]=='\n'){
  if(count==10)return 0;
  lines[count++]=buffer+start;buffer[i]=0;start=i+1;
 }
 if(count!=10||start!=length||strcmp(lines[0],"WR-IOT-1")||
    !wr_iot_control_id(lines[1])||!wr_iot_control_time(lines[2],&candidate.created))return 0;
 for(i=0;i<7;i++)fields.values[i]=lines[i+3];
 if(!wr_iot_request_read(&candidate.request,wr_iot_control_read,&fields,1,1,0,NULL,0))return 0;
 if(!candidate.request.enabled)for(i=1;i<7;i++)if(fields.values[i][0])return 0;
 memcpy(candidate.id,lines[1],33);*out=candidate;return 1;
}
static inline int wr_iot_control_encode(char *out,size_t capacity,
 const struct wr_iot_control_request *record){
 char buffer[WR_IOT_CONTROL_RECORD_MAX];int n;
 struct wr_iot_control_request checked;
 const struct wr_iot_request *r;
 if(!out||!record||!memchr(record->id,0,sizeof(record->id))||
    !wr_iot_control_id(record->id)||!record->created)return 0;
 r=&record->request;
 if((r->enabled!=0&&r->enabled!=1)||
    !memchr(r->ssid,0,sizeof(r->ssid))||!memchr(r->password,0,sizeof(r->password))||
    !memchr(r->gateway,0,sizeof(r->gateway))||!memchr(r->mask,0,sizeof(r->mask))||
    !memchr(r->first,0,sizeof(r->first))||!memchr(r->last,0,sizeof(r->last)))return 0;
 n=snprintf(buffer,sizeof(buffer),"WR-IOT-1\n%s\n%llu\n%d\n%s\n%s\n%s\n%s\n%s\n%s\n",
  record->id,record->created,r->enabled,r->ssid,r->password,r->gateway,r->mask,r->first,r->last);
 if(n<=0||(size_t)n>=sizeof(buffer)||(size_t)n+1>capacity||
    !wr_iot_control_decode(&checked,buffer,(size_t)n))return 0;
 memcpy(out,buffer,(size_t)n+1);return n;
}
#endif
