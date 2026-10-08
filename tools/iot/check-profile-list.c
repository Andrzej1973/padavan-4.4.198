#include "profile-list.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 char out[64],before[64];
 assert(wr_iot_profile_list(out,sizeof(out),"WPA2PSK;OPEN","WPA2PSK",1));
 assert(!strcmp(out,"WPA2PSK;OPEN;WPA2PSK"));
 assert(wr_iot_profile_list(out,sizeof(out),"AES;NONE","AES",1));assert(!strcmp(out,"AES;NONE;AES"));
 assert(wr_iot_profile_list(out,sizeof(out),"0;1","1",1));assert(!strcmp(out,"0;1;1"));
 assert(wr_iot_profile_list(out,sizeof(out),"0;1",NULL,0));assert(!strcmp(out,"0;1"));
 assert(wr_iot_profile_list(out,sizeof(out),"legacy;four;entry;list",NULL,0));assert(!strcmp(out,"legacy;four;entry;list"));
 memset(out,0x5a,sizeof(out));memcpy(before,out,sizeof(out));
 assert(!wr_iot_profile_list(out,sizeof(out),"0;1","1;0",1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_profile_list(out,sizeof(out),"0;1","1\nBssidNum=9",1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_profile_list(out,sizeof(out),"0;1;2","1",1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_profile_list(out,5,"0;1","1",1));assert(!memcmp(out,before,sizeof(out)));
 assert(wr_iot_profile_list(out,sizeof(out),";","",1));assert(!strcmp(out,";;"));
 puts("PASS IoT per-BSS list extension: first two entries preserved, OFF unchanged, bounds and malformed input rejection before writes");return 0;
}
