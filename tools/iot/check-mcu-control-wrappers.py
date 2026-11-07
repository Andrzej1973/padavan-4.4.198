#!/usr/bin/env python3
"""Execute generated wrappers; raw SDK body and actor admission are injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
wrappers=[]
for name,private in [('common/mlme.c','wr_iot_mlme_periodic_raw'),('os/linux/rt_main_dev.c','wr_iot_linux_ioctl_raw')]:
 text=(a.candidate/name).read_text();start=text.index('static ',text.index(private)-30)
 # The forward declaration immediately precedes the public wrapper.
 end=text.index('\nstatic ',start+1)
 wrappers.append(text[start:end])
prefix=r'''
#include <assert.h>
#include <stdio.h>
#define IN
typedef int INT;typedef int NTSTATUS;typedef int PCmdQElmt;
typedef struct {int mt;} RTMP_ADAPTER;typedef RTMP_ADAPTER *PRTMP_ADAPTER;
struct netdev {RTMP_ADAPTER *ad;};typedef struct netdev *PNET_DEV;
struct ifreq {int unused;};
#define GET_PAD_FROM_NET_DEV(out,dev) ((out)=(dev)->ad)
#define IS_MT7603(ad) ((ad)->mt)
#define NDIS_STATUS_SUCCESS 0
#define ENETDOWN 100
#define EBUSY 16
static int entered,left,active,allowed=1,calls,result;
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
static int wr_iot_control_enter(RTMP_ADAPTER *ad){assert(ad);entered++;if(!allowed)return 0;active++;return 1;}
static void wr_iot_control_leave(RTMP_ADAPTER *ad){assert(ad&&active);active--;left++;}
#endif
'''
tail=r'''
static NTSTATUS wr_iot_mlme_periodic_raw(PRTMP_ADAPTER ad,PCmdQElmt cmd){assert(ad&&cmd==7);calls++;return result;}
static INT wr_iot_linux_ioctl_raw(PNET_DEV dev,struct ifreq *rq,INT cmd){assert(dev&&rq&&cmd==9);calls++;return result;}
int main(void){RTMP_ADAPTER ad={1};struct netdev dev={&ad};struct ifreq rq={0};
 for(result=-2;result<=2;result++){
  assert(MlmePeriodicExec(&ad,7)==result);assert(rt28xx_ioctl(&dev,&rq,9)==result);assert(!active);
 }
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 assert(entered==10&&left==10&&calls==10);allowed=0;
 assert(!MlmePeriodicExec(&ad,7));assert(rt28xx_ioctl(&dev,&rq,9)==-EBUSY);assert(calls==10&&!active);
 ad.mt=0;assert(rt28xx_ioctl(&dev,&rq,9)==result);assert(MlmePeriodicExec(&ad,7)==result);assert(calls==12&&entered==12);
 dev.ad=0;assert(rt28xx_ioctl(&dev,&rq,9)==-ENETDOWN&&calls==12);
#else
 assert(calls==10&&!entered&&!left);(void)allowed;
#endif
 puts("PASS generated control wrappers: body results, blocked-body exclusion, balanced release and feature guards; admission/raw bodies injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-control-wrappers-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+'\n'.join(wrappers)+tail)
 for flags in ([],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',td+'/check'],check=True)
  subprocess.run([td+'/check'],check=True)
