#!/usr/bin/env python3
"""Extract real auxiliary ndo_stop wrappers and inject family/DOWN failures."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
functions=[]
for name,sig,command in [('ap/ap_apcli_inf.c','INT ApCli_VirtualIF_Close(','CMD_RTPRIV_IOCTL_APC_CLOSE'),
 ('os/linux/rt_profile.c','INT Monitor_VirtualIF_Close(','CMD_RTPRIV_IOCTL_SNIFF_CLOSE')]:
 s=(a.candidate/name).read_text();start=s.index(sig);body=s[start:s.index('\n}',start)+2]
 assert body.index(command)<body.index('VIRTUAL_IF_DOWN(')<body.index('RT_MOD_DEC_USE_COUNT(')
 assert '!= NDIS_STATUS_SUCCESS) return -EBUSY;' in body
 functions.append(body)
prefix=r'''
#include <assert.h>
typedef void VOID;typedef int INT;typedef void *PNET_DEV;
#define NULL ((void *)0)
#define NDIS_STATUS_SUCCESS 0
#define EBUSY 16
#define RT_DEBUG_TRACE 0
#define ASSERT(x) assert(x)
#define DBGPRINT(l,a) do{(void)(l);}while(0)
#define RTMP_OS_NETDEV_GET_PRIV(dev) (dev)
static int family_result,down_result,family_calls,down_calls,pins,hnat_calls;
#define CMD_RTPRIV_IOCTL_APC_CLOSE 1
#define CMD_RTPRIV_IOCTL_SNIFF_CLOSE 2
static int ioctl_close(void *ad,int cmd,void *dev){assert(ad&&dev&&(cmd==1||cmd==2));family_calls++;return family_result;}
#define RTMP_AP_IoctlHandle(ad,wrq,cmd,sub,data,flags) ioctl_close(ad,cmd,data)
#define RTMP_COM_IoctlHandle(ad,wrq,cmd,sub,data,flags) ioctl_close(ad,cmd,data)
static int down(void *ad){assert(ad&&!family_result);down_calls++;return down_result;}
#define VIRTUAL_IF_DOWN(ad) down(ad)
#define RT_MOD_HNAT_DEREG(dev) do{assert(dev&&!family_result);hnat_calls++;}while(0)
#define RT_MOD_DEC_USE_COUNT() do{assert(!family_result&&!down_result&&pins==1);pins--;}while(0)
'''
post=r'''
int main(void){int dev;
 for(int monitor=0;monitor<2;monitor++){
  family_calls=down_calls=hnat_calls=0;pins=1;family_result=1;down_result=0;
  assert((monitor?Monitor_VirtualIF_Close(&dev):ApCli_VirtualIF_Close(&dev))==-EBUSY);
  assert(family_calls==1&&!down_calls&&!hnat_calls&&pins==1);
  /* Independent invocation, not proof that replay of partial effects is safe. */
  family_calls=0;family_result=0;down_result=1;
  assert((monitor?Monitor_VirtualIF_Close(&dev):ApCli_VirtualIF_Close(&dev))==-EBUSY);
  assert(family_calls==1&&down_calls==1&&pins==1);
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
  assert(hnat_calls==1);
#else
  assert(!hnat_calls);
#endif
  family_calls=down_calls=hnat_calls=0;down_result=0;
  assert((monitor?Monitor_VirtualIF_Close(&dev):ApCli_VirtualIF_Close(&dev))==0);
  assert(family_calls==1&&down_calls==1&&pins==0);
 }
 return 0;}
'''
a.output.write_text(prefix+'\n'.join(functions)+post,encoding='utf-8')
print('Extracted real APCLI/Monitor ndo_stop wrappers; family/virtual DOWN and HNAT mocked')
