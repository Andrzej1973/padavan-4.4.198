#include <assert.h>
#include <stdio.h>
#include "guest-request.h"
static int reads;static char saved[65]="guest-password";
static const char *read_key(void *context,const char *name)
{
 assert(!strcmp(name,(const char *)context));reads++;return saved;
}
int main(void)
{
 struct wr_modern_guest_request r={"rt","1","Guest","0","psk","2","aes","1","1","0","0","0111110","08002200","10002300","keep",NULL};
 struct wr_modern_guest_plan out,before;
 memset(&out,0x5a,sizeof(out));before=out;
 assert(wr_modern_guest_prepare(&out,&r,read_key,"rt_guest_wpa_psk")==WR_SHARED_WIFI_OK);
 assert(reads==1&&out.keep&&out.has_key&&!strcmp(out.key,"guest-password"));
 saved[0]='X';assert(!strcmp(out.key,"guest-password"));saved[0]='g';
 r.band="wl";assert(wr_modern_guest_prepare(&out,&r,read_key,"wl_guest_wpa_psk")==WR_SHARED_WIFI_OK);assert(reads==2);
 const char **fields[]={&r.enable,&r.closed,&r.lan_isolate,&r.ap_isolate,&r.macrule,&r.rate,&r.days,&r.weekday,&r.weekend,&r.auth,&r.wpa_mode,&r.crypto,&r.intent,&r.band};
 for(unsigned int i=0;i<sizeof(fields)/sizeof(fields[0]);i++){
  const char *keep=*fields[i];*fields[i]="bad";out=before;
  assert(wr_modern_guest_prepare(&out,&r,read_key,"wl_guest_wpa_psk")!=WR_SHARED_WIFI_OK);
  assert(!memcmp(&out,&before,sizeof(out))&&reads==2);*fields[i]=keep;
 }
 r.ssid="";assert(wr_modern_guest_prepare(&out,&r,read_key,"wl_guest_wpa_psk")==WR_SHARED_WIFI_SSID);assert(reads==2);r.ssid="Guest";
 r.password="";assert(wr_modern_guest_prepare(&out,&r,read_key,"wl_guest_wpa_psk")!=WR_SHARED_WIFI_OK);assert(reads==2);
 r.intent="change";r.password="new-guest-password";
 assert(wr_modern_guest_prepare(&out,&r,NULL,NULL)==WR_SHARED_WIFI_OK);assert(!out.keep&&out.has_key&&!strcmp(out.key,r.password)&&reads==2);
 r.password="short";out=before;assert(wr_modern_guest_prepare(&out,&r,NULL,NULL)==WR_SHARED_WIFI_PASSWORD);assert(!memcmp(&out,&before,sizeof(out)));
 r.auth="open";r.intent="keep";r.password=NULL;r.wpa_mode=NULL;r.crypto=NULL;
 assert(wr_modern_guest_prepare(&out,&r,NULL,NULL)==WR_SHARED_WIFI_OK);assert(out.keep&&!out.has_key&&!out.key[0]&&reads==2);
 r.intent="change";assert(wr_modern_guest_prepare(&out,&r,NULL,NULL)!=WR_SHARED_WIFI_OK);
 wr_modern_guest_clear(&out);const unsigned char *bytes=(const unsigned char *)&out;for(unsigned int i=0;i<sizeof(out);i++)assert(bytes[i]==0);
 puts("PASS Guest request values: public checks before exact band Guest key read, owned keep/change, open preserves dormant key, reject unchanged, wipe; not CGI/persistence");
 return 0;
}
