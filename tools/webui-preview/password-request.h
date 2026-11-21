/* Modern credential-request preflight prototype; no persistence and not CGI-wired. */
#ifndef WR_MODERN_PASSWORD_REQUEST_H
#define WR_MODERN_PASSWORD_REQUEST_H
#include "password-intent.h"
typedef const char *(*wr_modern_request_read)(void *,const char *);
static enum wr_shared_wifi_result wr_modern_password_request(
 struct wr_modern_password_plan *out,wr_modern_request_read cgi,
 wr_modern_request_read nv,void *context)
{
 const char *band,*version,*expected,*stored,*sid,*mode,*script,*intent;
 const char *values[6];char key[32];unsigned int i;
 struct wr_shared_wifi_fields fields;
 static const char *const names[]={"ssid","auth_mode","wep_x","wpa_mode","crypto","wpa_psk"};
 if(!out||!cgi||!nv)return WR_SHARED_WIFI_MISSING;
 version=cgi(context,"wr_modern_wifi_version");
 band=cgi(context,"wr_modern_wifi_band");
 if(!version||strcmp(version,"1")||!band||
    (strcmp(band,"rt")&&strcmp(band,"wl")))return WR_SHARED_WIFI_SECURITY;
 expected=cgi(context,"wr_modern_expected_shared");stored=nv(context,"wr_wifi_shared");
 if(!expected||!stored||(strcmp(expected,"0")&&strcmp(expected,"1"))||strcmp(expected,stored))return WR_SHARED_WIFI_SECURITY;
 /* A band credential request cannot change shared-mode ownership. */
 if(cgi(context,"wr_wifi_shared")||cgi(context,"wr_wifi_source"))return WR_SHARED_WIFI_SECURITY;
 sid=cgi(context,"sid_list");mode=cgi(context,"action_mode");script=cgi(context,"action_script");
 if(!mode||strcmp(mode," Apply ")||(script&&*script)||!sid)return WR_SHARED_WIFI_SECURITY;
 if(!strcmp(stored,"1")) {
  if(strcmp(sid,"WLANConfig11b;WLANConfig11a;")&&strcmp(sid,"WLANConfig11a;WLANConfig11b;"))return WR_SHARED_WIFI_SECURITY;
 } else if(strcmp(sid,!strcmp(band,"rt")?"WLANConfig11b;":"WLANConfig11a;"))return WR_SHARED_WIFI_SECURITY;
 for(i=0;i<6;i++) {
  strcpy(key,!strcmp(band,"rt")?"wl_":"rt_");strcat(key,names[i]);
  if(cgi(context,key))return WR_SHARED_WIFI_SECURITY;
  strcpy(key,band);strcat(key,"_");strcat(key,names[i]);values[i]=cgi(context,key);
 }
 fields=(struct wr_shared_wifi_fields){values[0],values[1],values[2],values[3],values[4],values[5]};
 intent=cgi(context,"wr_modern_password_intent");
 return wr_modern_password_prepare(out,intent,band,&fields,nv,context);
}
#endif
