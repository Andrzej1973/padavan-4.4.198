#include "validate.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
 struct wr_shared_wifi_fields f={"Home","psk","0","2","aes","password"};
 char ssid[34],psk[66];
 assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_OK);
 assert(wr_shared_wifi_validate(NULL)==WR_SHARED_WIFI_MISSING);
 f.auth="radius";assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_SECURITY);
 f.auth="open";f.password=NULL;assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_OK);
 f.wep="1";assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_SECURITY);
 f.auth="psk";f.wep="0";f.password="short";assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_PASSWORD);
 memset(psk,'a',64);psk[64]=0;f.password=psk;assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_OK);
 psk[63]='g';assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_PASSWORD);
 f.password="password";memset(ssid,'a',32);ssid[32]=0;f.ssid=ssid;assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_OK);
 ssid[32]='a';ssid[33]=0;assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_SSID);
 f.ssid="";assert(wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_SSID);
 assert(wr_shared_wifi_text("\xf0\x9f\x8f\xa0",1,32));
 assert(!wr_shared_wifi_text("\xc0\x80",1,32));
 assert(!wr_shared_wifi_text("\xed\xa0\x80",1,32));
 assert(!wr_shared_wifi_text("\xf4\x90\x80\x80",1,32));
 assert(!wr_shared_wifi_text("\xe2\x82",1,32));
 assert(!wr_shared_wifi_text("a\n",1,32));
 puts("PASS shared Wi-Fi validation: bounds, UTF-8, security, raw PSK, no mutation API");return 0;
}
