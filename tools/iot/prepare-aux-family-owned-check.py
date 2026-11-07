#!/usr/bin/env python3
"""Compose actual auxiliary ndo_stop/helper and DOWN body with host primitives."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();here=Path(__file__).resolve().parent
if a.output.exists():p.error('new output required')
s=(here/'check-aux-family-close-owned.c').read_text()
start=s.index('static int wr_iot_virtual_down_checked(');end=s.index('\n}',start)+2
actual=(a.candidate/'include/wr-iot-virtual-down.inc').read_text()
actual=actual.replace('INT wr_iot_virtual_down_checked(', 'INT wr_iot_virtual_down_core(',1)
extra='''
#define VIRTUAL_IF_DEC(ad) ((ad)->count--)
static int wr_iot_rt28xx_close_checked(void *dev,const struct wr_iot_radio_ticket *t){
 (void)dev;(void)t;assert(0);return 1; /* Non-last test must not enter physical close. */
}
'''+actual+'''
static int wr_iot_virtual_down_checked(RTMP_ADAPTER *ad,const struct wr_iot_radio_ticket *t){
 assert(!held);down_calls++;if(down_result)return 1;
 return wr_iot_virtual_down_core(ad,t);
}
'''
s=s[:start]+extra+s[end:]
s=s.replace('#include "aux-family-close-owned.inc"','#include "wr-iot-aux-family-close-owned.inc"')
wrappers='''
static RTMP_ADAPTER *wrapper_ad;
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((void)(dev),wrapper_ad)
#define RTMP_AP_IoctlHandle(ad,wrq,cmd,sub,dev,flags) family_close(ad,dev)
#define RTMP_COM_IoctlHandle(ad,wrq,cmd,sub,dev,flags) family_close(ad,dev)
static INT wr_iot_aux_family_retry_submit(RTMP_ADAPTER *ad,PNET_DEV dev,
 enum wr_iot_ref_family family){
 (void)ad;(void)dev;(void)family;return -EBUSY;
}
'''
for name,callback,sig in [('ap/ap_apcli_inf.c','wr_iot_apcli_close_ioctl','INT ApCli_VirtualIF_Close('),
 ('os/linux/rt_profile.c','wr_iot_monitor_close_ioctl','INT Monitor_VirtualIF_Close(')]:
 text=(a.candidate/name).read_text()
 for anchor in ('static INT '+callback+'(',sig):
  begin=text.index(anchor);wrappers+=text[begin:text.index('\n}',begin)+2]+'\n'
s=s.replace('static void ready(',wrappers+'static void ready(',1)
s=s.replace('memset(ad,0,sizeof *ad);','memset(ad,0,sizeof *ad);wrapper_ad=ad;',1)
s=s.replace('wr_iot_aux_family_close_owned(&ad,&dev[1],f,family_close)',
 '(k?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))')
a.output.write_text(s,encoding='utf-8')
print('Composed actual two wrappers, owned helper and DOWN body; kernel/driver primitives mocked')
