/* Full Guest value preflight candidate. Not CGI/persistence integration.
 * All public values are checked before a keep-key read. Main/shared credentials
 * are outside this namespace. The caller must own/clear the successful plan.
 */
#ifndef WR_MODERN_GUEST_REQUEST_H
#define WR_MODERN_GUEST_REQUEST_H
#include "validate.h"
#include "guest-schedule.h"
struct wr_modern_guest_request {
 const char *band,*enable,*ssid,*closed,*auth,*wpa_mode,*crypto;
 const char *lan_isolate,*ap_isolate,*macrule,*rate,*days,*weekday,*weekend;
 const char *intent,*password;
};
struct wr_modern_guest_plan { int keep,has_key;char band[3];char key[65]; };
typedef const char *(*wr_modern_guest_secret_read)(void *,const char *);
static void wr_modern_guest_clear(struct wr_modern_guest_plan *plan)
{
 volatile unsigned char *p;size_t i;
 if(!plan)return;
 p=(volatile unsigned char *)plan;
 for(i=0;i<sizeof(*plan);i++)p[i]=0;
}
static int wr_modern_guest_boolean(const char *v)
{return v&&(!strcmp(v,"0")||!strcmp(v,"1"));}
static enum wr_shared_wifi_result wr_modern_guest_prepare(
 struct wr_modern_guest_plan *out,const struct wr_modern_guest_request *r,
 wr_modern_guest_secret_read read_secret,void *context)
{
 struct wr_modern_guest_plan next;
 struct wr_shared_wifi_fields fields;
 enum wr_shared_wifi_result result;
 const char *key;
 if(!out||!r||!r->band||!r->auth||!r->intent)return WR_SHARED_WIFI_MISSING;
 if(strcmp(r->band,"rt")&&strcmp(r->band,"wl"))return WR_SHARED_WIFI_SECURITY;
 if(!wr_modern_guest_boolean(r->enable)||!wr_modern_guest_boolean(r->closed)||
    !wr_modern_guest_boolean(r->lan_isolate)||!wr_modern_guest_boolean(r->ap_isolate)||
    !wr_modern_guest_boolean(r->macrule))return WR_SHARED_WIFI_SECURITY;
 if(!r->rate||strlen(r->rate)!=1||r->rate[0]<'0'||r->rate[0]>'9')return WR_SHARED_WIFI_SECURITY;
 if(wr_modern_guest_schedule_validate(r->days,r->weekday,r->weekend)!=WR_GUEST_SCHEDULE_OK)return WR_SHARED_WIFI_SECURITY;
 if(r->wpa_mode&&strcmp(r->wpa_mode,"0")&&strcmp(r->wpa_mode,"1")&&strcmp(r->wpa_mode,"2"))return WR_SHARED_WIFI_SECURITY;
 if(r->crypto&&strcmp(r->crypto,"aes")&&strcmp(r->crypto,"tkip")&&strcmp(r->crypto,"tkip+aes"))return WR_SHARED_WIFI_SECURITY;
 if(strcmp(r->intent,"keep")&&strcmp(r->intent,"change"))return WR_SHARED_WIFI_SECURITY;
 if(!strcmp(r->intent,"keep")&&r->password)return WR_SHARED_WIFI_SECURITY;
 fields=(struct wr_shared_wifi_fields){r->ssid,r->auth,"0",r->wpa_mode,r->crypto,"validation-only"};
 result=wr_shared_wifi_validate(&fields);
 if(result!=WR_SHARED_WIFI_OK)return result;
 memset(&next,0,sizeof(next));memcpy(next.band,r->band,3);next.keep=!strcmp(r->intent,"keep");
 if(!strcmp(r->auth,"open")) {
  /* Open keeps any dormant stored key; no key read or clearing operation. */
  if(!next.keep||r->password)return WR_SHARED_WIFI_SECURITY;
 } else {
  if(next.keep) {
   if(!read_secret)return WR_SHARED_WIFI_MISSING;
   key=read_secret(context,!strcmp(r->band,"rt")?"rt_guest_wpa_psk":"wl_guest_wpa_psk");
  } else key=r->password;
  fields.password=key;result=wr_shared_wifi_validate(&fields);
  if(result!=WR_SHARED_WIFI_OK)return result;
  next.has_key=1;memcpy(next.key,key,strlen(key)+1);
 }
 *out=next;wr_modern_guest_clear(&next);
 return WR_SHARED_WIFI_OK;
}
#endif
