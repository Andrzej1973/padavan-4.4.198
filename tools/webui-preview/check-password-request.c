#include "password-request.h"
#include <assert.h>
#include <stdio.h>
struct fixture {const char *band,*version,*expected,*stored,*sid,*mode,*script,*intent,*posted,*opposite,*selector;int secret_reads;};
static const char *cgi(void *context,const char *name) {
 struct fixture *f=context;
 if(!strcmp(name,"wr_modern_wifi_version"))return f->version;
 if(!strcmp(name,"wr_modern_wifi_band"))return f->band;
 if(!strcmp(name,"wr_modern_expected_shared"))return f->expected;
 if(!strcmp(name,"wr_modern_password_intent"))return f->intent;
 if(!strcmp(name,"wr_wifi_shared"))return f->selector;
 if(!strcmp(name,"sid_list"))return f->sid;
 if(!strcmp(name,"action_mode"))return f->mode;
 if(!strcmp(name,"action_script"))return f->script;
 if(!strcmp(name,"wl_ssid"))return f->opposite;
 if(!strcmp(name,"rt_ssid"))return "Stored";
 if(!strcmp(name,"rt_auth_mode"))return "psk";
 if(!strcmp(name,"rt_wep_x"))return "0";
 if(!strcmp(name,"rt_wpa_mode"))return "2";
 if(!strcmp(name,"rt_crypto"))return "aes";
 if(!strcmp(name,"rt_wpa_psk"))return f->posted;
 return NULL;
}
static const char *nv(void *context,const char *name) {
 struct fixture *f=context;
 if(!strcmp(name,"wr_wifi_shared"))return f->stored;
 assert(!strcmp(name,"rt_wpa_psk"));f->secret_reads++;return "stored-passphrase";
}
static void rejected(struct fixture *f) {
 struct wr_modern_password_plan out,before;int reads=f->secret_reads;
 memset(&out,0x5a,sizeof(out));before=out;
 assert(wr_modern_password_request(&out,cgi,nv,f)!=WR_SHARED_WIFI_OK);
 assert(f->secret_reads==reads && !memcmp(&out,&before,sizeof(out)));
}
int main(void) {
 struct fixture f={"rt","1","0","0","WLANConfig11b;"," Apply ","","keep",NULL,NULL,NULL,0};
 struct wr_modern_password_plan out;
 assert(wr_modern_password_request(&out,cgi,nv,&f)==WR_SHARED_WIFI_OK);
 assert(f.secret_reads==1 && !strcmp(out.value,"stored-passphrase"));wr_modern_password_clear(&out);
 f.version="2";rejected(&f);f.version="1";
 f.band="ra2";rejected(&f);f.band="rt";
 f.expected="1";rejected(&f);f.expected="0";
 f.sid="WLANConfig11b;FakeWLANConfig11a;";rejected(&f);f.sid="WLANConfig11b;";
 f.mode="Update";rejected(&f);f.mode=" Apply ";
 f.script="arbitrary";rejected(&f);f.script="";
 f.opposite="other-band";rejected(&f);f.opposite=NULL;
 f.selector="0";rejected(&f);f.selector=NULL;
 f.posted="";rejected(&f);f.posted=NULL;
 f.stored=f.expected="1";rejected(&f);
 f.sid="WLANConfig11b;WLANConfig11a;";
 assert(wr_modern_password_request(&out,cgi,nv,&f)==WR_SHARED_WIFI_OK);wr_modern_password_clear(&out);
 f.intent="change";f.posted="new-passphrase";
 {int reads=f.secret_reads;assert(wr_modern_password_request(&out,cgi,nv,&f)==WR_SHARED_WIFI_OK);assert(f.secret_reads==reads);}
 wr_modern_password_clear(&out);
 puts("PASS credential preflight: exact scope/version/action/services, stale shared flag, opposite-band fields, no hidden selector, no secret reads on metadata rejection; not persistence integration");return 0;
}
