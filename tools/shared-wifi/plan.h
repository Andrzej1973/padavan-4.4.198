/* Request planning only; no NVRAM mutation. Validate before the service loop. */
#ifndef WR_SHARED_WIFI_PLAN_H
#define WR_SHARED_WIFI_PLAN_H
#include "validate.h"
enum wr_shared_wifi_mode { WR_SHARED_INDEPENDENT, WR_SHARED_SYNC, WR_SHARED_DISABLE_KEEP };
struct wr_shared_wifi_request {
 int stored_enabled;
 const char *selector; /* NULL means preserve stored selector; otherwise exact 0/1. */
 int source_band; /* 0=2.4 GHz, 1=5 GHz; -1 means no explicit source. */
 int changed[2]; /* Any shared field submitted for this band. */
 int service[2]; /* Exact WLANConfig11b/a service-list membership. */
 struct wr_shared_wifi_fields fields[2]; /* Complete intended values, not unchecked fallbacks. */
};
struct wr_shared_wifi_plan {
 enum wr_shared_wifi_mode mode;
 int enabled, source_band;
 struct wr_shared_wifi_fields common;
};
static int wr_shared_wifi_equal(const struct wr_shared_wifi_fields *a,const struct wr_shared_wifi_fields *b) {
 const char *av[6]={a->ssid,a->auth,a->wep,a->wpa_mode,a->crypto,a->password};
 const char *bv[6]={b->ssid,b->auth,b->wep,b->wpa_mode,b->crypto,b->password};
 int i;for(i=0;i<6;i++){if(!av[i]||!bv[i]){if(av[i]!=bv[i])return 0;}else if(strcmp(av[i],bv[i]))return 0;}return 1;
}
static enum wr_shared_wifi_result wr_shared_wifi_make_plan(const struct wr_shared_wifi_request *r,struct wr_shared_wifi_plan *out) {
 struct wr_shared_wifi_plan plan;
 enum wr_shared_wifi_result result;
 int enabled,band;
 if(!r||!out)return WR_SHARED_WIFI_MISSING;
 enabled=r->stored_enabled!=0;
 if(r->selector){if(strcmp(r->selector,"0")&&strcmp(r->selector,"1"))return WR_SHARED_WIFI_SECURITY;enabled=!strcmp(r->selector,"1");}
 memset(&plan,0,sizeof(plan));plan.enabled=enabled;plan.source_band=-1;
 if(r->selector&&!enabled){plan.mode=WR_SHARED_DISABLE_KEEP;*out=plan;return WR_SHARED_WIFI_OK;}
 if(!enabled){plan.mode=WR_SHARED_INDEPENDENT;*out=plan;return WR_SHARED_WIFI_OK;}
 if(!r->changed[0]&&!r->changed[1]){
  if(r->selector)return WR_SHARED_WIFI_MISSING;
  plan.mode=WR_SHARED_INDEPENDENT;*out=plan;return WR_SHARED_WIFI_OK;
 }
 band=r->source_band;
 if(band==-1){if(r->changed[0]&&r->changed[1])return WR_SHARED_WIFI_SECURITY;band=r->changed[1]?1:0;}
 if(band<0||band>1||!r->changed[band]||!r->service[0]||!r->service[1])return WR_SHARED_WIFI_MISSING;
 result=wr_shared_wifi_validate(&r->fields[band]);if(result!=WR_SHARED_WIFI_OK)return result;
 if(r->changed[1-band]&&!wr_shared_wifi_equal(&r->fields[band],&r->fields[1-band]))return WR_SHARED_WIFI_SECURITY;
 plan.mode=WR_SHARED_SYNC;plan.source_band=band;plan.common=r->fields[band];*out=plan;return WR_SHARED_WIFI_OK;
}
#endif
