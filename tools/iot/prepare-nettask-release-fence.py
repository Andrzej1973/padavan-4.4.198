#!/usr/bin/env python3
"""Require joined network tasklets and permanently fence their reopen at release."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rtmp.h':'b5356085e00c2fd3f780896cd775c332bf4b1be1cea205c43273cb2e777155bf',
 'common/rtmp_init.c':'07c7f4205811b799cb3ed4b94c0a3daffbbeebd161a4b19d8b17768f63c7754e',
 'include/wr-iot-nettask-schedule.inc':'e74095bab2b0729423ebda39d07ba9a5c9475bd0e6181878ed3491664760b69d',
 'include/wr-iot-peer-adapter-release.inc':'ceda5cd648ea518fdfe69b64ec6d4d6a97814e454ce72be9b2bba8da47d7e607'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(name,old,new):
 if texts[name].count(old)!=1:p.error('changed anchor '+name+': '+old)
 texts[name]=texts[name].replace(old,new,1)
one('include/rtmp.h','unsigned int wr_iot_nettask_joined;',
 'unsigned int wr_iot_nettask_joined;\n unsigned int wr_iot_nettask_release_claimed,wr_iot_nettask_initializing;')
one('common/rtmp_init.c','pAd->wr_iot_nettask_joined=1; /* Fresh adapter has never submitted a tasklet. */',
 'pAd->wr_iot_nettask_joined=1; /* Fresh adapter has never submitted a tasklet. */\n pAd->wr_iot_nettask_release_claimed=0;pAd->wr_iot_nettask_initializing=0;')
name='include/wr-iot-nettask-schedule.inc'
one(name,'accepted=wr_iot_tasklet_schedule_open(',
 'accepted=!pAd->wr_iot_nettask_release_claimed && pAd->wr_iot_nettask_initializing && wr_iot_tasklet_schedule_open(')
one(name,'if(accepted)pAd->wr_iot_nettask_joined=0;',
 'if(accepted){pAd->wr_iot_nettask_joined=0;pAd->wr_iot_nettask_initializing=0;}')
one(name,'ready=pAd->wr_iot_nettask_joined &&',
 'ready=!pAd->wr_iot_nettask_release_claimed && !pAd->wr_iot_nettask_initializing && pAd->wr_iot_nettask_joined &&')
# Reserve initialization in the final helper, not the similarly shaped drain query.
old='ready=!pAd->wr_iot_nettask_release_claimed && !pAd->wr_iot_nettask_initializing && pAd->wr_iot_nettask_joined && wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner);'
one(name,old,old+'\n if(ready)pAd->wr_iot_nettask_initializing=1;')
old='RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);\n wr_iot_tasklet_schedule_block('
one(name,old,'''RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 if(pAd->wr_iot_nettask_initializing){
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);return NDIS_STATUS_FAILURE;
 }
 wr_iot_tasklet_schedule_block(''')
name='include/wr-iot-peer-adapter-release.inc'
one(name,' /* RELEASE_CLAIMED is terminal;', ''' /* The terminal radio receipt cannot authorize freeing a live scheduling
  * owner. Keep this fence even if a later peer-state check refuses release. */
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=!pAd->wr_iot_nettask_initializing && pAd->wr_iot_nettask_joined &&
  wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner);
 if(ready)pAd->wr_iot_nettask_release_claimed=1;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 if(!ready)return FALSE;
 /* RELEASE_CLAIMED is terminal;''')
texts[name]='#define WR_IOT_NETTASK_RELEASE_FENCE 1\n'+texts[name]
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
print('Bound network scheduling joined/drained release condition and permanent reopen fence')
