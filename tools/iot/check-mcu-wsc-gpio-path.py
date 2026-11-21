#!/usr/bin/env python3
"""Check WSC source call chain and execute its GPIO macro behind MLME admission."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
mlme=(a.candidate/'common/mlme.c').read_text()
wsc=(a.candidate/'common/wsc.c').read_text()
header=(a.candidate/'include/wsc.h').read_bytes().decode('latin-1')
assert mlme.count('WSC_HDR_BTN_MR_HANDLE(pAd);')==1
assert header.count('WSC_HDR_BTN_CheckHandler(__pAd);')==1
assert wsc.count('WSC_HDR_BTN_MR_PRESS_FLG_GET(pAd, flg_pressed);')==1
start=mlme.index('static NTSTATUS wr_iot_mlme_periodic_raw(')
wrapper=mlme[start:mlme.index('\nstatic NTSTATUS',start+1)]
start=header.index('#define WSC_HDR_BTN_MR_PRESS_FLG_GET(')
macro=header[start:header.index('/* WSC HDR PSH BTN FUNC */',start)]
prefix=r'''
#include <assert.h>
#include <stdio.h>
#define IN
typedef unsigned UINT32;typedef int NTSTATUS;typedef int PCmdQElmt;
typedef struct {int mt;struct {int hif_type;} chipCap;} RTMP_ADAPTER;
typedef RTMP_ADAPTER *PRTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->mt)
#define NDIS_STATUS_SUCCESS 0
#define HIF_MT 1
#define WSC_HDR_BTN_GPIO_0 0
#define WSC_HDR_BTN_GPIO_3 3
#define fRTMP_ADAPTER_WSC_PBC_PIN0 1
#define GPIO_CTRL_CFG 7
static int allowed,held,reads,pin0;
#define RTMP_TEST_MORE_FLAG(ad,flag) ((void)(ad),(void)(flag),pin0)
static UINT32 GPIOGetValue(RTMP_ADAPTER *ad,unsigned pin){assert(ad&&held&&pin==(pin0?0u:3u));reads++;return 1;}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),(void)(reg),*(out)=0)
static int wr_iot_control_enter(RTMP_ADAPTER *ad){assert(ad);if(!allowed)return 0;held++;return 1;}
static void wr_iot_control_leave(RTMP_ADAPTER *ad){assert(ad&&held==1);held--;}
'''
tail=r'''
static NTSTATUS wr_iot_mlme_periodic_raw(PRTMP_ADAPTER pAd,PCmdQElmt cmd){
 int pressed=9;assert(cmd==7);WSC_HDR_BTN_MR_PRESS_FLG_GET(pAd,pressed);assert(!pressed);return 5;
}
int main(void){RTMP_ADAPTER ad={1,{HIF_MT}};
 for(pin0=0;pin0<2;pin0++){
  reads=0;allowed=0;assert(!MlmePeriodicExec(&ad,7)&&!reads&&!held);
  allowed=1;assert(MlmePeriodicExec(&ad,7)==5&&reads==1&&!held);
 }
 puts("PASS WSC GPIO source chain and actual GPIO macro behind generated MLME admission: both pins, denied zero reads, admitted balanced lease; helper/GPIO injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-wsc-gpio-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+macro+wrapper+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
