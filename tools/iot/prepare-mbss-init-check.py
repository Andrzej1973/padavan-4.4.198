#!/usr/bin/env python3
"""Isolated failed-registration candidate; never edits production input.

Kernel lifetime and beacon/radio recovery remain separate gaps.
The fixture injects driver operations; it is not a kernel lifetime test.
"""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('fixture', type=Path)
a = p.parse_args()
if len({x.resolve() for x in (a.input, a.candidate, a.fixture)}) != 3:
    raise SystemExit('Input and outputs must be distinct')
if a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Refusing to overwrite outputs')
source = a.input.read_text(encoding='utf-8')
anchor = 'VOID MBSS_Init(RTMP_ADAPTER *pAd, RTMP_OS_NETDEV_OP_HOOK *pNetDevOps)'
if source.count(anchor) != 1:
    raise SystemExit('MBSS init signature changed')
start = source.index(anchor)
end = source.index('\n}', start) + 2
original = source[start:end]
old = '\t\t\tRtmpOSNetDevFree(pDevNew);\n\t\t\tbreak;'
if original.count(old) != 1:
    raise SystemExit('MBSS index-registration failure branch changed')
patched = original.replace(old, '''            /* Registration failed before this wdev acquired a registry slot.
             * Do not retain a pointer to the freed netdevice. Preserve already
             * created lower BSS indices, like the allocation-failure branch. */
            wdev->if_dev = NULL;
            pAd->ApCfg.BssidNum = IdBss;
            RtmpOSNetDevFree(pDevNew);
            break;''')
attach = '\t\t/*status =*/ RtmpOSNetDevAttach(pAd->OpMode, pDevNew, &netDevHook);'
if patched.count(attach) != 1:
    raise SystemExit('MBSS Linux-registration anchor changed')
patched = patched.replace(attach, '''        if (RtmpOSNetDevAttach(pAd->OpMode, pDevNew, &netDevHook) != NDIS_STATUS_SUCCESS) {
            /* Linux registration failed: no unregister_netdevice/detach.
             * Remove the successfully acquired driver registry slot first. */
            rtmp_wdev_idx_unreg(pAd, wdev);
            wdev->if_dev = NULL;
            pAd->ApCfg.BssidNum = IdBss;
            RtmpOSNetDevFree(pDevNew);
            break;
        }''')
free_helper = '''/* Only for netdevices whose Linux registration did not succeed.
 * Normal Detach owns the ops allocation for registered devices. */
static void wr_iot_mbss_free_unregistered(PNET_DEV dev)
{
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
    vfree(dev->netdev_ops);
    dev->netdev_ops = NULL;
#endif
    RtmpOSNetDevFree(dev);
}
'''
if patched.count('RtmpOSNetDevFree(pDevNew);') != 2:
    raise SystemExit('Unexpected MBSS cleanup sites')
