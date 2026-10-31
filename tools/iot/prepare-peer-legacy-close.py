#!/usr/bin/env python3
"""Guard legacy close replay and block reopen while its partial close is retained."""
import argparse, hashlib, json, shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')
pins={
 'common/rtmp_init_inf.c':'7f8460f5e14a244f36e62bbfd1728b59769d4ec7ebfa84bedc976f8398afc00a',
 'common/rtmp_init.c':'f5725b0a3cf4c3b3a0d56e1f96f380d0ac021138b810ccae384d1b5cdd4cd4a4',
 'include/rtmp.h':'d17d1f4b15e7e423b7c61d15f487c1495eeac947a73e543bec69e4b2f2760ec2',
 'include/wr-iot-peer-open-dispatch.inc':'6e45bf8ecb60dde46071b2c635c0c036c3ccd48599b4ef305396853e59a842e5'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(text,old,new):
 if text.count(old)!=1:p.error('changed anchor: '+old)
 return text.replace(old,new,1)
texts['include/rtmp.h']=one(texts['include/rtmp.h'],'unsigned long wr_iot_peer_close_serial;',
 'unsigned long wr_iot_peer_close_serial;\n unsigned int wr_iot_peer_legacy_close_state;')
texts['common/rtmp_init.c']=one(texts['common/rtmp_init.c'],'pAd->wr_iot_peer_close_serial=0;',
 'pAd->wr_iot_peer_close_serial=0;\n\t\tpAd->wr_iot_peer_legacy_close_state=0;')
s=texts['common/rtmp_init_inf.c'];start=s.index('INT RTMPDrvClose(');end=s.index('\n}',start)+2
body=s[start:end]
body=one(body,'UINT32 i = 0;', '''UINT32 i = 0;
 INT wr_legacy_admission=wr_iot_peer_legacy_close_begin(pAd);
 (void)net_dev;
 if(wr_legacy_admission==2)return NDIS_STATUS_SUCCESS;
 if(wr_legacy_admission!=1)return NDIS_STATUS_FAILURE;''')
body=one(body,'\t\twhile (pAd->DeQueueRunning[i] == TRUE)',
 '\t\tUINT32 wr_legacy_polls=0;\n\t\twhile (pAd->DeQueueRunning[i] == TRUE)')
body=one(body,'\t\t\tRtmpusecDelay(1000);',
 '\t\t\tif(wr_legacy_polls++>=1000U)return NDIS_STATUS_FAILURE;\n\t\t\tRtmpusecDelay(1000);')
anchor='DBGPRINT(RT_DEBUG_ERROR,("%s call RT28xxPciAsicRadioOff fail !!\\n", __FUNCTION__));'
body=one(body,anchor,anchor+'\n\t\t\t\treturn NDIS_STATUS_FAILURE;')
body=one(body,'\treturn NDIS_STATUS_SUCCESS;',
 '\tif(!wr_iot_peer_legacy_close_finish(pAd))return NDIS_STATUS_FAILURE;\n\treturn NDIS_STATUS_SUCCESS;')
s=s[:start]+body+s[end:]
s=one(s,'#include "wr-iot-peer-close-table.inc"',
 '#include "wr-iot-peer-close-table.inc"\n#include "wr-iot-peer-legacy-close.inc"')
# Checked close must not enter teardown over a retained legacy close.
start=s.index('INT wr_iot_drv_close_checked(');end=s.index('\n}',start)+2;body=s[start:end]
body=one(body,'if (!pAd || !ticket) return NDIS_STATUS_FAILURE;', '''if (!pAd || !ticket) return NDIS_STATUS_FAILURE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(pAd->wr_iot_peer_legacy_close_state==1U){
  NdisReleaseSpinLock(&pAd->MacTabLock);return NDIS_STATUS_FAILURE;
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);''')
texts['common/rtmp_init_inf.c']=s[:start]+body+s[end:]
name='include/wr-iot-peer-open-dispatch.inc'
texts[name]=one(texts[name],'if (request->serial || pAd->MacTab.Size) break;',
 'if (request->serial || pAd->MacTab.Size || pAd->wr_iot_peer_legacy_close_state==1U) break;')
texts[name]=one(texts[name],'if(accepted)request->serial=ticket.serial;',
 'if(accepted){request->serial=ticket.serial;pAd->wr_iot_peer_legacy_close_state=0;}')
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('peer-legacy-close.inc'),out/'include/wr-iot-peer-legacy-close.inc')
out.with_name(out.name+'-manifest.json').write_text(json.dumps({
 'input_sha256':pins,'target_compiled':False,'runtime_verified':False,
 'adapter_release_bound':False,'scope':'legacy close replay latch, bounded dequeue, radio-off failure and reopen admission'},indent=2)+'\n')
print('Staged legacy close replay latch and reopen exclusion; adapter free remains unbound')
