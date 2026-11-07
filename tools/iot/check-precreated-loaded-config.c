#include <assert.h>
#include <stdio.h>
#include <string.h>
struct device {unsigned id;};typedef struct device *PNET_DEV;
#define Ndis802_11AuthModeWPA2PSK 7
#define Ndis802_11AESEnable 3
typedef struct {unsigned char Ssid[32],SsidLen,PMK[32];struct {PNET_DEV if_dev;unsigned AuthMode,WepStatus,GroupKeyWepStatus,IEEE8021X;} wdev;} BSS_STRUCT;
typedef struct {int mt7603;struct {unsigned BssidNum;BSS_STRUCT MBSSID[4];} ApCfg;} RTMP_ADAPTER,*PRTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->mt7603)
#include "precreated-loaded-config.h"
int main(void){
 RTMP_ADAPTER ad={.mt7603=1,.ApCfg.BssidNum=3};struct device dev={1},other={2};
 unsigned char ssid[32],pmk[32];for(unsigned i=0;i<32;i++){ssid[i]=(unsigned char)('a'+i%20);pmk[i]=(unsigned char)(i*7);}
 BSS_STRUCT *b=&ad.ApCfg.MBSSID[2];b->wdev.if_dev=&dev;b->wdev.AuthMode=7;b->wdev.WepStatus=b->wdev.GroupKeyWepStatus=3;b->SsidLen=32;
 memcpy(b->Ssid,ssid,32);memcpy(b->PMK,pmk,32);
 assert(wr_iot_precreated_loaded_matches(&ad,&dev,ssid,32,pmk,32));
 for(unsigned i=0;i<32;i++){
  b->Ssid[i]^=1;assert(!wr_iot_precreated_loaded_matches(&ad,&dev,ssid,32,pmk,32));b->Ssid[i]^=1;
  b->PMK[i]^=1;assert(!wr_iot_precreated_loaded_matches(&ad,&dev,ssid,32,pmk,32));b->PMK[i]^=1;
 }
 assert(!wr_iot_precreated_loaded_matches(&ad,&other,ssid,32,pmk,32));
 for(unsigned length=0;length<35;length++)if(length!=32)assert(!wr_iot_precreated_loaded_matches(&ad,&dev,ssid,length,pmk,32));
 for(unsigned length=0;length<35;length++)if(length!=32)assert(!wr_iot_precreated_loaded_matches(&ad,&dev,ssid,32,pmk,length));
 unsigned *fields[]={&b->wdev.AuthMode,&b->wdev.WepStatus,&b->wdev.GroupKeyWepStatus};
 for(unsigned i=0;i<3;i++){unsigned saved=*fields[i];*fields[i]=0;assert(!wr_iot_precreated_loaded_matches(&ad,&dev,ssid,32,pmk,32));*fields[i]=saved;}
 b->wdev.IEEE8021X=1;assert(!wr_iot_precreated_loaded_matches(&ad,&dev,ssid,32,pmk,32));b->wdev.IEEE8021X=0;
 ad.ApCfg.BssidNum=5;assert(!wr_iot_precreated_loaded_matches(&ad,&dev,ssid,32,pmk,32));
 assert(!wr_iot_precreated_loaded_matches(NULL,&dev,ssid,32,pmk,32));
 puts("PASS loaded third-BSS SSID/security/PMK matcher:64 byte mutations, lengths, device and mode mismatches rejected. Injected structures; no PBKDF or live-driver identity claim.");return 0;
}
