#!/usr/bin/env python3
"""Extract legacy close and bridges; kernel/OS_ABL layouts remain mocked."""
import argparse
import re
from pathlib import Path
import close_fixture_support as support
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
def extract(text,signature):
 start=text.index(signature);return text[start:text.index('\n}',start)+2]
source=(a.candidate/'common/rtmp_init_inf.c').read_text()
legacy=extract(source,'static INT wr_iot_legacy_close_body(' if support.enabled(a.candidate) else 'INT RTMPDrvClose(')
shutdown=extract((a.candidate/'ap/ap.c').read_text(),'BOOLEAN APShutdown(')
bridge=extract((a.candidate/'os/linux/rt_main_dev.c').read_text(),'int rt28xx_close(VOID *dev)')
header=(a.candidate/'include/rt_os_net.h').read_text()
field='INT (*RTMPDrvClose)(VOID *pAd, VOID *net_dev);'
prototype='INT RTMPDrvClose(VOID *pAd, VOID *net_dev);'
assignment='pDrvOps->RTMPDrvClose = RTMPDrvClose;'
assert field in header and prototype in header and assignment in source
dispatch=re.search(r'^#define RTMPDrvClose .+$',header,re.M).group()
wrapper=extract(header,'__inline INT VIRTUAL_IF_DOWN(').replace('__inline INT','static INT',1)
cfg=(a.candidate/'common/cmm_cfg.c').read_text()
start=cfg.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:')
end=cfg.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_GET:',start)
case=cfg[start:end]
owner_only_down='WR_IOT_OWNER_ONLY_DOWN' in case
if not owner_only_down:
 assert 'if (pInfConf->rt28xx_close(pAd->net_dev) != 0) return NDIS_STATUS_FAILURE;' in case
pci=(a.candidate/'os/linux/pci_main_dev.c').read_text()
guard='if (rt28xx_close((PNET_DEV)net_dev) != 0) return -EBUSY;'
assert pci.index(guard)<pci.index('RT_MOD_DEC_USE_COUNT();',pci.index(guard))<pci.index('pci_disable_device(pci_dev);')
template=Path(__file__).with_name('checked-close-host-fixture.c.in').read_text()
prefix=template.split('@@CHECKED_CLOSE_FUNCTION@@')[0]
prefix=prefix.replace('#define APShutdown(ad) ((void)(ad),mock_ap_shutdown())','')
prefix=prefix.replace('static int mock_ap_shutdown(void){assert(!held);ap_calls++;return ap_result;}','')
prefix=re.sub(r'^static int wr_iot_mgmt_exit_checked[^\n]+\n','',prefix,flags=re.M)
prefix=prefix.replace('int wr_iot_transition_lock;','int wr_iot_transition_lock,MacTabLock;')
prefix=prefix.replace('int infType;unsigned int flags;}','int infType;unsigned int flags;int VirtualIfCnt;void *net_dev;}')
extra=r'''
#define EIO 5
#define EBUSY 16
static int locks_freed,diagnostics,module_refs=1,power_down;
#define MlmeRadioOff(ad) ((void)(ad),ap_calls++)
#define APStop(ad) ((void)(ad),ap_result)
#define NdisFreeSpinLock(l) ((void)(l),locks_freed++)
#define RtmpMgmtTaskExit(ad) ((void)(ad),joins++)
static int mock_radio_off(void){return radio_result;}
#undef RT28xxPciAsicRadioOff
#define RT28xxPciAsicRadioOff(ad,why,num) ((void)(ad),(void)(why),(void)(num),mock_radio_off())
struct net_device {RTMP_ADAPTER *priv;};
typedef struct net_device *PNET_DEV;
#define GET_PAD_FROM_NET_DEV(ad,dev) do{(ad)=(dev)->priv;}while(0)
#ifdef WIFI_DIAG
#define DiagProcExit(ad) ((void)(ad),diagnostics++)
#endif
'''
ops='\ntypedef struct { '+field+' } RTMP_DRV_ABL_OPS;\n'
ops+='static void init_ops(RTMP_DRV_ABL_OPS *pDrvOps){'+assignment+'}\n'
ops+='#ifdef TEST_ABL\nstatic void *pRtmpDrvOps;\n'+dispatch+'\n#endif\n'
extra2=r'''
typedef struct {int (*rt28xx_open)(void *);int (*rt28xx_close)(void *);void *if_dev;unsigned long generation,serial,epoch,operation;} RT_CMD_INF_UP_DOWN;
static int rt28xx_open(void *dev){(void)dev;return 0;}
#define CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN 1
#define CMD_RTPRIV_IOCTL_VIRTUAL_INF_GET 2
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define VIRTUAL_IF_DEC(ad) ((ad)->VirtualIfCnt--)
'''
handler='static int RTMP_COM_IoctlHandle(void *raw,void *wrq,int cmd,int sub,void *pData,int flags){RTMP_ADAPTER *pAd=raw;(void)pAd;(void)pData;(void)wrq;(void)sub;(void)flags;switch(cmd){'+case+'}return NDIS_STATUS_SUCCESS;}\n'
pm='static int pm_close(struct net_device *net_dev){'+guard+'module_refs--;power_down++;return 0;}\n'
endpoints=''
owned_endpoints=0
for rel,sig in [('os/linux/rt_profile.c','INT Monitor_VirtualIF_Close(PNET_DEV dev_p)'),('ap/ap_apcli_inf.c','INT ApCli_VirtualIF_Close(PNET_DEV dev_p)')]:
 text=(a.candidate/rel).read_text()
 f=extract(text,sig+'\n')
 if 'wr_iot_aux_family_close_owned(' in f:
  assert (a.candidate/'include/wr-iot-aux-family-close-owned.inc').exists()
  owned_endpoints+=1
  continue # Actual new endpoints are composed by prepare-aux-family-owned-check.py.
 assert f.index('if (VIRTUAL_IF_DOWN(pAd) != 0) return -EBUSY;')<f.index('RT_MOD_DEC_USE_COUNT();')
 endpoints+=f+'\n'
