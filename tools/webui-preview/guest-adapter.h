/* Guest metadata/field adapter candidate. Not installed in production CGI. */
#ifndef WR_MODERN_GUEST_ADAPTER_H
#define WR_MODERN_GUEST_ADAPTER_H
#include <stdio.h>
#include "guest-request.h"
typedef const char *(*wr_modern_guest_read)(void *,const char *);
static const char *wr_modern_guest_fields[]={
 "enable","ssid","closed","auth_mode","wpa_mode","crypto","lan_isolate",
 "ap_isolate","macrule","mcs_mode","date_x","time_x","time2_x","wpa_psk"
};
/* Public snapshot comparison is an optimistic precondition, not a lock/CAS.
 * Secret keep/change handling still uses the current key at admission. */
static int wr_modern_guest_snapshot_matches(const char *band,
 wr_modern_guest_read cgi,wr_modern_guest_read nv,void *context)
{
 char expected_key[64],stored_key[40];unsigned int i;
 for(i=0;i<13;i++) {
  const char *expected,*stored;
  snprintf(expected_key,sizeof(expected_key),"wr_modern_guest_expected_%s",wr_modern_guest_fields[i]);
  expected=cgi(context,expected_key);if(!expected)return 0;
  snprintf(stored_key,sizeof(stored_key),"%s_guest_%s",band,wr_modern_guest_fields[i]);
  stored=nv(context,stored_key);if(!stored||strcmp(expected,stored))return 0;
 }
 return 1;
}
enum wr_modern_guest_error {WR_GUEST_ERROR_NONE,WR_GUEST_ERROR_INVALID,WR_GUEST_ERROR_RELOAD};
static enum wr_shared_wifi_result wr_modern_guest_admit_reason(
 struct wr_modern_guest_plan *out,wr_modern_guest_read cgi,
 wr_modern_guest_read nv,void *context,enum wr_modern_guest_error *reason)
{
 struct wr_modern_guest_request r;const char *band,*value,*values[14];char key[40];unsigned int i;
 enum wr_shared_wifi_result result;
 if(reason)*reason=WR_GUEST_ERROR_INVALID;
 if(!out||!cgi||!nv)return WR_SHARED_WIFI_MISSING;
 value=cgi(context,"wr_modern_guest_version");
 if(!value||strcmp(value,"1"))return WR_SHARED_WIFI_SECURITY;
 band=cgi(context,"wr_modern_guest_band");
 if(!band||(strcmp(band,"rt")&&strcmp(band,"wl")))return WR_SHARED_WIFI_SECURITY;
 value=cgi(context,"action_mode");if(!value||strcmp(value," Apply "))return WR_SHARED_WIFI_SECURITY;
 value=cgi(context,"action_script");if(value&&*value)return WR_SHARED_WIFI_SECURITY;
 value=cgi(context,"sid_list");
 if(!value||strcmp(value,!strcmp(band,"rt")?"WLANConfig11b;":"WLANConfig11a;"))return WR_SHARED_WIFI_SECURITY;
 if(cgi(context,"wr_modern_wifi_version")||cgi(context,"wr_wifi_shared")||cgi(context,"wr_wifi_source"))return WR_SHARED_WIFI_SECURITY;
 for(i=0;i<14;i++) {
  snprintf(key,sizeof(key),"%s_guest_%s",!strcmp(band,"rt")?"wl":"rt",wr_modern_guest_fields[i]);
  if(cgi(context,key))return WR_SHARED_WIFI_SECURITY;
  snprintf(key,sizeof(key),"%s_guest_%s",band,wr_modern_guest_fields[i]);values[i]=cgi(context,key);
 }
 r=(struct wr_modern_guest_request){band,values[0],values[1],values[2],values[3],values[4],values[5],values[6],values[7],values[8],values[9],values[10],values[11],values[12],cgi(context,"wr_modern_guest_password_intent"),values[13]};
 if(!wr_modern_guest_snapshot_matches(band,cgi,nv,context)){
  if(reason)*reason=WR_GUEST_ERROR_RELOAD;
  return WR_SHARED_WIFI_SECURITY;
 }
 result=wr_modern_guest_prepare(out,&r,nv,context);
 if(result==WR_SHARED_WIFI_OK&&reason)*reason=WR_GUEST_ERROR_NONE;
 return result;
}
static inline enum wr_shared_wifi_result wr_modern_guest_admit(
 struct wr_modern_guest_plan *out,wr_modern_guest_read cgi,
 wr_modern_guest_read nv,void *context)
{return wr_modern_guest_admit_reason(out,cgi,nv,context,NULL);}
/* Call only for an admitted request and selected band. All other table entries
 * are dropped, including files, main/IoT keys and shared selector. Open auth
 * with no key plan cannot clear dormant credentials. */
static const char *wr_modern_guest_persist_value(
 const struct wr_modern_guest_plan *plan,const char *name,const char *value)
{
 char key[40];unsigned int i;
 if(!plan||!name||(memcmp(plan->band,"rt",3)&&memcmp(plan->band,"wl",3)))return NULL;
 for(i=0;i<14;i++) {
  snprintf(key,sizeof(key),"%s_guest_%s",plan->band,wr_modern_guest_fields[i]);
  if(!strcmp(name,key))return i==13?(plan->has_key?plan->key:NULL):value;
 }
 return NULL;
}
#endif
