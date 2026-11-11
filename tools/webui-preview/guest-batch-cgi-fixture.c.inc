/* Actual pinned CGI decoding -> candidate handler -> actual NVRAM core.
 * Auth, descriptor/copy boundary, flash and RC remain fixture substitutes. */
#include "modern-body.h"
static void batch_form_pair(char *body,size_t capacity,const char *key,const char *value)
{
 static const char hex[]="0123456789ABCDEF";
 size_t n=strlen(body);
 if(n){assert(n+1<capacity);body[n++]='&';}
 for(unsigned int part=0;part<2;part++){
  const unsigned char *p=(const unsigned char *)(part?value:key);
  for(;*p;p++){
   assert(n+3<capacity);
   body[n++]='%';body[n++]=hex[*p>>4];body[n++]=hex[*p&15];
  }
  if(!part){assert(n+1<capacity);body[n++]='=';}
 }
 body[n]=0;
}
static void guest_batch_cgi_cases(void)
{
 const char *ssid="Дім &;=%+";
 const char *invalid[]={NULL,NULL,"&x=%00", "&x=%GG"};
 for(unsigned int band=0;band<2;band++)for(unsigned int stale=0;stale<2;stale++){
  char body[8193]={0},decoded[8193],key[64],*json=NULL;size_t size=0;
  FILE *input,*output;
  reset_http_batch();guest_band=band?"wl":"rt";
  depth=1;
  assert(!_nvram_set("rt_ssid","main24-sentinel",0));
  assert(!_nvram_set("wl_ssid","main5-sentinel",0));
  assert(!_nvram_set("rt_iot_ssid","iot-sentinel",0));depth=0;
  batch_form_pair(body,sizeof(body),"wr_modern_guest_version","1");
  batch_form_pair(body,sizeof(body),"wr_modern_guest_band",guest_band);
  batch_form_pair(body,sizeof(body),"wr_modern_guest_password_intent","keep");
  batch_form_pair(body,sizeof(body),"action_mode"," Apply ");
  batch_form_pair(body,sizeof(body),"action_script","");
  batch_form_pair(body,sizeof(body),"sid_list",band?"WLANConfig11a;":"WLANConfig11b;");
  for(unsigned int i=0;i<13;i++){
   snprintf(key,sizeof(key),"%s_guest_%s",guest_band,wr_modern_guest_fields[i]);
   batch_form_pair(body,sizeof(body),key,i==1?ssid:guest_old[i]);
   snprintf(key,sizeof(key),"wr_modern_guest_expected_%s",wr_modern_guest_fields[i]);
   batch_form_pair(body,sizeof(body),key,stale&&i==1?"stale":guest_old[i]);
  }
  input=fmemopen(body,strlen(body),"r");assert(input);
  assert(wr_modern_body_read(input,decoded,sizeof(decoded),(int)strlen(body)));fclose(input);
  init_cgi(decoded);http_actual_cgi=1;
  output=open_memstream(&json,&size);assert(output);
  do_wr_modern_guest_apply("wr_modern_guest_apply.json",output);fclose(output);
  assert(strstr(json,stale?"reload_required":"configuration_matches"));free(json);
  snprintf(key,sizeof(key),"%s_guest_ssid",guest_band);
  assert(!strcmp(_nvram_get(key),stale?"Guest":ssid));
  snprintf(key,sizeof(key),"%s_guest_wpa_psk",guest_band);
  assert(!strcmp(_nvram_get(key),"stored-guest-key"));
  assert(!strcmp(_nvram_get("rt_ssid"),"main24-sentinel"));
  assert(!strcmp(_nvram_get("wl_ssid"),"main5-sentinel"));
  assert(!strcmp(_nvram_get("rt_iot_ssid"),"iot-sentinel"));
  assert(!strcmp(_nvram_get(band?"rt_guest_ssid":"wl_guest_ssid"),"Guest"));
  assert(http_calls==(stale?0:1)&&http_commits==(stale?0:1));
  assert(http_notifications==(stale?0:1));
  init_cgi(NULL);http_actual_cgi=0;wr_modern_guest_batch_wipe(decoded,sizeof(decoded));
  for(unsigned int bad=0;bad<sizeof(invalid)/sizeof(invalid[0]);bad++){
   char malformed[8193],suffix[64];int calls=http_calls;
   if(bad==0)snprintf(suffix,sizeof(suffix),"&%s_guest_ssid=alias",guest_band);
   else if(bad==1)snprintf(suffix,sizeof(suffix),"&%s_guest_ssid=alias",band?"w%6c":"r%74");
   else snprintf(suffix,sizeof(suffix),"%s",invalid[bad]);
   assert(snprintf(malformed,sizeof(malformed),"%s%s",body,suffix)<(int)sizeof(malformed));
   input=fmemopen(malformed,strlen(malformed),"r");assert(input);
   assert(!wr_modern_body_read(input,decoded,sizeof(decoded),(int)strlen(malformed)));fclose(input);
   assert(wr_nvram_zero_bytes(decoded,sizeof(decoded))&&!get_cgi("rt_guest_ssid")&&http_calls==calls);
  }
 }
 http_ioctl_mode=0;
 puts("PASS actual CGI + strict form body -> batch HTTP/ioctl/core: both bands UTF8/delimiters, keep-key, stale snapshot no writes, alias duplicates/malformed encoding rejected; auth/flash/RC substituted");
}
