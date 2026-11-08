#!/usr/bin/env python3
"""Bind authorized OPEN API in a hash-checked isolated candidate, never production."""
import argparse, hashlib, json, runpy
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();local=Path(__file__).parent
runpy.run_path(str(local/'check-radio-transition-api.py'),run_name='__main__')
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
one('include/rtmp.h','#include "interface-registry.h"','#include "interface-registry.h"\n'+guard+'\n#include "driver-api-owner.h"\n#include "mbss-closed-probe.h"\n#endif')
one('include/rtmp.h','NDIS_SPIN_LOCK wr_iot_transition_lock;','NDIS_SPIN_LOCK wr_iot_transition_lock;\n'+guard+'\n struct wr_iot_driver_owner wr_iot_driver_owner;\n struct wr_iot_mbss_closed_probe wr_iot_closed_probe;\n#endif')
one('common/rtmp_init.c','pAd->wr_iot_control_users=pAd->wr_iot_control_poisoned=0;','pAd->wr_iot_control_users=pAd->wr_iot_control_poisoned=0;\n        NdisZeroMemory(&pAd->wr_iot_driver_owner,sizeof(pAd->wr_iot_driver_owner));\n        NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));')
one('include/wr-iot-mcu-control-admission.inc','ready=!ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&','ready=!ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&\n       !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&')
# Reserved IoT close already revokes its producer and checked executor disables
# its CR. Preserve MAC-mode remake, but do not advance shared DTIM/coexistence
# or rebuild unrelated active beacon buffers as a side effect of this close.
one('ap/ap_mbss.c','\tAPMakeAllBssBeacon(pAd);\n\tAPUpdateAllBeaconFrame(pAd);',
    '\tAPMakeAllBssBeacon(pAd);\n\tif (!(IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT &&\n\t      pAd->ApCfg.BssidNum == 3 && BssId == 2))\n\t\tAPUpdateAllBeaconFrame(pAd);')
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
for n in ('driver-api-owner.h','driver-api-wire.h','driver-api-owner-binding.inc','driver-api-open-entry.inc','driver-api-identity.inc','radio-transition-api.h','mbss-close-receipt.h','mbss-closed-probe.h','mt7603-closed-observe.h','mt7603-closed-probe-binding.inc','driver-api-closed-entry.inc'):
 changes['include/'+n]=(local/n).read_text()
# Historical stages use the frozen base; only the API successor receives the extension.
changes['include/radio-transition.h']=(local/'radio-transition-api.h').read_text()
# All source anchors/collisions verified before the first mutation.
for name,s in changes.items():(src/name).write_text(s)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['linux_open_api']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'ioctl_open': '0x89ff','ioctl_identity':'0x89fe','ioctl_closed_configuration':'0x89fd','production_installed':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
