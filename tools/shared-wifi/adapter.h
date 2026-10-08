/* CGI/NVRAM read adapter. Persistence stays in the existing apply loop. */
#ifndef WR_SHARED_WIFI_ADAPTER_H
#define WR_SHARED_WIFI_ADAPTER_H
#include "plan.h"
typedef const char *(*wr_shared_wifi_read)(void *,const char *);
struct wr_shared_wifi_adapter {
 struct wr_shared_wifi_plan plan;
 char saved[2][7][97]; /* includes encoded ssid2; snapshot before any writes */
};
static const char *const wr_shared_wifi_names[7]={"ssid","auth_mode","wep_x","wpa_mode","crypto","wpa_psk","ssid2"};
static int wr_shared_wifi_service(const char *list,const char *wanted) {
 const char *end;size_t n;if(!list)return 0;
 while(*list){end=strchr(list,';');if(!end)end=list+strlen(list);n=(size_t)(end-list);
  if(n==strlen(wanted)&&!strncmp(list,wanted,n))return 1;
  if(!*end)break;
  list=end+1;
 }return 0;
}
static void wr_shared_wifi_field_key(char *key,int band,int index) {
 strcpy(key,band?"wl_":"rt_");strcat(key,wr_shared_wifi_names[index]);
}
static enum wr_shared_wifi_result wr_shared_wifi_prepare(struct wr_shared_wifi_adapter *a,void *ctx,wr_shared_wifi_read cgi,wr_shared_wifi_read nv) {
 struct wr_shared_wifi_request r;
 struct wr_shared_wifi_adapter next;
 const char *v,*source,*sid,*values[2][6];char key[32];int band,i;
 enum wr_shared_wifi_result result;
 if(!a||!cgi||!nv)return WR_SHARED_WIFI_MISSING;
 memset(&r,0,sizeof(r));memset(&next,0,sizeof(next));r.source_band=-1;
 v=nv(ctx,"wr_wifi_shared");r.stored_enabled=v&&!strcmp(v,"1");r.selector=cgi(ctx,"wr_wifi_shared");
 source=cgi(ctx,"wr_wifi_source");if(source){if(!strcmp(source,"rt"))r.source_band=0;else if(!strcmp(source,"wl"))r.source_band=1;else return WR_SHARED_WIFI_SECURITY;}
 sid=cgi(ctx,"sid_list");r.service[0]=wr_shared_wifi_service(sid,"WLANConfig11b");r.service[1]=wr_shared_wifi_service(sid,"WLANConfig11a");
 for(band=0;band<2;band++){
  for(i=0;i<6;i++){wr_shared_wifi_field_key(key,band,i);values[band][i]=cgi(ctx,key);if(values[band][i])r.changed[band]=1;}
  r.fields[band]=(struct wr_shared_wifi_fields){values[band][0],values[band][1],values[band][2],values[band][3],values[band][4],values[band][5]};
 }
 result=wr_shared_wifi_make_plan(&r,&next.plan);if(result!=WR_SHARED_WIFI_OK)return result;
 if(next.plan.mode==WR_SHARED_DISABLE_KEEP){
  if(!r.service[0]||!r.service[1])return WR_SHARED_WIFI_MISSING;
  for(band=0;band<2;band++)for(i=0;i<7;i++){
   wr_shared_wifi_field_key(key,band,i);v=nv(ctx,key);if(!v)v="";
   if(strlen(v)>=sizeof(next.saved[band][i]))return WR_SHARED_WIFI_MISSING;
   strcpy(next.saved[band][i],v);
  }
 }
 *a=next;return WR_SHARED_WIFI_OK;
}
/* NULL means omit a field; shared ssid2 is generated from ssid by existing code. */
static const char *wr_shared_wifi_value(const struct wr_shared_wifi_adapter *a,const char *key,const char *ordinary) {
 int band,i;const char *suffix;
 const char *common[6]={a->plan.common.ssid,a->plan.common.auth,a->plan.common.wep,a->plan.common.wpa_mode,a->plan.common.crypto,a->plan.common.password};
 if(!strcmp(key,"wr_wifi_shared"))return a->plan.enabled?"1":"0";
 if(a->plan.mode==WR_SHARED_INDEPENDENT)return ordinary;
 if(!strncmp(key,"rt_",3))band=0;else if(!strncmp(key,"wl_",3))band=1;else return ordinary;
 suffix=key+3;for(i=0;i<7;i++)if(!strcmp(suffix,wr_shared_wifi_names[i])){
  if(a->plan.mode==WR_SHARED_DISABLE_KEEP)return a->saved[band][i];
  return i==6?NULL:common[i];
 }return ordinary;
}
#endif
