#include "password-intent.h"
#include <assert.h>
#include <stdio.h>
struct fixture {int reads; const char *expected; char stored[65];};
static const char *read_secret(void *context,const char *key) {
 struct fixture *f=context;f->reads++;assert(!strcmp(key,f->expected));return f->stored;
}
int main(void) {
 struct fixture f={0,"rt_wpa_psk","stored-passphrase"};
 struct wr_shared_wifi_fields request={"Stored","psk","0","2","aes",NULL};
 struct wr_modern_password_plan plan,before;
 int reads;
 memset(&plan,0x5a,sizeof(plan));before=plan;
 assert(wr_modern_password_prepare(&plan,"keep","rt",&request,read_secret,&f)==WR_SHARED_WIFI_OK);
 assert(f.reads==1 && plan.keep && !strcmp(plan.value,"stored-passphrase"));
 strcpy(f.stored,"changed-after-snapshot");assert(!strcmp(plan.value,"stored-passphrase"));
 f.expected="wl_wpa_psk";
 assert(wr_modern_password_prepare(&plan,"keep","wl",&request,read_secret,&f)==WR_SHARED_WIFI_OK);
 assert(!strcmp(plan.value,f.stored));
 reads=f.reads;plan=before;request.password="";
 assert(wr_modern_password_prepare(&plan,"keep","wl",&request,read_secret,&f)==WR_SHARED_WIFI_SECURITY);
 assert(f.reads==reads && !memcmp(&plan,&before,sizeof(plan)));
 request.password="replacement-passphrase";
 assert(wr_modern_password_prepare(&plan,"change","rt",&request,read_secret,&f)==WR_SHARED_WIFI_OK);
 assert(f.reads==reads && !plan.keep && !strcmp(plan.value,request.password));
 plan=before;request.password="short";
 assert(wr_modern_password_prepare(&plan,"change","rt",&request,read_secret,&f)==WR_SHARED_WIFI_PASSWORD);
 assert(!memcmp(&plan,&before,sizeof(plan)));
 request.password=NULL;
 assert(wr_modern_password_prepare(&plan,"change","rt",&request,read_secret,&f)==WR_SHARED_WIFI_MISSING);
 assert(wr_modern_password_prepare(&plan,NULL,"rt",&request,read_secret,&f)==WR_SHARED_WIFI_MISSING);
 assert(wr_modern_password_prepare(&plan,"automatic","rt",&request,read_secret,&f)==WR_SHARED_WIFI_SECURITY);
 assert(wr_modern_password_prepare(&plan,"keep","ra2",&request,read_secret,&f)==WR_SHARED_WIFI_SECURITY);
 assert(f.reads==reads && !memcmp(&plan,&before,sizeof(plan)));
 request.ssid="";
 assert(wr_modern_password_prepare(&plan,"keep","wl",&request,read_secret,&f)==WR_SHARED_WIFI_SSID);
 assert(f.reads==reads);request.ssid="Stored";
 strcpy(f.stored,"short");
 assert(wr_modern_password_prepare(&plan,"keep","wl",&request,read_secret,&f)==WR_SHARED_WIFI_PASSWORD);
 assert(!memcmp(&plan,&before,sizeof(plan)));
 request.password="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
 assert(wr_modern_password_prepare(&plan,"change","rt",&request,NULL,NULL)==WR_SHARED_WIFI_OK);
 request.password="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
 plan=before;
 assert(wr_modern_password_prepare(&plan,"change","rt",&request,NULL,NULL)==WR_SHARED_WIFI_PASSWORD);
 assert(!memcmp(&plan,&before,sizeof(plan)));
 wr_modern_password_clear(&plan);
 {const unsigned char *bytes=(const unsigned char *)&plan;size_t i;for(i=0;i<sizeof(plan);i++)assert(bytes[i]==0);}
 puts("PASS explicit password intent: keep/change, exact band secret read, owned snapshot, no implicit fallback, validation, unchanged rejection, wipe; not CGI integration");
 return 0;
}
