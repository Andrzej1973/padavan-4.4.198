#!/usr/bin/env python3
"""Bind outer WDS insertion count to registration removal admission."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'ap/ap_wds.c':'e15fc9d9bcdb8fe04343bf14332a2b73d74441996068a64cee7da1dd5e200122',
 'include/interface-registry.h':'e90b709fe492b7f886b4278d46480a7b32a3deab5651620f6018801534a32f82',
 'include/interface-reference.h':'b9e276cd6720667230afb5ccec013d5d2ffa0f704d38c52666aae2b1eb7cfb6d',
 'include/aux-close-claim.h':'96d56ef124b6ca486e87a8f637a6c1d56f1ecd3d7e6e21736c35888108b602d7'}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed source: '+n)
ref=(src/'include/interface-reference.h').read_text()
ref=ref.replace('#define WR_IOT_INTERFACE_REFERENCE_H','#define WR_IOT_INTERFACE_REFERENCE_H\n#include "wds-peer-operation.h"',1)
ref=ref.replace('struct wr_iot_interface_ref {','struct wr_iot_interface_ref {\n struct wr_iot_wds_peer_operation peer_operation;',1)
anchor=' r->device=device;r->generation=generation;';assert ref.count(anchor)==1
ref=ref.replace(anchor,' wr_iot_wds_peer_operation_init(&r->peer_operation,device,generation);\n'+anchor,1)
anchor=' if(!wr_iot_ref_matches(r,device,generation,token)||r->phase!=WR_REF_OWNED)return 0;'
assert ref.count(anchor)==1
ref=ref.replace(anchor,' if(r&&r->peer_operation.active)return 0;\n'+anchor,1)
registry=(src/'include/interface-registry.h').read_text()
anchor=' r->removing=1;return 1;';assert registry.count(anchor)==1
registry=registry.replace(anchor,' if(r->peer_operation.active)return 0;\n'+anchor,1)
anchor=' if(!r||!device||r->device!=device||!generation||r->generation!=generation||'
assert registry.count(anchor)==1
registry=registry.replace(anchor,' if(r&&r->peer_operation.active)return 0;\n'+anchor,1)
s=(src/'ap/ap_wds.c').read_text()
start=s.index('MAC_TABLE_ENTRY *MacTableInsertWDSEntry(')
end=s.index('MAC_TABLE_ENTRY *WdsTableLookupByWcid(',start)
body=s[start:end].replace('MAC_TABLE_ENTRY *MacTableInsertWDSEntry(',
 'static MAC_TABLE_ENTRY *wr_iot_wds_insert_body(',1)
wrapper='''MAC_TABLE_ENTRY *MacTableInsertWDSEntry(RTMP_ADAPTER *pAd, UCHAR *pAddr, UINT WdsTabIdx)
{
 struct wr_iot_interface_ref *record = NULL;
 MAC_TABLE_ENTRY *result;
 PNET_DEV device;
 ULONG flags;
 UINT slot;
 unsigned long generation = 0;
 if (!pAd || !pAddr || WdsTabIdx >= MAX_WDS_ENTRY) return NULL;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 device = pAd->WdsTab.WdsEntry[WdsTabIdx].wdev.if_dev;
 if (device && !pAd->wr_iot_transition.retiring &&
     !pAd->wr_iot_transition.pm_suspending && !pAd->wr_iot_transition.pm_suspended) {
  for (slot = 0; slot < WDEV_NUM_MAX + 1; slot++) {
   struct wr_iot_interface_ref *r = &pAd->wr_iot_interface_refs[slot];
   if (r->device == device && r->published && !r->removing &&
       r->family == WR_REF_FAMILY_WDS && r->phase == WR_REF_OWNED &&
       wr_iot_wds_peer_operation_enter(&r->peer_operation, device, r->generation)) {
    if (!wr_iot_radio_tx_enter(&pAd->wr_iot_transition)) {
     (void)wr_iot_wds_peer_operation_leave(&r->peer_operation, device, r->generation);
     break;
    }
    dev_hold((struct net_device *)device);
    record = r; generation = r->generation; break;
   }
  }
 }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 if (!record) return NULL;
 result = wr_iot_wds_insert_body(pAd, pAddr, WdsTabIdx);
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 if (wr_iot_wds_peer_operation_leave(&record->peer_operation, device, generation))
  (void)wr_iot_radio_tx_leave(&pAd->wr_iot_transition);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 wake_up_all(&pAd->wr_iot_ticket_wait);
 dev_put((struct net_device *)device);
 return result;
}

'''
s=s[:start]+body+wrapper+s[end:]
shutil.copytree(src,out)
aux=(src/'include/aux-close-claim.h').read_text()
anchor=' if(!record||record->family!=family||!record->last_token||'
assert aux.count(anchor)==1
aux=aux.replace(anchor,' if(record&&record->peer_operation.active)return 0;\n'+anchor,1)
changed={'ap/ap_wds.c':s,'include/interface-reference.h':ref,'include/interface-registry.h':registry,'include/aux-close-claim.h':aux}
for n,t in changed.items():(out/n).write_text(t,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('wds-peer-operation.h'),out/'include/wds-peer-operation.h')
out.with_name(out.name+'-outer-operation.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changed},
 'scope':'outer insertion count/removal admission; full adapter/PCI/callback lifetime not proved',
 'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged whole WDS insertion wrapper and registry active-operation refusal')
