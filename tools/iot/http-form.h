/* Parse one bounded, URL-encoded IoT POST before any NVRAM or RC operation.
 * Authentication, CSRF comparison and activation are the caller's duties. */
#ifndef WR_IOT_HTTP_FORM_H
#define WR_IOT_HTTP_FORM_H

#include <stddef.h>
#include <string.h>

#define WR_IOT_HTTP_FORM_MAX 1024
#define WR_IOT_HTTP_FIELD_COUNT 8

struct wr_iot_http_form {
 char enable[2],ssid[33],psk[65],gateway[16],mask[16],start[16],end[16],token[33];
 unsigned int present;
};

static int wr_iot_http_hex(unsigned char c)
{
 if(c>='0'&&c<='9')return c-'0';
 if(c>='a'&&c<='f')return c-'a'+10;
 if(c>='A'&&c<='F')return c-'A'+10;
 return -1;
}

static int wr_iot_http_value(char *out,size_t capacity,const char *in,size_t length)
{
 size_t i,n=0;int high,low;unsigned char c;
 for(i=0;i<length;i++){
  c=(unsigned char)in[i];
  if(c=='%'){
   if(i+2>=length)return 0;
   high=wr_iot_http_hex((unsigned char)in[++i]);
   low=wr_iot_http_hex((unsigned char)in[++i]);
   if(high<0||low<0)return 0;
   c=(unsigned char)((high<<4)|low);
  }else if(c=='+')c=' ';
  if(!c||c<0x20||c==0x7f||n+1>=capacity)return 0;
  out[n++]=(char)c;
 }
 out[n]=0;return 1;
}

static int wr_iot_http_form_parse(struct wr_iot_http_form *out,const char *body,size_t length)
{
 static const char *names[]={"wr_iot_request_enable","wr_iot_request_ssid",
  "wr_iot_request_psk","wr_iot_request_gateway","wr_iot_request_mask",
  "wr_iot_request_start","wr_iot_request_end","token"};
 struct wr_iot_http_form candidate={0};
 char *values[]={candidate.enable,candidate.ssid,candidate.psk,candidate.gateway,
  candidate.mask,candidate.start,candidate.end,candidate.token};
 const size_t capacities[]={sizeof(candidate.enable),sizeof(candidate.ssid),
  sizeof(candidate.psk),sizeof(candidate.gateway),sizeof(candidate.mask),
  sizeof(candidate.start),sizeof(candidate.end),sizeof(candidate.token)};
 size_t start,end,equal,i;int matched;
 if(!out||!body||!length||length>WR_IOT_HTTP_FORM_MAX)return 0;
 for(start=0;start<length;start=end+1){
  for(end=start;end<length&&body[end]!='&';end++)
   if(!body[end])return 0;
  if(end==start)return 0;
  for(equal=start;equal<end&&body[equal]!='=';equal++);
  if(equal==start||equal==end)return 0;
  matched=-1;
  for(i=0;i<WR_IOT_HTTP_FIELD_COUNT;i++)
   if(strlen(names[i])==equal-start&&
      !memcmp(body+start,names[i],equal-start)){matched=(int)i;break;}
  if(matched<0||(candidate.present&(1U<<matched))||
     !wr_iot_http_value(values[matched],capacities[matched],
                        body+equal+1,end-equal-1))return 0;
  candidate.present|=1U<<matched;
  if(end==length)break;
  if(end+1==length)return 0;
 }
 if(!(candidate.present&1U)||!(candidate.present&(1U<<7))||
    (strcmp(candidate.enable,"0")&&strcmp(candidate.enable,"1"))||
    strlen(candidate.token)!=32)return 0;
 for(i=0;i<32;i++)if(wr_iot_http_hex((unsigned char)candidate.token[i])<0)return 0;
 if(candidate.enable[0]=='1'&&candidate.present!=((1U<<WR_IOT_HTTP_FIELD_COUNT)-1))return 0;
 *out=candidate;return 1;
}

/* Adapter for wr_iot_request_read(); absent fields remain absent. */
static const char *wr_iot_http_form_read(void *context,const char *key)
{
 static const char *keys[]={"wr_iot_enable","wr_iot_ssid","wr_iot_psk",
  "wr_iot_gateway","wr_iot_mask","wr_iot_start","wr_iot_end"};
 const struct wr_iot_http_form *form=context;
 const char *values[7];size_t i;
 if(!form||!key)return NULL;
 values[0]=form->enable;values[1]=form->ssid;values[2]=form->psk;
 values[3]=form->gateway;values[4]=form->mask;
 values[5]=form->start;values[6]=form->end;
 for(i=0;i<7;i++)
  if(!strcmp(key,keys[i]))return form->present&(1U<<i)?values[i]:NULL;
 return NULL;
}

#endif
