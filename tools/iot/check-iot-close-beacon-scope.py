#!/usr/bin/env python3
"""Execute actual candidate MBSS_Close global beacon-update selection."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
s=(a.driver/'ap/ap_mbss.c').read_text();sig='INT MBSS_Close(PNET_DEV pDev)'
assert s.count(sig)==1
start=s.index(sig);body=s[start:s.index('\n}',start)+2]
pre=r'''
#include <assert.h>
#include <stdio.h>
typedef int INT;typedef unsigned UINT32;
#define HIF_MT 1
#define REASON_DISASSOC_INACTIVE 4
struct adapter {int mt;struct {int hif_type;} chipCap;struct {int BssidNum,BandSteering;struct {int wdev;} MBSSID[4];} ApCfg;};
typedef struct adapter *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;int index;} *PNET_DEV;
static int stop,kick,drain,make,update,allow;
#ifdef BAND_STEERING
#define FALSE 0
typedef int *PBND_STRG_CLI_TABLE;
static int steering;
static PBND_STRG_CLI_TABLE Get_BndStrgTable(PRTMP_ADAPTER ad,int index){assert(ad&&index>=0);return &steering;}
static void BndStrg_SetInfFlags(PRTMP_ADAPTER ad,int *wdev,PBND_STRG_CLI_TABLE table,int up){assert(ad&&wdev&&table&&!up);steering++;}
#endif
#define IS_MT7603(ad) ((ad)->mt)
#define RTMP_OS_NETDEV_GET_PRIV(d) ((d)->ad)
#define RT28xx_MBSS_IdxGet(ad,d) ((void)(ad),(d)->index)
#define RTMP_OS_NETDEV_STOP_QUEUE(d) ((void)(d),stop++)
static void MbssKickOutStas(PRTMP_ADAPTER ad,int b,int reason){assert(ad&&b>=0&&reason==4);kick++;}
static int wr_iot_bcn_revoke_and_drain(PRTMP_ADAPTER ad,int b){assert(ad&&b>=0);drain++;return allow;}
static void APMakeAllBssBeacon(PRTMP_ADAPTER ad){assert(ad&&drain);make++;}
static void APUpdateAllBeaconFrame(PRTMP_ADAPTER ad){assert(ad&&make);update++;}
'''
post=r'''
int main(void){
 for(int f=0;f<6;f++){
  struct adapter ad={.mt=1,.chipCap.hif_type=HIF_MT,.ApCfg={.BssidNum=3,.BandSteering=1}};
  struct device dev={&ad,2};
  stop=kick=drain=make=update=0;allow=1;
#ifdef BAND_STEERING
  steering=0;
#endif
  if(f==1)dev.index=1;
  if(f==2)ad.mt=0;
  if(f==3)ad.chipCap.hif_type=0;
  if(f==4)ad.ApCfg.BssidNum=4;
  if(f==5)allow=0;
  int result=MBSS_Close(&dev);
  assert(stop==1&&kick==1&&drain==1);
  if(f==5)assert(result==-1&&!make&&!update);
  else assert(!result&&make==1&&update==(f!=0));
#ifdef BAND_STEERING
  assert(steering==(f==2));
#endif
 }
 puts("PASS actual IoT close: no global update, MAC remake retained; Guest/other chip/count paths preserved, failed drain stops before remake. No RF proof.");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-close-scope-') as d:
 src=Path(d)/'t.c';exe=Path(d)/'t';src.write_text(pre+body+post)
 for extra in ([],['-DBAND_STEERING']):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)]+extra,check=True)
  subprocess.run([str(exe)],check=True)
