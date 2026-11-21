#!/usr/bin/env python3
"""Serialize public raw reset execution against both close paths and main open."""
import argparse,hashlib,shutil,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/wr-iot-reset-admission.inc':'fa3f17c292beaf54012906294c2f2b44c1551a7a06480bc46fedd0d4c701e6a5',
 'include/peer-close-executor.h':'f1aa6edf3cdb3bde8aa4f63de43f96ade0e2a727193f12f0d8ba377fb82aa084'}
actual={}
for name,digest in pins.items():
 actual[name]=hashlib.sha256((src/name).read_bytes()).hexdigest()
 accepted={digest}
 if name=='include/peer-close-executor.h':
  # Fresh stage53 copies the shared helper including the reviewed reset lane;
  # the original incremental53 preceded that extension. Accept these exact two.
  accepted.add('58feca7c44653eac0559a31793e8c60f757279edf24546b546c0df61a2423d33')
 if actual[name] not in accepted:p.error('unreviewed predecessor: '+name)
s=(src/'include/wr-iot-reset-admission.inc').read_text()
def one(old,new):
 global s
 if s.count(old)!=1:p.error('changed anchor: '+old)
 s=s.replace(old,new,1)
one('if(!rtnl_trylock())return;', '''if(!rtnl_trylock())return;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 admitted=wr_iot_peer_close_executor_enter(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_RESET,0);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!admitted){rtnl_unlock();return;}
 admitted=0;''')
# There are now two refusal branches; replace only the one after radio admission.
anchor=' RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);\n if(!admitted){rtnl_unlock();return;}'
one(anchor,''' RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 if(!admitted){
  NdisAcquireSpinLock(&pAd->MacTabLock);
  (void)wr_iot_peer_close_executor_leave(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_RESET,0,0,0);
  NdisReleaseSpinLock(&pAd->MacTabLock);
  rtnl_unlock();return;
 }''')
one(' RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);\n rtnl_unlock();',
 ''' RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 /* Retired means software execution returned, not physical reset success. */
 (void)wr_iot_peer_close_executor_leave(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_RESET,0,retired,1);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 rtnl_unlock();''')
shutil.copytree(src,out)
(out/'include/wr-iot-reset-admission.inc').write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('peer-close-executor.h'),out/'include/peer-close-executor.h')
out.with_name(out.name+'-manifest.json').write_text(json.dumps({'input_sha256':actual,
 'scope':'public raw reset execution versus close executor and main-open admission',
 'peer_writers_serialized':False,'adapter_release_bound':False,
 'target_compiled':False,'runtime_verified':False},indent=2)+'\n')
print('Staged raw reset execution exclusion; peer writers and adapter release still unproved')
