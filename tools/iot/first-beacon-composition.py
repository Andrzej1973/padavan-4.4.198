"""Compose host beacon receipt hooks and bounded wait into isolated API tree."""
from pathlib import Path
import re

def compose(changes,source,local):
 result=dict(changes);source=Path(source);local=Path(local)
 def one(name,old,new):
  value=result.get(name)
  if value is None:value=(source/name).read_text()
  if value.count(old)!=1:raise ValueError('First beacon composition anchor changed: '+name+' '+repr(old[:60]))
  result[name]=value.replace(old,new,1)
 one('include/rtmp.h','#include "driver-api-owner.h"',
     '#include "driver-api-owner.h"\n#include "precreated-first-beacon.h"')
 one('include/rtmp.h',' struct wr_iot_mbss_closed_probe wr_iot_closed_probe;',
     ' struct wr_iot_mbss_closed_probe wr_iot_closed_probe;\n struct wr_iot_first_beacon wr_iot_first_beacon;\n struct wr_iot_first_beacon_identity wr_iot_first_beacon_capture;')
 init='NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));'
 one('common/rtmp_init.c',init,init+'\n        NdisZeroMemory(&pAd->wr_iot_first_beacon,sizeof(pAd->wr_iot_first_beacon));\n        NdisZeroMemory(&pAd->wr_iot_first_beacon_capture,sizeof(pAd->wr_iot_first_beacon_capture));')
 name='include/wr-iot-beacon-producer-kernel.h'
 one(name,'      wr_iot_beacon_gate_begin(gate, gate->generation, ticket);',
     '      wr_iot_beacon_gate_begin(gate, gate->generation, ticket);\n if (ok && protect) wr_iot_first_beacon_capture_locked(ad,bss,ticket->generation);')
 result[name]='#include "precreated-first-beacon-kernel.h"\n'+result[name]
 name='common/cmm_mac_pci.c'
 value=result.get(name)
 if value is None:value=(source/name).read_text()
 includes=re.findall(r'^#include[ \t]+"rt_config.h"[ \t]*$',value,re.M)
 if len(includes)!=1:raise ValueError('First beacon config include missing/ambiguous: '+name)
 one(name,includes[0],includes[0]+'\n#include "precreated-first-beacon-kernel.h"')
 one('common/cmm_mac_pci.c','\t\tbcn_buf->bcn_state = BCN_TX_WRITE_TO_DMA;\n\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);',
     '\t\tbcn_buf->bcn_state = BCN_TX_WRITE_TO_DMA;\n\t\twr_iot_first_beacon_published_locked(pAd,apidx);\n\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);')
 one('os/linux/rt_main_dev.c','#include \"driver-api-owner-binding.inc\"\n#include \"driver-api-open-entry.inc\"',
     '#include \"driver-api-owner-binding.inc\"\n#include \"precreated-first-beacon-wait.inc\"\n#include \"driver-api-open-entry.inc\"')
 for asset in ['precreated-first-beacon.h','precreated-first-beacon-kernel.h','precreated-first-beacon-wait.inc']:
  if 'include/'+asset in result or (source/'include'/asset).exists():
   raise ValueError('Unexpected prior first-beacon asset: '+asset)
  result['include/'+asset]=(local/asset).read_text()
 return result
