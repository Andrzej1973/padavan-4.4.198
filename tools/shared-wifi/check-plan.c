#include "plan.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 struct wr_shared_wifi_request r;
 struct wr_shared_wifi_plan out,before;
 int band;
 memset(&r,0,sizeof(r));memset(&out,0x5a,sizeof(out));before=out;
 r.source_band=-1;
 assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_OK&&out.mode==WR_SHARED_INDEPENDENT);
 for(band=0;band<2;band++){
  memset(&r,0,sizeof(r));r.selector="1";r.source_band=band;r.changed[band]=1;r.service[0]=r.service[1]=1;
  r.fields[band]=(struct wr_shared_wifi_fields){"Home","psk","0","2","aes","password"};
  assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_OK&&out.mode==WR_SHARED_SYNC&&out.source_band==band);
  r.stored_enabled=1;r.selector=NULL;assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_OK);
  r.fields[band].password="bad";out=before;assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_PASSWORD);assert(!memcmp(&out,&before,sizeof(out)));
  r.selector="0";assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_OK&&out.mode==WR_SHARED_DISABLE_KEEP);
 }
 memset(&r,0,sizeof(r));r.stored_enabled=1;r.source_band=-1;
 assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_OK&&out.mode==WR_SHARED_INDEPENDENT&&out.enabled==1);
 r.selector="garbage";out=before;assert(wr_shared_wifi_make_plan(&r,&out)!=WR_SHARED_WIFI_OK);assert(!memcmp(&out,&before,sizeof(out)));
 memset(&r,0,sizeof(r));r.selector="1";r.source_band=-1;assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_MISSING);
 r.changed[0]=r.changed[1]=1;assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_SECURITY);
 r.source_band=0;r.service[0]=r.service[1]=1;r.fields[0]=(struct wr_shared_wifi_fields){"Home","open","0",NULL,NULL,NULL};r.fields[1]=r.fields[0];
 assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_OK);
 r.fields[1].ssid="Other";assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_SECURITY);
 r.changed[1]=0;r.service[1]=0;assert(wr_shared_wifi_make_plan(&r,&out)==WR_SHARED_WIFI_MISSING);
 puts("PASS shared Wi-Fi plan: both sources, preservation modes, malformed input, conflict rejection, unchanged output on rejection");return 0;
}
