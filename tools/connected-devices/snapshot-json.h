/* Bounded ASCII JSON with Unicode round-trip. Caller discards failed output. */
#ifndef WR_DEVICE_SNAPSHOT_JSON_H
#define WR_DEVICE_SNAPSHOT_JSON_H
#include "networkmap.h"
#include <stdint.h>
#include <stdarg.h>
struct wr_device_json_buffer {char *data;size_t capacity,length;};
static inline int wr_device_json_append(struct wr_device_json_buffer *out,const char *s){
 size_t n=strlen(s);
 if(out->length>=out->capacity||n>=out->capacity-out->length)return 0;
 memcpy(out->data+out->length,s,n);out->length+=n;out->data[out->length]=0;return 1;
}
static inline int wr_device_json_format(struct wr_device_json_buffer *out,const char *format,...){
 va_list args;int n;
 if(out->length>=out->capacity)return 0;
 va_start(args,format);n=vsnprintf(out->data+out->length,out->capacity-out->length,format,args);va_end(args);
 if(n<0||(size_t)n>=out->capacity-out->length)return 0;
 out->length+=(size_t)n;return 1;
}
static inline int wr_device_json_string(struct wr_device_json_buffer *out,const char *s,size_t limit){
 size_t i=0,n=strnlen(s,limit+1);
 if(n>limit||!wr_device_json_append(out,"\""))return 0;
 while(i<n){
  unsigned int c=(unsigned char)s[i++],cp=c;size_t follow=0,j;
  if(c>=0x80){
   if(c>=0xc2&&c<=0xdf){cp=c&31;follow=1;}
   else if(c>=0xe0&&c<=0xef){cp=c&15;follow=2;}
   else if(c>=0xf0&&c<=0xf4){cp=c&7;follow=3;}
   else cp=0xfffd;
   if(follow){
    int valid=n-i>=follow;
    for(j=0;valid&&j<follow;j++){unsigned int part=(unsigned char)s[i+j];if((part&0xc0)!=0x80)valid=0;else cp=(cp<<6)|(part&63);}
    if(!valid||(follow==1&&cp<0x80)||(follow==2&&cp<0x800)||(follow==3&&cp<0x10000)||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff))cp=0xfffd;
    else i+=follow;
   }
  }
  if(cp>=32&&cp<=126&&cp!=34&&cp!=92&&cp!=60&&cp!=62&&cp!=38){
   char literal[2]={(char)cp,0};if(!wr_device_json_append(out,literal))return 0;
  }else if(cp>0xffff){
   cp-=0x10000;if(!wr_device_json_format(out,"\\u%04x\\u%04x",0xd800+(cp>>10),0xdc00+(cp&1023)))return 0;
  }else if(!wr_device_json_format(out,"\\u%04x",cp))return 0;
 }
 return wr_device_json_append(out,"\"");
}
static inline int wr_device_snapshot_json(const struct wr_device_snapshot *snapshot,const char *epoch,uint64_t sequence,char *buffer,size_t capacity,size_t *length){
 struct wr_device_json_buffer out={buffer,capacity,0};unsigned int i;
 if(!snapshot||!epoch||!epoch[0]||!buffer||!capacity||!length||snapshot->count>WR_DEVICE_LIMIT||sequence>9007199254740991ULL)return 0;
 buffer[0]=0;*length=0;
 if(!wr_device_json_append(&out,"{\"epoch\":")||!wr_device_json_string(&out,epoch,64)||
    !wr_device_json_format(&out,",\"sequence\":%llu,\"invalid\":%u,\"truncated\":%s,\"devices\":[",(unsigned long long)sequence,snapshot->invalid,snapshot->truncated?"true":"false"))return 0;
 for(i=0;i<snapshot->count;i++){
  const struct wr_device_record *record=&snapshot->records[i];
  if((i&&!wr_device_json_append(&out,","))||!wr_device_json_append(&out,"{\"ip\":")||!wr_device_json_string(&out,record->ip,15)||
     !wr_device_json_append(&out,",\"mac\":")||!wr_device_json_string(&out,record->mac,17)||
     !wr_device_json_append(&out,",\"hostname\":")||!wr_device_json_string(&out,record->name,128)||
     !wr_device_json_format(&out,",\"legacyType\":%u,\"http\":%s,\"networkmapStale\":%s}",record->legacy_type,record->http?"true":"false",record->networkmap_stale?"true":"false"))return 0;
 }
 if(!wr_device_json_append(&out,"]}"))return 0;
 *length=out.length;return 1;
}
#endif
