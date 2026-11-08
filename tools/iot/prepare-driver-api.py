#!/usr/bin/env python3
"""Bind authorized OPEN API in a hash-checked isolated candidate, never production."""
import argparse, hashlib, json, runpy
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();local=Path(__file__).parent
transition_api=runpy.run_path(str(local/'check-radio-transition-api.py'),run_name='__main__')
mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or m.get('target_compiled') is not False or 'precreated_bss_admission' not in m or 'linux_open_api' in m or actual!=m['merged_driver_sha256']:
 p.error('Expected unchanged isolated precreated-BSS candidate')
for f in src.rglob('*'):
 if f.is_file() and f.suffix in ('.c','.h') and any(number in f.read_text(errors='replace').lower() for number in ('0x89ff','0x89fe','0x89fd')):
  p.error('Private-device ioctl number requires collision review: '+str(f))
changes={}
def one(name,old,new):
 s=changes.get(name,(src/name).read_text())
 if s.count(old)!=1:p.error('OPEN API anchor changed: '+name+' '+repr(old[:65]))
 changes[name]=s.replace(old,new,1)
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
close_helpers=runpy.run_path(str(local/'close-owner-composition.py'))
close_composition=close_helpers['compose']
changes['include/wr-iot-mbss-recovery-work.inc']=close_helpers['compose_recovery_idle']((src/'include/wr-iot-mbss-recovery-work.inc').read_text())
changes['include/wr-iot-mbss-recovery-join.inc']=close_helpers['compose_recovery_join']((src/'include/wr-iot-mbss-recovery-join.inc').read_text())
changes['include/wr-iot-mbss-close-checked.inc']=close_composition((src/'include/wr-iot-mbss-close-checked.inc').read_text())
one('include/rtmp.h','#include "interface-registry.h"','#include "interface-registry.h"\n'+guard+'\n#include "driver-api-owner.h"\n#include "driver-api-close-owner.h"\n#include "mbss-closed-probe.h"\n#endif')
one('include/rtmp.h','NDIS_SPIN_LOCK wr_iot_transition_lock;','NDIS_SPIN_LOCK wr_iot_transition_lock;\n'+guard+'\n struct wr_iot_driver_owner wr_iot_driver_owner;\n struct wr_iot_driver_close_owner wr_iot_close_owner;\n struct wr_iot_mbss_closed_probe wr_iot_closed_probe;\n#endif')
one('common/rtmp_init.c','pAd->wr_iot_control_users=pAd->wr_iot_control_poisoned=0;','pAd->wr_iot_control_users=pAd->wr_iot_control_poisoned=0;\n        NdisZeroMemory(&pAd->wr_iot_driver_owner,sizeof(pAd->wr_iot_driver_owner));\n        NdisZeroMemory(&pAd->wr_iot_close_owner,sizeof(pAd->wr_iot_close_owner));\n        NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));')
one('include/wr-iot-mcu-control-admission.inc','ready=!ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&','ready=!ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&\n       !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&')
# Reserved IoT close already revokes its producer and checked executor disables
# its CR. Preserve MAC-mode remake, but do not advance shared DTIM/coexistence
# or rebuild unrelated active beacon buffers as a side effect of this close.
one('ap/ap_mbss.c','\tAPMakeAllBssBeacon(pAd);\n\tAPUpdateAllBeaconFrame(pAd);',
    '\tAPMakeAllBssBeacon(pAd);\n\tif (!(IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT &&\n\t      pAd->ApCfg.BssidNum == 3 && BssId == 2))\n\t\tAPUpdateAllBeaconFrame(pAd);')
# BSS2 builders share the counted producer gate, but must be exclusive before
# inspecting mapped cells. Keep the pin while checking DMA outside ring lock.
one('include/wr-iot-beacon-producer-kernel.h',
 ' int ok;\n if (!ad || !ticket', ' int ok, protect;\n if (!ad || !ticket')
one('include/wr-iot-beacon-producer-kernel.h',
 ' ok = wr_iot_beacon_gate_begin(gate, gate->generation, ticket);',
 ' protect = IS_MT7603(ad) && ad->ApCfg.BssidNum == 3 && bss == 2;\n'
 ' ok = (!protect || !gate->active) &&\n'
 '      wr_iot_beacon_gate_begin(gate, gate->generation, ticket);')
