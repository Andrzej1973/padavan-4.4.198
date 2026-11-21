#!/usr/bin/env python3
"""Join tasklets after IRQ release in both physical close bodies."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'common/rtmp_init_inf.c':'81790a10d9f583a3c010e935385c557ccddd14cd5763134e946184ddc856f9b6',
 'include/wr-iot-peer-adapter-release.inc':'ceda5cd648ea518fdfe69b64ec6d4d6a97814e454ce72be9b2bba8da47d7e607'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
s=texts['common/rtmp_init_inf.c']
join='''
 /* IRQ source has been detached/synchronized before tasklet memory release.
  * Exclusive close executor serializes this receipt across retries. */
 {
  ULONG wr_tasklet_flags;int wr_tasklet_joined;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,wr_tasklet_flags);
  wr_tasklet_joined=(pAd->wr_iot_transition.joined_workers&4U)!=0;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,wr_tasklet_flags);
  if(!wr_tasklet_joined){
   RtmpNetTaskExit(pAd);
   RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,wr_tasklet_flags);
   pAd->wr_iot_transition.joined_workers|=4U;
   RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,wr_tasklet_flags);
  }
 }
'''
for sig in ['static INT wr_iot_legacy_close_body(', 'static INT wr_iot_checked_close_body(']:
 start=s.index(sig);end=s.index('\n}',start)+2;body=s[start:end]
 early='\tRtmpNetTaskExit(pAd);'
 if body.count(early)!=1:p.error('changed early tasklet exit')
 body=body.replace(early,'\t/* Tasklets stay alive until IRQ teardown below. */',1)
 anchor='#ifdef SINGLE_SKU_V2'
 if body.count(anchor)!=1:p.error('changed post-IRQ location')
 body=body.replace(anchor,join+'\n'+anchor,1)
 assert body.index('RTMP_OS_IRQ_RELEASE(pAd, net_dev);')<body.index('RtmpNetTaskExit(pAd);')<body.index('RTMPFreeTxRxRingMemory(pAd);')
 s=s[:start]+body+s[end:]
texts['common/rtmp_init_inf.c']=s
name='include/wr-iot-peer-adapter-release.inc'
if texts[name].count('required_workers=1U;')!=1:p.error('changed release join mask')
texts[name]=texts[name].replace('required_workers=1U;','required_workers=1U|4U;',1)
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
print('Staged tasklet join after IRQ release; adds explicit final tasklet receipt')
