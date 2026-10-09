#include "profile-line.h"
#include <assert.h>
#include <stdio.h>
int main(void){char out[256],before[256];
 assert(wr_iot_profile_line(out,sizeof(out),"AuthMode=WPA2PSK;OPEN\n","IoT","password",1));assert(!strcmp(out,"AuthMode=WPA2PSK;OPEN;WPA2PSK\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"BssidNum=2\n","IoT","password",1));assert(!strcmp(out,"BssidNum=3\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"SSID3=\n","IoT","password",1));assert(!strcmp(out,"SSID3=IoT\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"WPAPSK3=\n","IoT","password",1));assert(!strcmp(out,"WPAPSK3=password\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"HT_GI=1;1\n","IoT","password",1));assert(!strcmp(out,"HT_GI=1;1\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"APCwmin=4;4;3;2\n","IoT","password",1));assert(!strcmp(out,"APCwmin=4;4;3;2\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"SSID3=\n",NULL,NULL,0));assert(!strcmp(out,"SSID3=\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"SSID1=Main\n","IoT","password",1));assert(!strcmp(out,"SSID1=Main\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"WPAPSK2=guest-password\n","IoT","password",1));assert(!strcmp(out,"WPAPSK2=guest-password\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"HT_BW=1\n","IoT","password",1));assert(!strcmp(out,"HT_BW=1\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"HT_MCS=33;15\n","IoT","password",1));assert(!strcmp(out,"HT_MCS=33;15;33\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"NoForwarding=0;1\n","IoT","password",1));assert(!strcmp(out,"NoForwarding=0;1;1\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"BndStrgBssIdx=1;0\n","IoT","password",1));assert(!strcmp(out,"BndStrgBssIdx=1;0;0\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"BndStrgBssIdx=0;0\n","IoT","password",1));assert(!strcmp(out,"BndStrgBssIdx=0;0;0\n"));
 assert(wr_iot_profile_line(out,sizeof(out),"BndStrgBssIdx=1;0\n",NULL,NULL,0));assert(!strcmp(out,"BndStrgBssIdx=1;0\n"));
 memset(out,0x5a,sizeof(out));memcpy(before,out,sizeof(out));
 assert(!wr_iot_profile_line(out,sizeof(out),"BssidNum=3\n","IoT","password",1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_profile_line(out,sizeof(out),"SSID3=\n","IoT","short",1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_profile_line(out,4,"SSID3=\n","IoT","password",1));assert(!memcmp(out,before,sizeof(out)));
 puts("PASS IoT candidate profile lines: explicit per-BSS fields, shared radio/QoS untouched, OFF unchanged, invalid output rejected before writes");return 0;}
