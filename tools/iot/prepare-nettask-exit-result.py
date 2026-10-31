#!/usr/bin/env python3
"""Make net-task exit refusal observable before caller resource teardown.

Prerequisite only: scheduling fence/drain is not installed by this transform.
"""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rtmp.h':'b5cb1efed32a609a61bfa26969b171d2fc4c8cbe4237a95abaac37a220b98709',
 'os/linux/rt_rbus_pci_drv.c':'d4f7c75e59fd866afb016e425b731b505c3afe8780ddb30978938528e45ecd12',
 'os/linux/rt_sdio.c':'c560fa3cd1f7154e720a6f99f09a06f69e6ebdeb138c7a85e5cda1e54bae15c1',
 'common/rtmp_init_inf.c':'81790a10d9f583a3c010e935385c557ccddd14cd5763134e946184ddc856f9b6'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(name,old,new):
 if texts[name].count(old)!=1:p.error('changed anchor: '+name+': '+old)
 texts[name]=texts[name].replace(old,new,1)
one('include/rtmp.h','VOID RtmpNetTaskExit(RTMP_ADAPTER *pAd);','INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);')
for name,sig in [('os/linux/rt_rbus_pci_drv.c','void RtmpNetTaskExit('),('os/linux/rt_sdio.c','VOID RtmpNetTaskExit(')]:
 s=texts[name];start=s.index(sig);end=s.index('\n}',start)+2;body=s[start:end]
 if 'return;' in body:p.error('unreviewed early return')
 body=body.replace(sig,'INT RtmpNetTaskExit(',1)
 body=body[:-2]+'\n return NDIS_STATUS_SUCCESS;\n}'
 texts[name]=s[:start]+body+s[end:]
name='common/rtmp_init_inf.c'
one(name,'err2:\n\tRtmpNetTaskExit(pAd);',
 'err2:\n\tif (RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS) return FALSE;')
start=texts[name].index('static INT wr_iot_legacy_close_body(')
end=texts[name].index('\n}',start)+2;body=texts[name][start:end]
assert body.count('RtmpNetTaskExit(pAd);')==1
body=body.replace('RtmpNetTaskExit(pAd);','if (RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS) return NDIS_STATUS_FAILURE;',1)
texts[name]=texts[name][:start]+body+texts[name][end:]
start=texts[name].index('static INT wr_iot_checked_close_body(')
end=texts[name].index('\n}',start)+2;body=texts[name][start:end]
assert body.count('RtmpNetTaskExit(pAd);')==1
body=body.replace('RtmpNetTaskExit(pAd);','''if (RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS) {
  /* Early teardown is partial: retain ownership, never replay stage zero. */
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
  pAd->wr_iot_transition.shutdown_stage=3U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }''',1)
texts[name]=texts[name][:start]+body+texts[name][end:]
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
print('Staged net-task exit status and three caller guards; producer fence/drain remains unbound')
