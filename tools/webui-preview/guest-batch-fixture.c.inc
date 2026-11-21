#include "guest-batch.h"
static const char *guest_band,*guest_intent;
static const char *guest_values[14];
static const char *guest_old[]={"1","Guest","0","psk","2","aes","1","1","0","0","0111110","08002200","10002300"};
static int guest_secret_reads,guest_open;
static const char *guest_cgi(void *context,const char *key)
{
 char name[64];unsigned int i;(void)context;
 if(!strcmp(key,"wr_modern_guest_version"))return "1";
 if(!strcmp(key,"wr_modern_guest_band"))return guest_band;
 if(!strcmp(key,"wr_modern_guest_password_intent"))return guest_intent;
 if(!strcmp(key,"action_mode"))return " Apply ";
 if(!strcmp(key,"action_script"))return "";
 if(!strcmp(key,"sid_list"))return !strcmp(guest_band,"rt")?"WLANConfig11b;":"WLANConfig11a;";
 for(i=0;i<14;i++){
  snprintf(name,sizeof(name),"%s_guest_%s",guest_band,wr_modern_guest_fields[i]);
  if(!strcmp(key,name))return guest_open&&(i==4||i==5)?NULL:guest_values[i];
 }
 for(i=0;i<13;i++){
  snprintf(name,sizeof(name),"wr_modern_guest_expected_%s",wr_modern_guest_fields[i]);
  if(!strcmp(key,name))return guest_old[i];
 }
 return NULL;
}
static const char *guest_nv(void *context,const char *key)
{
 (void)context;if(strstr(key,"wpa_psk"))guest_secret_reads++;
 return _nvram_get(key);
}
static void guest_batch_cases(void)
{
 struct wr_nvram_wire_request packet,before;struct wr_nvram_edit decoded[16];
 enum wr_modern_guest_error reason;char key[64];unsigned int i;
 /* Reference existing persistence helper too; this fixture replaces no source. */
 (void)wr_modern_guest_persist_value;
 for(int band=0;band<2;band++)for(int mode=0;mode<3;mode++){
  reset_store();guest_band=band?"wl":"rt";guest_intent=mode==1?"change":"keep";guest_open=mode==2;
  depth=1;
  for(i=0;i<13;i++){
   guest_values[i]=guest_old[i];snprintf(key,sizeof(key),"%s_guest_%s",guest_band,wr_modern_guest_fields[i]);
   assert(!_nvram_set(key,guest_old[i],0));
  }
  snprintf(key,sizeof(key),"%s_guest_wpa_psk",guest_band);assert(!_nvram_set(key,"stored-guest-key",0));
  assert(!_nvram_set("rt_ssid","main-sentinel",0));assert(!_nvram_set("rt_iot_ssid","iot-sentinel",0));depth=0;
  guest_values[1]="NewGuest";guest_values[13]=mode==1?"replacement-key":NULL;
  if(guest_open)guest_values[3]="open";
  guest_secret_reads=0;
  assert(wr_modern_guest_build_batch(&packet,guest_cgi,guest_nv,NULL,&reason)==WR_SHARED_WIFI_OK);
  assert(reason==WR_GUEST_ERROR_NONE&&packet.count==(guest_open?13U:14U));
  assert(guest_secret_reads==(mode==0?1:0));
  assert(wr_nvram_decode_batch(&packet,sizeof(packet),decoded)==(int)packet.count);
  if(mode==0){
   snprintf(key,sizeof(key),"%s_guest_wpa_psk",guest_band);
   depth=1;assert(!_nvram_set(key,"concurrent-new-key",0));depth=0;
   assert(wr_nvram_batch_candidate(decoded,packet.count)==-EAGAIN);
   snprintf(key,sizeof(key),"%s_guest_ssid",guest_band);assert(!strcmp(_nvram_get(key),"Guest"));
   snprintf(key,sizeof(key),"%s_guest_wpa_psk",guest_band);
   depth=1;assert(!_nvram_set(key,"stored-guest-key",0));depth=0;
  }
  assert(wr_nvram_batch_candidate(decoded,packet.count)>0);
  snprintf(key,sizeof(key),"%s_guest_ssid",guest_band);assert(!strcmp(_nvram_get(key),"NewGuest"));
  snprintf(key,sizeof(key),"%s_guest_wpa_psk",guest_band);
  assert(!strcmp(_nvram_get(key),mode==1?"replacement-key":"stored-guest-key"));
  assert(!strcmp(_nvram_get("rt_ssid"),"main-sentinel")&&!strcmp(_nvram_get("rt_iot_ssid"),"iot-sentinel"));
  wr_modern_guest_batch_wipe(&packet,sizeof(packet));assert(wr_nvram_zero_bytes(&packet,sizeof(packet)));
  /* Invalid public data must not read a key or modify caller output. */
  depth=1;for(i=0;i<13;i++){
   snprintf(key,sizeof(key),"%s_guest_%s",guest_band,wr_modern_guest_fields[i]);
   assert(!_nvram_set(key,guest_old[i],0));
  }depth=0;
  guest_values[0]="invalid";memset(&packet,0x5a,sizeof(packet));before=packet;guest_secret_reads=0;
  assert(wr_modern_guest_build_batch(&packet,guest_cgi,guest_nv,NULL,&reason)!=WR_SHARED_WIFI_OK);
  assert(!guest_secret_reads&&!memcmp(&packet,&before,sizeof(packet)));
 }
 puts("PASS Guest planner -> actual decoder/core for both bands keep/change/open: public CAS, keep check-only, dormant key retained, Main/IoT unchanged, invalid output preserved");
}
