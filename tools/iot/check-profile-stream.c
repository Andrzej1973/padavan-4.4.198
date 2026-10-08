#include "profile-stream.h"
#include <assert.h>
#include <stdio.h>
static const char profile[]="Default\nBssidNum=2\nSSID1=Main\nSSID2=Guest\nSSID3=\nWPAPSK1=main-password\nWPAPSK2=guest-password\nWPAPSK3=\nAuthMode=WPA2PSK;OPEN\nEncrypType=AES;NONE\nWmmCapable=1;1\nDLSCapable=0;0\nNoForwarding=0;1\nHideSSID=0;0\nStationKeepAlive=0;0\nPreAuth=0;0\nIEEE8021X=0;0\nFixedTxMode=0;0\nHT_MCS=33;33\nHT_BW=1\nAPCwmin=4;4;3;2\n";
static FILE *source(const char *text){FILE *f=tmpfile();assert(f);assert(fputs(text,f)>=0);rewind(f);return f;}
int main(void){FILE *in,*out;char result[4096];size_t n;
 in=source(profile);out=tmpfile();assert(out);
 assert(wr_iot_profile_stream(in,out,"IoT","password",1));rewind(out);n=fread(result,1,sizeof(result)-1,out);result[n]=0;
 assert(strstr(result,"BssidNum=3\n"));assert(strstr(result,"SSID1=Main\nSSID2=Guest\nSSID3=IoT\n"));
 assert(strstr(result,"WPAPSK2=guest-password\nWPAPSK3=password\n"));assert(strstr(result,"HT_BW=1\n"));assert(strstr(result,"APCwmin=4;4;3;2\n"));fclose(in);fclose(out);
 in=source(profile);out=tmpfile();assert(out);assert(wr_iot_profile_stream(in,out,NULL,NULL,0));rewind(out);n=fread(result,1,sizeof(result)-1,out);result[n]=0;assert(!strcmp(result,profile));fclose(in);fclose(out);
 in=source(profile);assert(fseek(in,0,SEEK_END)==0);assert(fputs("SSID3=duplicate\n",in)>=0);rewind(in);out=tmpfile();assert(out);
 assert(!wr_iot_profile_stream(in,out,"IoT","password",1));assert(ftell(out)==0);fclose(in);fclose(out);
 in=source("BssidNum=2\nSSID3=\n");out=tmpfile();assert(out);assert(!wr_iot_profile_stream(in,out,"IoT","password",1));assert(ftell(out)==0);fclose(in);fclose(out);
 in=source(profile);out=tmpfile();assert(out);assert(!wr_iot_profile_stream(in,out,"IoT","short",1));assert(ftell(out)==0);fclose(in);fclose(out);
 puts("PASS IoT whole-profile preflight: required unique fields, zero output on structural rejection, OFF byte identical, primary/guest and shared radio preserved");return 0;}
