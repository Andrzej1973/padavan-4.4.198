#!/usr/bin/env python3
"""Stage a narrow failed-first-open beacon-intent rollback outside production."""
import argparse
import hashlib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path, help='pinned mt76x3 source directory')
p.add_argument('output', type=Path, help='new separate candidate directory')
a = p.parse_args()
root, out = a.source.resolve(), a.output.resolve()
if out.exists() or out == root or root in out.parents or out in root.parents:
    raise SystemExit('New output outside source tree required')
blobs = {
    'ap/ap_mbss.c': '92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f',
    'ap/ap_mbss_inf.c': '7c736a04eeeddace0bbb0c5c96198d0738f400a2',
    'ap/ap_cfg.c': '17853ec17d577021ce876c5ec6d8909e27a7453b',
    'include/rtmp_cmd.h': 'adfd19a69fac4fa3b08ca113f7a88b9016e25a67',
    'include/ap_mbss.h': '667b4728f1ade6f7030b2c23ef24cc413617ff3b',
}
original = {}
for name, expected in blobs.items():
    data = (root/name).read_bytes()
    actual = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if actual != expected:
        raise SystemExit('Unreviewed source: '+name)
    original[name] = data

def replace_once(text, old, new, name):
    if text.count(old) != 1:
        raise SystemExit('Changed anchor: '+name)
    return text.replace(old, new, 1)

updated = {name: data.decode('utf-8') for name, data in original.items()}
helper = '''INT MBSS_AbortOpen(PNET_DEV pDev)
{
    PRTMP_ADAPTER pAd;
    INT BssId;
    UINT32 max_bss;

    if (!pDev)
        return -1;
    pAd = RTMP_OS_NETDEV_GET_PRIV(pDev);
    if (!pAd)
        return -1;
    max_bss = sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]);
    if (pAd->ApCfg.BssidNum > max_bss)
        return -1;
    BssId = RT28xx_MBSS_IdxGet(pAd, pDev);
    if (BssId <= 0 || (UINT32)BssId >= max_bss ||
        (UINT32)BssId >= pAd->ApCfg.BssidNum)
        return -1;

    /* First virtual-interface startup failed; CR_ENABLE was not reached.
     * Clear only this BSS's request, without kicking stations or MMIO. */
    RTMP_SEM_LOCK(&pAd->BcnRingLock);
    pAd->ApCfg.MBSSID[BssId].bcn_buf.bBcnSntReq = FALSE;
    RTMP_SEM_UNLOCK(&pAd->BcnRingLock);
    return 0;
}

'''
name = 'ap/ap_mbss.c'
close_comment = '''/*
========================================================================
Routine Description:
    Close a virtual network interface.'''
updated[name] = replace_once(updated[name], close_comment,
                             helper+close_comment, name)
name = 'include/ap_mbss.h'
updated[name] = replace_once(updated[name], 'INT MBSS_Close(PNET_DEV pDev);',
                             'INT MBSS_Close(PNET_DEV pDev);\nINT MBSS_AbortOpen(PNET_DEV pDev);', name)
name = 'include/rtmp_cmd.h'
updated[name] = replace_once(updated[name],
    '\tCMD_RTPRIV_IOCTL_80211_COM_LATEST_ONE,',
    '\t/* Append to preserve all existing command values. */\n'
    '\tCMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN,\n\tCMD_RTPRIV_IOCTL_80211_COM_LATEST_ONE,', name)
name = 'ap/ap_cfg.c'
updated[name] = replace_once(updated[name],
    '\t\tcase CMD_RTPRIV_IOCTL_MBSS_CLOSE:\n\t\t\tMBSS_Close(pData);',
    '\t\tcase CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN:\n'
    '\t\t\tif (MBSS_AbortOpen(pData) != 0)\n'
    '\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\tbreak;\n\n'
    '\t\tcase CMD_RTPRIV_IOCTL_MBSS_CLOSE:\n\t\t\tMBSS_Close(pData);', name)
name = 'ap/ap_mbss_inf.c'
updated[name] = replace_once(updated[name],
    '\tRTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_MBSS_OPEN, 0, pDev, 0);',
    '\tif (RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_MBSS_OPEN, 0, pDev, 0)\n'
    '\t    != NDIS_STATUS_SUCCESS) {\n'
    '\t\tRT_MOD_DEC_USE_COUNT();\n\t\treturn -1;\n\t}', name)
updated[name] = replace_once(updated[name],
    '\tif (VIRTUAL_IF_UP(pAd) != 0)\n\t\treturn -1;',
    '\tif (VIRTUAL_IF_UP(pAd) != 0) {\n'
    '\t\tif (RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN, 0, pDev, 0)\n'
    '\t\t    != NDIS_STATUS_SUCCESS)\n'
    '\t\t\tDBGPRINT(RT_DEBUG_ERROR, ("MBSS open abort failed\\n"));\n'
    '\t\tRT_MOD_DEC_USE_COUNT();\n\t\treturn -1;\n\t}', name)

