#!/usr/bin/env python3
"""Extract parent exit; verify child failure stops later detach. Kernel mocked."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'os/linux/rt_main_dev.c').read_text()
start=s.index('BOOLEAN RtmpPhyNetDevExit(');end=s.index('\n}',start)+2;body=s[start:end]
pci=(a.candidate/'os/linux/pci_main_dev.c').read_text()
guard='if (!RtmpPhyNetDevExit(pAd, net_dev))\n\t\t\treturn;'
assert pci.count(guard)==1
cfg=(a.candidate/'common/cmm_cfg.c').read_text()
assert 'if (WDS_Remove(pAd) != NDIS_STATUS_SUCCESS)\n\t\t\t\treturn NDIS_STATUS_FAILURE;' in cfg
prefix=r'''
#include <assert.h>
#include <stddef.h>
#define CONFIG_AP_SUPPORT 1
#define APCLI_SUPPORT 1
#define WDS_SUPPORT 1
#define MBSS_SUPPORT 1
#define CONFIG_SNIFFER_SUPPORT 1
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
typedef int BOOLEAN;typedef void VOID;typedef unsigned long ULONG;
typedef struct {int wr_iot_transition_lock,wr_iot_transition;} ADAPTER,*PRTMP_ADAPTER;
typedef struct {char *name;} DEV,*PNET_DEV;
static int lock,failed,calls,detach,retire;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!lock);lock=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(lock);lock=0;}while(0)
#define wr_iot_radio_retire(s) do{(void)(s);assert(lock);retire++;}while(0)
static int child(void *a,int n){(void)a;assert(!lock);calls++;return failed==n?-1:0;}
#define RT28xx_ApCli_Remove(a) child(a,1)
#define RT28xx_WDS_Remove(a) child(a,2)
#define RT28xx_MBSS_Remove(a) child(a,3)
#define RT28xx_Monitor_Remove(a) child(a,4)
#define printk(...) ((void)0)
#define RtmpOSNetDevProtect(n) ((void)(n))
#define RtmpOSNetDevDetach(d) do{(void)(d);assert(!failed&&!lock);detach++;}while(0)
'''
suffix=r'''
int main(void){ADAPTER a={0};DEV d={0};
for(int i=1;i<=4;i++){failed=i;calls=detach=retire=0;
 assert(!RtmpPhyNetDevExit(&a,&d)&&calls==i&&!detach&&!lock&&retire==1);}
failed=0;calls=detach=retire=0;
assert(RtmpPhyNetDevExit(&a,&d)&&calls==4&&detach==1&&!lock&&retire==1);
return 0;}
'''
a.output.write_text(prefix+body+suffix,encoding='utf-8')
print('Extracted parent child-failure checks; PCI guard/dispatcher source assertions pass')
