#!/usr/bin/env python3
"""Verify first-beacon hook composition and final-driver placement, not RF safety."""
import argparse,runpy,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'first-beacon-composition.py'))['compose']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',nargs='?',type=Path);a=p.parse_args()
original={
 'os/linux/rt_main_dev.c':'#include \"driver-api-owner-binding.inc\"\n#include \"driver-api-open-entry.inc\"',
 'include/rtmp.h':'#include "driver-api-owner.h"\n struct wr_iot_mbss_closed_probe wr_iot_closed_probe;',
 'common/rtmp_init.c':'NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));',
 'include/wr-iot-beacon-producer-kernel.h':'      wr_iot_beacon_gate_begin(gate, gate->generation, ticket);',
 'common/cmm_mac_pci.c':'#include "rt_config.h"\n\t\tbcn_buf->bcn_state = BCN_TX_WRITE_TO_DMA;\n\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);'
}
with tempfile.TemporaryDirectory(prefix='wr-iot-first-beacon-compose-') as td:
 root=Path(td);snapshot=dict(original);result=compose(original,root,here)
 assert original==snapshot
 assert len(result)==8
 assert 'wr_iot_first_beacon_capture_locked' in result['include/wr-iot-beacon-producer-kernel.h']
 assert 'wr_iot_first_beacon_published_locked' in result['common/cmm_mac_pci.c']
 for name in original:
  drift=dict(original);drift[name]='changed input'
  try:compose(drift,root,here)
  except ValueError:pass
  else:raise AssertionError('changed anchor accepted:'+name)
 try:compose(result,root,here)
 except ValueError:pass
 else:raise AssertionError('replayed composition accepted')
if a.driver:
 producer=(a.driver/'include/wr-iot-beacon-producer-kernel.h').read_text()
 assert producer.count('wr_iot_first_beacon_capture_locked(ad,bss,ticket->generation)')==1
 assert producer.index('wr_iot_beacon_gate_begin(')<producer.index('wr_iot_first_beacon_capture_locked(')
 source=(a.driver/'common/cmm_mac_pci.c').read_text()
 hook='wr_iot_first_beacon_published_locked(pAd,apidx);'
 assert source.count(hook)==1
 point=source.index(hook);start=source.rfind('INT32 RT28xx_UpdateBeaconToAsic(',0,point)
 assert start>=0
 block=source[start:source.index('\n}',point)+2]
 assert block.index('HAL_KickOutMgmtTx')<block.index('bcn_buf->bcn_state = BCN_TX_WRITE_TO_DMA;')<block.index(hook)
 assert block.index('goto unsubmitted;',block.index('HAL_KickOutMgmtTx'))<block.index(hook)
 main=(a.driver/'os/linux/rt_main_dev.c').read_text()
 assert main.count('#include \"precreated-first-beacon-wait.inc\"')==1
 assert main.index('#include \"driver-api-owner-binding.inc\"')<main.index('#include \"precreated-first-beacon-wait.inc\"')<main.index('#include \"driver-api-open-entry.inc\"')
 for name in ['precreated-first-beacon.h','precreated-first-beacon-kernel.h','precreated-first-beacon-wait.inc']:
  assert (a.driver/'include'/name).read_bytes()==(here/name).read_bytes()
print('PASS first-beacon composition: exact anchors, no partial mutation/replay; final-driver hook/wait placement checked when supplied. Target/runtime and RF retirement unverified.')
