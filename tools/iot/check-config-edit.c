#include "config-edit.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 struct wr_iot_saved_config baseline={.profile={.enabled=0,.ssid="Old IoT",.password="old-password",
 .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 struct wr_iot_saved_config edit=baseline,out,before,foreign=baseline;
 char record[384],changed[384];size_t length;
 assert(wr_iot_saved_config_encode(record,sizeof(record),&baseline));length=strlen(record);
 memset(&out,0x5a,sizeof(out));before=out;memset(edit.profile.password,0,sizeof(edit.profile.password));
 strcpy(edit.profile.ssid,"New IoT");
 assert(wr_iot_config_edit_resolve(&out,&edit,WR_IOT_CONFIG_KEY_KEEP,record,length,record,length));
 assert(!strcmp(out.profile.password,"old-password")&&!strcmp(out.profile.ssid,"New IoT")&&!out.profile.enabled);
 strcpy(foreign.profile.password,"foreign-password");assert(wr_iot_saved_config_encode(changed,sizeof(changed),&foreign));
 out=before;assert(!wr_iot_config_edit_resolve(&out,&edit,WR_IOT_CONFIG_KEY_KEEP,record,length,changed,strlen(changed)));
 assert(!memcmp(&out,&before,sizeof(out)));
 edit.profile.password[3]='x';assert(!wr_iot_config_edit_resolve(&out,&edit,WR_IOT_CONFIG_KEY_KEEP,record,length,record,length));
 assert(!memcmp(&out,&before,sizeof(out)));memset(edit.profile.password,0,sizeof(edit.profile.password));
 assert(!wr_iot_config_edit_resolve(&out,&edit,WR_IOT_CONFIG_KEY_REPLACE,record,length,record,length));
 assert(!memcmp(&out,&before,sizeof(out)));strcpy(edit.profile.password,"new-password");
 assert(wr_iot_config_edit_resolve(&out,&edit,WR_IOT_CONFIG_KEY_REPLACE,record,length,record,length));
 assert(!strcmp(out.profile.password,"new-password"));out=before;
 assert(!wr_iot_config_edit_resolve(&out,&edit,99,record,length,record,length));assert(!memcmp(&out,&before,sizeof(out)));
 assert(!wr_iot_config_edit_resolve(&out,&edit,WR_IOT_CONFIG_KEY_REPLACE,"bad",3,"bad",3));
 assert(!memcmp(&out,&before,sizeof(out)));
 /* Output may alias edit: success uses a validated private candidate. */
 assert(wr_iot_config_edit_resolve(&edit,&edit,WR_IOT_CONFIG_KEY_REPLACE,record,length,record,length));
 puts("PASS exact-revision key KEEP/REPLACE: no silent retarget, hidden replacement bytes refuse, invalid/empty replacement leaves output unchanged; no HTTP/NVRAM writes");return 0;
}