one('include/wr-iot-beacon-producer-kernel.h',
 ' RTMP_SEM_UNLOCK(&ad->BcnRingLock);\n return ok;\n}\n\nstatic inline void wr_iot_bcn_producer_end',
 ' RTMP_SEM_UNLOCK(&ad->BcnRingLock);\n'
 ' if (ok && protect) {\n'
 '  int dma = WrBeaconDmaOutstanding(ad, (UINT32)bss), wake = 0;\n'
 '  RTMP_SEM_LOCK(&ad->BcnRingLock);\n'
 '  if (dma != 0 || ad->ApCfg.BssidNum != 3 || !wr_iot_beacon_gate_submit(gate, ticket)) {\n'
 '   ok = 0;\n'
 '   if (wr_iot_beacon_gate_end(gate, ticket) && !gate->active) wake = 1;\n'
 '  }\n'
 '  RTMP_SEM_UNLOCK(&ad->BcnRingLock);\n'
 '  if (wake) wake_up_all(&ad->wr_iot_beacon_wait);\n'
 ' }\n return ok;\n}\n\nstatic inline void wr_iot_bcn_producer_end')
# Serialize existing shared DMA filter commands across BSS recovery callers.
one('include/rtmp.h','#include "mbss-closed-probe.h"',
 '#include "mbss-closed-probe.h"\n#include "beacon-filter-owner.h"')
one('include/rtmp.h',' struct wr_iot_mbss_closed_probe wr_iot_closed_probe;',
 ' struct wr_iot_mbss_closed_probe wr_iot_closed_probe;\n struct wr_iot_beacon_filter_owner wr_iot_beacon_filter_owner;')
one('common/rtmp_init.c','NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));',
 'NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));\n        NdisZeroMemory(&pAd->wr_iot_beacon_filter_owner,sizeof(pAd->wr_iot_beacon_filter_owner));')
name='hw_ctrl/cmm_asic_mt.c';text=(src/name).read_text()
signature='VOID APCheckBcnQHandler(RTMP_ADAPTER *pAd, INT apidx, BOOLEAN *is_pretbtt_int)'
if text.count(signature)!=1:p.error('Shared beacon recovery signature changed')
start=text.index(signature);end=text.index('\n}',start)+2
inner=text[start:end].replace(signature,'static '+signature.replace('APCheckBcnQHandler','wr_iot_APCheckBcnQHandler_inner'),1)
wrapper='''
VOID APCheckBcnQHandler(RTMP_ADAPTER *pAd, INT apidx, BOOLEAN *is_pretbtt_int)
{
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 unsigned long token=0;
 if(!is_pretbtt_int)return;
 if(!pAd){*is_pretbtt_int=FALSE;return;}
 if(IS_MT7603(pAd)){
  *is_pretbtt_int=FALSE;
  if(!wr_iot_bcn_filter_enter(pAd,&token))return;
  wr_iot_APCheckBcnQHandler_inner(pAd,apidx,is_pretbtt_int);
  if(!wr_iot_bcn_filter_leave(pAd,token))*is_pretbtt_int=FALSE;
  return;
 }
#endif
 wr_iot_APCheckBcnQHandler_inner(pAd,apidx,is_pretbtt_int);
}
'''
changes[name]=text[:start]+'#include "beacon-filter-owner-kernel.h"\n'+inner+wrapper+text[end:]
main='os/linux/rt_main_dev.c'
signature='INT rt28xx_ioctl(PNET_DEV net_dev, struct ifreq *rq, INT cmd)\n{'
one(main,signature,guard+'\n#include <linux/rtnetlink.h>\n#include <linux/capability.h>\n#include "driver-api-owner-binding.inc"\n#include "driver-api-open-entry.inc"\n#include "driver-api-identity.inc"\n#include "mbss-closed-probe.h"\n#include "mt7603-closed-observe.h"\n#include "mt7603-closed-probe-binding.inc"\n#include "driver-api-closed-entry.inc"\n#endif\n'+signature)
one(main,'if(IS_MT7603(ad)&&!wr_iot_control_enter(ad))return -EBUSY;','if(cmd==WR_IOT_DRIVER_IOCTL_OPEN)return wr_iot_driver_open_ioctl(ad,net_dev,rq);\n if(cmd==WR_IOT_DRIVER_IOCTL_IDENTITY)return wr_iot_driver_identity_ioctl(ad,net_dev,rq);\n if(cmd==WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG)return wr_iot_driver_closed_ioctl(ad,net_dev,rq);\n if(IS_MT7603(ad)&&!wr_iot_control_enter(ad))return -EBUSY;')
name='include/wr-iot-mbss-open-admission.inc';s=(src/name).read_text()
s=s.replace('struct wr_iot_radio_ticket ticket;','struct wr_iot_radio_ticket ticket;\n const struct wr_iot_driver_open_request *api_request=NULL;',1)
a0=s.index(' record=wr_iot_registry_find_openable(');b0=s.index(' if(IS_MT7603(adapter)&&adapter->ApCfg.BssidNum>=3&&',a0)
# Replace preflight up to the separate BSS-index selection. Third-BSS owner
# already reserved this registry slot; ordinary Guest keeps its existing path.
s=s[:a0]+''' observe_iot=IS_MT7603(adapter)&&adapter->ApCfg.BssidNum>=3&&
   (unsigned int)adapter->ApCfg.BssidNum<=sizeof(adapter->ApCfg.MBSSID)/sizeof(adapter->ApCfg.MBSSID[0])&&
   adapter->ApCfg.MBSSID[2].wdev.if_dev==pDev;
 if(observe_iot){
  api_request=wr_iot_driver_owner_take(&adapter->wr_iot_driver_owner,current,
   pDev,&adapter->wr_iot_transition,adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1);
  record=api_request?wr_iot_registry_find(adapter->wr_iot_interface_refs,
   WDEV_NUM_MAX+1,pDev,adapter->wr_iot_driver_owner.claim.generation):NULL;
  ticket=adapter->wr_iot_driver_owner.ticket;
 }else record=wr_iot_registry_find_openable(adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,pDev);
 if(!record){RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);return -1;}
'''+s[b0:]
a0=s.index(' admitted=wr_iot_radio_begin(');b0=s.index(' RTMP_IRQ_UNLOCK(',a0)
s=s[:a0]+' admitted=observe_iot;\n if(!observe_iot){\n'+s[a0:b0]+' }\n'+s[b0:]
old='ret=!observe_iot||WR_IOT_MBSS_OBSERVE_MAIN(adapter);'
if s.count(old)!=1:p.error('Main observation anchor changed')
s=s.replace(old,'''ret=!observe_iot||(api_request&&wr_iot_precreated_key_matches(adapter,pDev,
  api_request->ssid,api_request->ssid_length,(const char *)api_request->password,
  api_request->password_length)&&WR_IOT_MBSS_OBSERVE_MAIN(adapter));''',1)
