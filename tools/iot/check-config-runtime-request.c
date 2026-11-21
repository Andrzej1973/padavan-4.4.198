#include <assert.h>
#include <stdio.h>
#include "config-runtime-request.h"
int main(void)
{
 struct wr_iot_saved_config captured={.profile={.enabled=0,.ssid="Saved IoT",.password="saved-password",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}},resolved;
 struct wr_iot_request out,before;char record[WR_IOT_SAVED_CONFIG_MAX]={0};
 assert(wr_iot_saved_config_encode(record,sizeof(record),&captured));
 for(int enabled=0;enabled<=1;enabled++){
  resolved=captured;resolved.profile.enabled=enabled;
  assert(wr_iot_config_runtime_request(&out,&resolved,record));
  if(enabled)assert(!memcmp(&out,&resolved.profile,sizeof(out)));
  else {struct wr_iot_request zero={0};assert(!memcmp(&out,&zero,sizeof(out)));}
 }
 memset(&out,0x5a,sizeof(out));before=out;
 for(int field=0;field<4;field++){
  resolved=captured;resolved.profile.enabled=1;
  if(field==0)strcpy(resolved.profile.ssid,"Another IoT");
  if(field==1)strcpy(resolved.profile.password,"another-password");
  if(field==2)strcpy(resolved.profile.first,"192.168.50.21");
  if(field==3)resolved.profile.enabled=7;
  assert(!wr_iot_config_runtime_request(&out,&resolved,record));
  assert(!memcmp(&out,&before,sizeof(out)));
 }
 strcpy(record,"malformed");resolved=captured;
 assert(!wr_iot_config_runtime_request(&out,&resolved,record)&&!memcmp(&out,&before,sizeof(out)));
 puts("PASS runtime conversion: only enabled intent changes, exact captured profile required, OFF empty, altered SSID/key/range/malformed refuse unchanged; no activation or persistence");
}
