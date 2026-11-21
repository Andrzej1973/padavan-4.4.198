#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "precreated-profile.h"
static const char profile[]="Default\nBssidNum=2\nSSID1=Main\nSSID2=Guest\nSSID3=\nWPAPSK1=main-password\nWPAPSK2=guest-password\nWPAPSK3=\nAuthMode=WPA2PSK;OPEN\nEncrypType=AES;NONE\nWmmCapable=1;1\nDLSCapable=0;0\nNoForwarding=0;1\nHideSSID=0;0\nStationKeepAlive=0;0\nPreAuth=0;0\nIEEE8021X=0;0\nFixedTxMode=0;0\nHT_MCS=33;33\nChannel=6\nAutoChannelSelect=0\n";
static FILE *source(void){FILE *f=tmpfile();assert(f);assert(fwrite(profile,1,strlen(profile),f)==strlen(profile));rewind(f);return f;}
int main(void){
 char result[2][4096];
 for(int enabled=0;enabled<2;enabled++){
  FILE *in=source(),*out=tmpfile();assert(out);
  assert(wr_iot_precreated_profile(in,out,"IoT","iot-password",enabled));rewind(out);
  size_t n=fread(result[enabled],1,sizeof(result[enabled])-1,out);result[enabled][n]=0;
  assert(strstr(result[enabled],"BssidNum=3\n"));
  assert(strstr(result[enabled],"SSID1=Main\nSSID2=Guest\nSSID3=IoT\n"));
  assert(strstr(result[enabled],"AuthMode=WPA2PSK;OPEN;WPA2PSK\n"));
  assert(strstr(result[enabled],"Channel=6\nAutoChannelSelect=0\n"));
  fclose(in);fclose(out);
 }
 assert(!strcmp(result[0],result[1]));
 for(int bad=0;bad<2;bad++){
  FILE *in=source(),*out=tmpfile();assert(out);
  assert(!wr_iot_precreated_profile(in,out,"IoT",bad?"iot-password":"short",bad?2:0));
  assert(ftell(out)==0);fclose(in);fclose(out);
 }
 puts("PASS cold third-profile reservation independent of runtime enable; primary/guest/channel preserved; invalid credentials/enable rejected. No loaded BSS, default OFF, RF or runtime claim.");
 return 0;
}