old='if(!ret||adapter->wr_iot_transition.busy!=WR_RADIO_BSS_OPEN||'
if s.count(old)!=1:p.error('MBSS pre-mutation revalidation changed')
s=s.replace(old,'''if(!ret||(observe_iot&&!wr_iot_virtual_open_claim_matches(
    &adapter->wr_iot_driver_owner.claim,&adapter->wr_iot_transition,
    adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1))||
    adapter->wr_iot_transition.busy!=WR_RADIO_BSS_OPEN||''',1)
# Mark possible mutation under the owned ticket, before the first raw call.
raw_anchor=' RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n ret=wr_iot_mbss_open_raw(pDev,&ticket,record->generation);'
if s.count(raw_anchor)!=1:p.error('MBSS raw mutation boundary changed')
s=s.replace(raw_anchor,' if(observe_iot)adapter->wr_iot_driver_owner.mutation_started=1;\n'+raw_anchor,1)
s='#include "precreated-key-match.h"\n'+s
changes[name]=s
for n in ('driver-api-close-wire.h','driver-api-open-current-wire.h','driver-api-open-current.h','driver-api-open-current-entry.inc','driver-api-close-admission.h','driver-api-close-owner.h','driver-api-close-binding.inc','beacon-filter-owner.h','beacon-filter-owner-kernel.h','driver-api-owner.h','driver-api-wire.h','driver-api-owner-binding.inc','driver-api-open-entry.inc','driver-api-identity.inc','radio-transition-api.h','mbss-close-receipt.h','mbss-closed-probe.h','mt7603-closed-observe.h','mt7603-closed-probe-binding.inc','driver-api-closed-entry.inc'):
 changes['include/'+n]=(local/n).read_text()
# Reuse existing privileged, RTNL-checked 64-byte observation transport.
compose_open_current=runpy.run_path(str(local/'open-current-composition.py'))['compose']
changes['include/driver-api-closed-entry.inc']=compose_open_current(changes['include/driver-api-closed-entry.inc'])
# Historical stages use the frozen base; only the API successor receives the extension.
# Extend the accumulated successor, not the frozen base: previous layers add
# shutdown/cleanup fields and lifecycle transitions that must survive this API.
extended_transition=transition_api['extend_transition']((src/'include/radio-transition.h').read_text())
changes['include/radio-transition.h']=extended_transition
changes['include/radio-transition-api.h']=extended_transition
# All source anchors/collisions verified before the first mutation.
for name,s in changes.items():(src/name).write_text(s)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['linux_open_api']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'ioctl_open': '0x89ff','ioctl_identity':'0x89fe','ioctl_closed_configuration':'0x89fd','production_installed':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