endpoint_shim=r'''
#define ASSERT assert
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->priv)
#define CMD_RTPRIV_IOCTL_SNIFF_CLOSE 3
#define CMD_RTPRIV_IOCTL_APC_CLOSE 4
#define RTMP_AP_IoctlHandle RTMP_COM_IoctlHandle
#define RT_MOD_DEC_USE_COUNT() (--module_refs)
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
static int dereg;
#define RT_MOD_HNAT_DEREG(dev) ((void)(dev),dereg++)
#endif
'''
post=r'''
int main(void){RTMP_ADAPTER a={0};struct net_device dev={&a};RTMP_DRV_ABL_OPS ops;
init_ops(&ops);(void)ops;(void)join_result;
#ifdef TEST_ABL
pRtmpDrvOps=&ops;
#endif
ap_result=0;assert(rt28xx_close(&dev)==-EIO);
assert(ap_calls==1&&!locks_freed&&!pre_calls&&!post_calls&&!ring_frees&&!diagnostics&&!joins);
assert(pm_close(&dev)==-EBUSY&&module_refs==1&&!power_down&&!locks_freed);
a.VirtualIfCnt=1;a.net_dev=&dev;assert(VIRTUAL_IF_DOWN(&a)==-1&&!a.VirtualIfCnt&&!locks_freed);
int oldap=ap_calls;assert(VIRTUAL_IF_DOWN(&a)==-1&&ap_calls==oldap);
memset(&a,0,sizeof a);ap_result=1;
assert(!rt28xx_close(&dev)&&locks_freed==1&&pre_calls==1&&post_calls==1&&ring_frees==1&&joins==1);
#ifdef WIFI_DIAG
assert(diagnostics==1);
#else
assert(!diagnostics);
#endif
memset(&a,0,sizeof a);assert(!pm_close(&dev)&&!module_refs&&power_down==1);
memset(&a,0,sizeof a);a.VirtualIfCnt=1;a.net_dev=&dev;assert(!VIRTUAL_IF_DOWN(&a)&&!a.VirtualIfCnt);
for(int which=0;which<2;which++){
 memset(&a,0,sizeof a);a.VirtualIfCnt=1;a.net_dev=&dev;module_refs=1;ap_result=0;
 assert((which?ApCli_VirtualIF_Close(&dev):Monitor_VirtualIF_Close(&dev))==-EBUSY&&module_refs==1&&!a.VirtualIfCnt);
 memset(&a,0,sizeof a);a.VirtualIfCnt=1;a.net_dev=&dev;ap_result=1;
 assert(!(which?ApCli_VirtualIF_Close(&dev):Monitor_VirtualIF_Close(&dev))&&!module_refs&&!a.VirtualIfCnt);
}
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
assert(dereg==4);
#endif
dev.priv=NULL;assert(!rt28xx_close(&dev));
return 0;}
'''
if 'NdisFreeSpinLock(&pAd->MacTabLock);' not in shutdown:
 post=post.replace('locks_freed==1&&pre_calls==1','locks_freed==0&&pre_calls==1')
if owner_only_down:
 post=post.replace('VIRTUAL_IF_DOWN(&a)==-1&&!a.VirtualIfCnt&&!locks_freed',
                   'VIRTUAL_IF_DOWN(&a)==-1&&a.VirtualIfCnt==1&&!locks_freed')
 post=post.replace('assert(!VIRTUAL_IF_DOWN(&a)&&!a.VirtualIfCnt);',
                   'assert(VIRTUAL_IF_DOWN(&a)==-1&&a.VirtualIfCnt==1);')
if owned_endpoints:
 assert owned_endpoints==2 and not endpoints, 'mixed endpoint implementations require separate fixture support'
 begin=post.index('for(int which=0;which<2;which++){')
 end=post.index('dev.priv=NULL;',begin)
 post=post[:begin]+post[end:]
 endpoint_shim=''
if support.enabled(a.candidate):
 prefix=support.prefix(prefix);legacy=support.definitions(source)
 post=support.fresh(post).replace('init_ops(&ops);','init_ops(&ops);wr_test_peer_fresh(&a);',1)
a.output.write_text(prefix+extra+prototype+'\n'+shutdown+'\n'+legacy+ops+bridge+extra2+handler+wrapper+pm+endpoint_shim+endpoints+post,encoding='utf-8')
print('Extracted whole legacy close, native/ABL bridge and virtual-down; PCI guard seam only')