for name, data in original.items():
    if (root/name).read_bytes() != data:
        raise SystemExit('Source changed: '+name)
out.mkdir()
for name, text in updated.items():
    target = out/name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
def function(text, signature):
    if text.count(signature) != 1:
        raise SystemExit('Changed function: '+signature)
    start = text.index(signature)
    return text[start:text.index('\n}', start)+2]
abort = function(updated['ap/ap_mbss.c'], 'INT MBSS_AbortOpen(PNET_DEV pDev)')
wrapper = function(updated['ap/ap_mbss_inf.c'], 'INT MBSS_VirtualIF_Open(PNET_DEV pDev)')
fixture = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT;
typedef unsigned int UINT32;
typedef void VOID;
typedef struct adapter {struct {UINT32 BssidNum;struct {struct {int bBcnSntReq;} bcn_buf;} MBSSID[3];} ApCfg;
 int BcnRingLock;} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
#define RT_DEBUG_TRACE 0
#define RT_DEBUG_ERROR 1
#define DBGPRINT(level,args) ((void)0)
#define RTMP_OS_NETDEV_GET_DEVNAME(dev) "ra2"
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define RTMP_SEM_LOCK(lock) do {assert(!*(lock));*(lock)=1;locks++;} while(0)
#define RTMP_SEM_UNLOCK(lock) do {assert(*(lock));*(lock)=0;unlocks++;} while(0)
#define RT_MOD_INC_USE_COUNT() (++refs)
#define RT_MOD_DEC_USE_COUNT() (--refs)
#define CMD_RTPRIV_IOCTL_MBSS_OPEN 1
#define CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN 2
#define CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE 3
#define RTMP_OS_NETDEV_START_QUEUE(dev) ((void)(dev),queue_starts++)
#define RT_MOD_HNAT_REG(dev) ((void)(dev),hnat++)
static int index_value=2,idx_calls,locks,unlocks,refs,open_result,up_result;
static int up_calls,abort_calls,cr_calls,queue_starts,hnat;
static struct adapter ad;static struct device dev={&ad};
static INT RT28xx_MBSS_IdxGet(PRTMP_ADAPTER a,PNET_DEV d){
 assert(a&&d&&a->ApCfg.BssidNum<=3);idx_calls++;return index_value;
}
'''+abort+r'''
static INT RTMP_AP_IoctlHandle(VOID *a,VOID *unused,INT cmd,INT z,PNET_DEV d,INT n){
 assert(a==&ad&&!unused&&!z&&d==&dev&&!n);
 if(cmd==CMD_RTPRIV_IOCTL_MBSS_OPEN){
  if(open_result)return NDIS_STATUS_FAILURE;
  ad.ApCfg.MBSSID[index_value].bcn_buf.bBcnSntReq=1;return NDIS_STATUS_SUCCESS;
 }
 if(cmd==CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN){abort_calls++;return MBSS_AbortOpen(d);}
 if(cmd==CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE){cr_calls++;return NDIS_STATUS_SUCCESS;}
 assert(0);return NDIS_STATUS_FAILURE;
}
static INT VIRTUAL_IF_UP(VOID *a){assert(a==&ad);up_calls++;return up_result;}
'''+wrapper+r'''
int main(void){
 memset(&ad,0,sizeof(ad));ad.ApCfg.BssidNum=3;
 open_result=-1;
 assert(MBSS_VirtualIF_Open(&dev)==-1);
 assert(!refs&&!up_calls&&!abort_calls&&!locks&&!queue_starts);
 open_result=0;up_result=-1;
 assert(MBSS_VirtualIF_Open(&dev)==-1);
 assert(!refs&&up_calls==1&&abort_calls==1&&locks==1&&unlocks==1);
 assert(!ad.BcnRingLock&&!ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq);
 assert(!ad.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq&&!queue_starts);
 up_result=0;
 assert(!MBSS_VirtualIF_Open(&dev));
 assert(refs==1&&up_calls==2&&abort_calls==1&&queue_starts==1);
 assert(ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq);
#ifdef MT_MAC
 assert(cr_calls==1);
#else
 assert(!cr_calls);
#endif
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 assert(hnat==1);
#else
 assert(!hnat);
#endif
 int before=locks;index_value=0;
 assert(MBSS_AbortOpen(&dev)==-1&&locks==before);
 index_value=2;ad.ApCfg.BssidNum=4;
 assert(MBSS_AbortOpen(&dev)==-1&&locks==before);
 assert(idx_calls==2);
 puts("PASS pinned MBSS abort-open candidate: failed ioctl, failed first up, successful path, invalid abort");
 return 0;
}
'''
(out/'check.c').write_text(fixture, encoding='utf-8')
print('Staged pinned failed-open rollback candidate; production source unchanged')
