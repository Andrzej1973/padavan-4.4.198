#include <assert.h>
#include <stdio.h>
#include "guest-adapter.h"
static const char *version="1",*band="rt",*mode=" Apply ",*sid="WLANConfig11b;",*script="",*inject,*omit;
static int reads;
static const char *values[]={"1","Guest","0","psk","2","aes","1","1","0","0","0111110","08002200","10002300",NULL};
static const char *cgi(void *context,const char *key)
{
 char name[40];unsigned int i;(void)context;
 if(omit&&!strcmp(omit,key))return NULL;
 if(inject&&!strcmp(inject,key))return "injected";
 if(!strcmp(key,"wr_modern_guest_version"))return version;
 if(!strcmp(key,"wr_modern_guest_band"))return band;
 if(!strcmp(key,"wr_modern_guest_password_intent"))return "keep";
 if(!strcmp(key,"action_mode"))return mode;
 if(!strcmp(key,"action_script"))return script;
 if(!strcmp(key,"sid_list"))return sid;
 for(i=0;i<14;i++){snprintf(name,sizeof(name),"%s_guest_%s",band,wr_modern_guest_fields[i]);if(!strcmp(name,key))return values[i];}
 for(i=0;i<13;i++){snprintf(name,sizeof(name),"wr_modern_guest_expected_%s",wr_modern_guest_fields[i]);if(!strcmp(name,key))return values[i];}
 return NULL;
}
static const char *nv(void *context,const char *key)
{
 char name[40];(void)context;snprintf(name,sizeof(name),"%s_guest_wpa_psk",band);
 if(!strcmp(key,name)){reads++;return "stored-guest-key";}
 for(unsigned int i=0;i<13;i++){snprintf(name,sizeof(name),"%s_guest_%s",band,wr_modern_guest_fields[i]);if(!strcmp(key,name))return values[i];}
 assert(0);return NULL;
}
int main(void)
{
 struct wr_modern_guest_plan out,before;char name[40];unsigned int i;
 memset(&before,0x5a,sizeof(before));
 assert(wr_modern_guest_admit(&out,cgi,nv,NULL)==WR_SHARED_WIFI_OK);assert(reads==1&&!strcmp(out.band,"rt"));
 {
  struct wr_modern_guest_plan accepted=out;
  for(unsigned int field=0;field<13;field++){
   char expected[64];snprintf(expected,sizeof(expected),"wr_modern_guest_expected_%s",wr_modern_guest_fields[field]);
   enum wr_modern_guest_error reason=WR_GUEST_ERROR_NONE;
   inject=expected;out=before;assert(wr_modern_guest_admit_reason(&out,cgi,nv,NULL,&reason)!=WR_SHARED_WIFI_OK&&reason==WR_GUEST_ERROR_RELOAD);assert(reads==1&&!memcmp(&out,&before,sizeof(out)));inject=NULL;
   omit=expected;out=before;assert(wr_modern_guest_admit_reason(&out,cgi,nv,NULL,&reason)!=WR_SHARED_WIFI_OK&&reason==WR_GUEST_ERROR_RELOAD);assert(reads==1&&!memcmp(&out,&before,sizeof(out)));omit=NULL;
  }
  out=accepted;
 }
 for(i=0;i<14;i++){
  snprintf(name,sizeof(name),"rt_guest_%s",wr_modern_guest_fields[i]);
  const char *got=wr_modern_guest_persist_value(&out,name,"posted");assert(got);
  assert(!strcmp(got,i==13?"stored-guest-key":"posted"));
 }
 const char *blocked[]={"rt_ssid","rt_wpa_psk","rt_radio_x","rt_iot_enable","wr_wifi_shared","wl_guest_ssid","wl_guest_wpa_psk","scripts.ap_script.sh","rt_guest_ssid_extra","rt_guest_"};
 for(i=0;i<sizeof(blocked)/sizeof(blocked[0]);i++)assert(!wr_modern_guest_persist_value(&out,blocked[i],"bad"));
 const char *injected[]={"wr_modern_wifi_version","wr_wifi_shared","wr_wifi_source","wr_modern_guest_expected_ssid","wl_guest_ssid","wl_guest_wpa_psk"};
 for(i=0;i<sizeof(injected)/sizeof(injected[0]);i++){
  inject=injected[i];out=before;assert(wr_modern_guest_admit(&out,cgi,nv,NULL)!=WR_SHARED_WIFI_OK);assert(reads==1&&!memcmp(&out,&before,sizeof(out)));
 }inject=NULL;
 const char **metadata[]={&version,&band,&mode,&sid,&script};
 for(i=0;i<sizeof(metadata)/sizeof(metadata[0]);i++){
  const char *saved=*metadata[i];*metadata[i]="bad";out=before;
  assert(wr_modern_guest_admit(&out,cgi,nv,NULL)!=WR_SHARED_WIFI_OK);assert(reads==1&&!memcmp(&out,&before,sizeof(out)));*metadata[i]=saved;
 }
 band="wl";sid="WLANConfig11a;";
 assert(wr_modern_guest_admit(&out,cgi,nv,NULL)==WR_SHARED_WIFI_OK);assert(reads==2&&!strcmp(out.band,"wl"));
 assert(!wr_modern_guest_persist_value(&out,"rt_guest_ssid","bad"));
 assert(wr_modern_guest_persist_value(&out,"wl_guest_ssid","Good"));
 wr_modern_guest_clear(&out);
 puts("PASS Guest adapter candidate: exact metadata/band/services, no secret on reject, opposite Guest rejected, persistence namespace bound to owned plan; not installed CGI");
 return 0;
}
