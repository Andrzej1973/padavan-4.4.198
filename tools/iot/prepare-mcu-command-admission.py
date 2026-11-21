#!/usr/bin/env python3
"""Fence PCI command dispatch while preserving cleanup and deferred reset drain."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False or
 'mcu_control_admission' not in m or 'mcu_command_admission' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated control-admission candidate')
name='common/rtmp_init.c';text=(src/name).read_text()
start=text.index('VOID CMDHandler(RTMP_ADAPTER *pAd)\n{');end=text.index('\n#endif /* RTMP_MAC_PCI */',start)
body=text[start:end]
def one(old,new):
 global body
 if body.count(old)!=1:p.error('Changed command admission anchor')
 body=body.replace(old,new)
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
one('\tPCmdQElmt cmdqelmt;', '\tPCmdQElmt cmdqelmt;\n'+guard+'\n int wr_iot_command_admitted=0;\n#endif')
one('\t\tpData = cmdqelmt->buffer;', '\t\tpData = cmdqelmt->buffer;\n'+guard+'\n wr_iot_command_admitted=0;\n#endif')
anchor='if(!(RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST) || RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_HALT_IN_PROGRESS)))'
one(anchor,anchor[:-1]+'\n'+guard+'\n && (!IS_MT7603(pAd) || (wr_iot_command_admitted=wr_iot_control_enter(pAd)))\n#endif\n )')
reset='''#if defined(MT7603) && defined(DMA_RESET_SUPPORT)
						wr_iot_radio_reset_drain(pAd);
#endif'''
one(reset,'')
one('\t\twr_iot_queue_cleanup(cmdqelmt);',guard+'''
 if(wr_iot_command_admitted)wr_iot_control_leave(pAd);
#endif
 /* Reset owns its separate transition. Never call it under control admission;
  * periodic dispatch may be denied precisely because reset is pending. */
#if defined(MT7603) && defined(DMA_RESET_SUPPORT)
 if(cmdqelmt->command==CMDTHREAD_MLME_PERIOIDC_EXEC &&
    !RTMP_TEST_FLAG(pAd,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_HALT_IN_PROGRESS))
  wr_iot_radio_reset_drain(pAd);
#endif
		wr_iot_queue_cleanup(cmdqelmt);''')
(src/name).write_text(text[:start]+body+text[end:])
digest=hashlib.sha256((src/name).read_bytes()).hexdigest()
m['merged_driver_sha256'][name]=digest;m['candidate_driver_sha256'][name]=digest
m['mcu_command_admission']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':{name:digest},'all_remap_users_covered':False,
 'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
