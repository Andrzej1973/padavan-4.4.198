#!/usr/bin/env python3
"""Extract controller exit, free ABI and exact caller guards; actual free mocked."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new fixture output required')
root=a.candidate;header=(root/'include/rt_os_net.h').read_text()
field='BOOLEAN (*RTMPFreeAdapter)(VOID *pAd);';prototype='BOOLEAN RTMPFreeAdapter(VOID *pAd);'
assert field in header and prototype in header
ops_source=(root/'common/rtmp_init_inf.c').read_text();assignment='pDrvOps->RTMPFreeAdapter = RTMPFreeAdapter;'
assert assignment in ops_source
dispatch=re.search(r'^#define RTMPFreeAdapter .+$',header,re.M).group()
init=(root/'common/rtmp_init.c').read_text();start=init.index('BOOLEAN RtmpRaDevCtrlExit(')
controller=init[start:init.index('\n}',start)+2]
assert 'if (!RTMPFreeAdapter(pAd)) return FALSE;' in controller
free=(root/'os/linux/rt_profile.c').read_text();start=free.index('BOOLEAN RTMPFreeAdapter(')
free=free[start:free.index('\n}',start)+2]
assert 'return;' not in free and free.count('return FALSE;')==2 and free.count('return TRUE;')==1
assert free.index('RtmpOsVfree(pAd)')<free.index('return TRUE;')
pci=(root/'os/linux/pci_main_dev.c').read_text();sdio=(root/'os/linux/sdio_main_dev.c').read_text()
guards={'pci_remove':'if (!RtmpRaDevCtrlExit(pAd)) return;',
 'sdio_remove':'if (!RtmpRaDevCtrlExit(pAd)) return;',
 'pci_probe':'if (!RTMPFreeAdapter(pAd)) return -EBUSY;',
 'sdio_probe':'if (!RTMPFreeAdapter(pAd)) return;'}
for name,guard in guards.items():assert guard in (pci if name.startswith('pci') else sdio)
prefix=r'''
#include <assert.h>
typedef int BOOLEAN;typedef int INT;typedef void VOID;
#define IN
#define TRUE 1
#define FALSE 0
#define EBUSY 16
#define MAX_LEN_OF_BSS_TABLE 2
typedef struct {int AutoRateLock,e2p_read_lock;struct {void *pIe;} ProbeRespIE[2];} RTMP_ADAPTER;
static int free_ok,free_calls,destructors,unmaps,irqs,cookies;
#define RTMP_SEM_EVENT_DESTORY(p) ((void)(p),destructors++)
#define os_free_mem(ad,p) ((void)(ad),(void)(p),destructors++)
BOOLEAN RTMPFreeAdapter(VOID *pAd){assert(pAd);free_calls++;return free_ok;}
'''
prefix+='typedef struct {'+field+'} RTMP_DRV_ABL_OPS;\n'
prefix+='static void init_ops(RTMP_DRV_ABL_OPS *pDrvOps){'+assignment+'}\n'
prefix+='#ifdef TEST_ABL\nstatic void *pRtmpDrvOps;\n'+dispatch+'\n#endif\n'
seams='\nstatic void pci_remove(RTMP_ADAPTER *pAd){'+guards['pci_remove']+'unmaps++;}\n'
seams+='static void sdio_remove(RTMP_ADAPTER *pAd){'+guards['sdio_remove']+'irqs++;}\n'
seams+='static int pci_probe(RTMP_ADAPTER *pAd){'+guards['pci_probe']+'unmaps++;return 0;}\n'
seams+='static void sdio_probe(RTMP_ADAPTER *pAd){'+guards['sdio_probe']+'cookies++;}\n'
post=r'''
int main(void){RTMP_ADAPTER a={0};RTMP_DRV_ABL_OPS ops;init_ops(&ops);(void)ops;
#ifdef TEST_ABL
pRtmpDrvOps=&ops;
#endif
free_ok=0;a.ProbeRespIE[0].pIe=&a;
pci_remove(&a);sdio_remove(&a);assert(pci_probe(&a)==-EBUSY);sdio_probe(&a);
assert(free_calls==4&&!unmaps&&!irqs&&!cookies);
/* Existing controller destructors still precede free: early claim remains open. */
assert(destructors==6);
free_ok=1;pci_remove(&a);sdio_remove(&a);assert(!pci_probe(&a));sdio_probe(&a);
assert(free_calls==8&&unmaps==2&&irqs==1&&cookies==1);
return 0;}
'''
if 'if (!wr_iot_adapter_release_begin(pAd)) return FALSE;' in controller:
 assert controller.index('wr_iot_adapter_release_begin(pAd)')<controller.index('RTMP_SEM_EVENT_DESTORY')
 prefix+='static int gate_ok=1;\nstatic BOOLEAN wr_iot_adapter_release_begin(RTMP_ADAPTER *ad){assert(ad);return gate_ok;}\n'
 post=post.replace('free_ok=0;a.ProbeRespIE[0].pIe=&a;', '''
gate_ok=0;pci_remove(&a);sdio_remove(&a);
assert(!free_calls&&!destructors&&!unmaps&&!irqs&&!cookies);
gate_ok=1;free_ok=0;a.ProbeRespIE[0].pIe=&a;''')
a.output.write_text(prefix+controller+seams+post,encoding='utf-8')
print('Extracted controller/ABI/four caller seams; free and outer resource operations mocked')