patched = patched.replace('RtmpOSNetDevFree(pDevNew);', 'wr_iot_mbss_free_unregistered(pDevNew);')
prefix = r'''#include <assert.h>
#include <string.h>
#include <stdio.h>
typedef int INT32;
typedef unsigned int UINT32;
typedef void VOID;
struct ops {int number,freed;};
struct device {int number,freed,attached,registered;const struct ops *netdev_ops;};
typedef struct device *PNET_DEV;
struct wifi_dev {
 int wdev_type,func_idx,tx_pkt_allowed,tx_pkt_handle,wdev_hard_tx;
 int rx_pkt_allowed,rx_ps_handle,rx_pkt_foward;
 void *func_dev,*sys_handle;
 PNET_DEV if_dev;
 unsigned char bssid[6];
};
typedef struct {struct wifi_dev wdev; int bcn_buf;} BSS_STRUCT;
typedef struct {int FlgMbssInit,OpMode;struct {int BssidNum;BSS_STRUCT MBSSID[4];} ApCfg;} RTMP_ADAPTER;
typedef struct {int priv_flags,needProtcted;struct wifi_dev *wdev;unsigned char devAddr[6];} RTMP_OS_NETDEV_OP_HOOK;
static struct device devices[4];
static struct ops operations[4];
static int fail_index,fail_attach,allocated,freed,registered,unregistered,beacons;
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define LINUX_VERSION_CODE KERNEL_VERSION(4,4,198)
#define NDIS_STATUS_SUCCESS 0
#define FALSE 0
#define TRUE 1
#define FIRST_MBSSID 1
#define MAX_MBSSID_NUM(ad) 4
#define WDEV_TYPE_AP 1
#define INT_MBSSID 2
#define MAC_ADDR_LEN 6
#define RT_DEBUG_TRACE 0
#define RT_DEBUG_ERROR 1
#define DBGPRINT(level,args) ((void)0)
#define ASSERT(value) assert(value)
#define ApAllowToSendPacket 1
#define APSendPacket 2
#define APHardTransmit 3
#define ap_rx_pkt_allow 4
#define ap_rx_ps_handle 5
#define ap_rx_foward_handle 6
#define RTMP_OS_NETDEV_SET_PRIV(dev,ad) ((void)0)
#define RTMP_OS_NETDEV_SET_WDEV(dev,wdev) ((void)0)
#define NdisCopyMemory memcpy
#define NdisMoveMemory memcpy
struct mt_dev_priv {int unused;};
static char *get_dev_name_prefix(RTMP_ADAPTER *ad,int kind){(void)ad;assert(kind==2);return "ra";}
static PNET_DEV RtmpOSNetDevCreate(UINT32 row,UINT32 *io,int kind,int index,size_t n,char *name){
 assert(!row&&!*io&&kind==2&&n==sizeof(struct mt_dev_priv)&&!strcmp(name,"ra"));
 devices[index].number=index;operations[index].number=index;
 devices[index].netdev_ops=&operations[index];allocated++;return &devices[index];
}
static int rtmp_wdev_idx_reg(RTMP_ADAPTER *ad,struct wifi_dev *w){
 (void)ad;if(w->func_idx==fail_index)return -1;
 w->if_dev->registered=1;registered++;return w->func_idx;
}
static int rtmp_wdev_idx_unreg(RTMP_ADAPTER *ad,struct wifi_dev *w){
 (void)ad;assert(w->if_dev->registered&&!w->if_dev->attached);
 w->if_dev->registered=0;unregistered++;return 0;
}
static void vfree(const void *p){
 const struct ops *o=p;int index=o->number;
 assert(p==&operations[index]&&!o->freed&&!devices[index].attached&&!devices[index].registered);
 operations[index].freed=1;
}
static void RtmpOSNetDevFree(PNET_DEV d){
 assert(!d->freed&&!d->attached&&!d->registered&&!d->netdev_ops&&operations[d->number].freed);
 d->freed=1;freed++;
}
static int RtmpOSNetDevAttach(int mode,PNET_DEV d,RTMP_OS_NETDEV_OP_HOOK *hook){
 assert(!mode&&hook->wdev->if_dev==d&&!d->freed&&d->registered);
 if(d->number==fail_attach)return 1;
 d->attached=1;return 0;
}
static void wdev_bcn_buf_init(RTMP_ADAPTER *ad,int *buf){(void)ad;*buf=1;beacons++;}
'''
tail = r'''
static void reset(void){memset(devices,0,sizeof(devices));memset(operations,0,sizeof(operations));allocated=freed=registered=unregistered=beacons=0;fail_index=fail_attach=0;}
int main(void){
 RTMP_ADAPTER ad;RTMP_OS_NETDEV_OP_HOOK hook={0};
 int failure;
 for(failure=1;failure<=2;failure++){
  reset();memset(&ad,0,sizeof(ad));ad.ApCfg.BssidNum=3;fail_index=failure;
  MBSS_Init(&ad,&hook);
  assert(ad.FlgMbssInit&&ad.ApCfg.BssidNum==failure);
  assert(ad.ApCfg.MBSSID[failure].wdev.if_dev==NULL&&devices[failure].freed);
  assert(allocated==failure&&freed==1&&registered==failure-1&&beacons==failure-1);
  if(failure==2)assert(ad.ApCfg.MBSSID[1].wdev.if_dev==&devices[1]&&devices[1].attached);
  MBSS_Init(&ad,&hook);assert(allocated==failure); /* one-time flag stays explicit */
 }
 for(failure=1;failure<=2;failure++){
  reset();memset(&ad,0,sizeof(ad));ad.ApCfg.BssidNum=3;fail_attach=failure;
  MBSS_Init(&ad,&hook);
  assert(ad.FlgMbssInit&&ad.ApCfg.BssidNum==failure);
  assert(ad.ApCfg.MBSSID[failure].wdev.if_dev==NULL&&devices[failure].freed);
  assert(allocated==failure&&freed==1&&registered==failure&&unregistered==1&&beacons==failure-1);
  if(failure==2)assert(devices[1].registered&&devices[1].attached&&!devices[1].freed);
  MBSS_Init(&ad,&hook);assert(allocated==failure);
 }
 reset();memset(&ad,0,sizeof(ad));ad.ApCfg.BssidNum=3;fail_index=0;
 MBSS_Init(&ad,&hook);
 assert(ad.ApCfg.BssidNum==3&&ad.FlgMbssInit&&allocated==2&&!freed&&registered==2&&beacons==2);
 assert(ad.ApCfg.MBSSID[1].wdev.if_dev==&devices[1]&&ad.ApCfg.MBSSID[2].wdev.if_dev==&devices[2]);
 assert(!operations[1].freed&&!operations[2].freed);
 puts("PASS candidate actual MBSS_Init: registration failure frees private ops/device once; successful lower BSS retained; operations injected");
 return 0;
}
'''
a.candidate.write_text(source[:start] + '#include <linux/vmalloc.h>\n' + free_helper + patched + source[end:], encoding='utf-8')
a.fixture.write_text(prefix + free_helper + patched + tail, encoding='utf-8')
print('Prepared isolated init candidate; production and radio recovery unchanged')
