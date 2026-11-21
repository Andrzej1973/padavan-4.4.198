#!/usr/bin/env python3
"""Verify one complete pending arbitration source set and exact installed seams."""
import argparse,hashlib,json,runpy
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--prepared-driver',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)
base['common/cmm_wpa.c']=runpy.run_path(str(here/'ra2-gtk-request-composition.py'))['compose'](base['common/cmm_wpa.c'])
base['ap/ap_wpa.c']=runpy.run_path(str(here/'ra2-rekey-composition.py'))['compose']((a.source/'ap/ap_wpa.c').read_text())
for name in ('ra2-rekey-admission.h','ra2-gtk-request-kernel.h'):
 base['include/'+name]=(here/name).read_text()
# The delete-execution predecessor adds this admission before the Linux API
# producer. Reproduce that exact reviewed transformation, not pristine input.
insertion=(here/'peer-normal-insert.inc').read_text()
anchor='entered=wr_iot_peer_close_executor_idle('
assert insertion.count(anchor)==1
insertion=insertion.replace(anchor,
 'entered=!pAd->wr_iot_peer_delete_active && wr_iot_peer_close_executor_idle(',1)
base['include/wr-iot-peer-normal-insert.inc']=insertion
compose=runpy.run_path(str(here/'ra2-mutation-binding.py'))['compose_all']
expected=compose(base,a.source,here)
assert expected['ap/ap_wpa.c'].count('wr_ra2_rekey_peers_enter(ad,&peers)')==1
assert expected['include/ra2-gtk-request-kernel.h'].count('&scope->key_ticket,1)')==1
assert expected['include/wr-iot-peer-normal-insert.inc'].count('wr_ra2_mutation_enter_wdev(')==1
assert expected['include/rtmp.h'].count('struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')==1
# Regression for optional1408: verify the full predecessor+arbiter fragment,
# and prove neither omission of deletion admission nor a missing wrapper passes.
def verify_insertion_fragment(actual):
 name='include/wr-iot-peer-normal-insert.inc'
 assert actual==expected[name],name
fragment=expected['include/wr-iot-peer-normal-insert.inc']
verify_insertion_fragment(fragment)
for stale in (fragment.replace('!pAd->wr_iot_peer_delete_active && ',''),insertion):
 assert stale!=fragment
 try:verify_insertion_fragment(stale)
 except AssertionError:pass
 else:raise AssertionError('incomplete insertion admission accepted')
try:compose(expected,a.source,here)
except ValueError:pass
else:raise AssertionError('duplicate binding accepted')
if a.prepared_driver:
 # Other predecessor stages legitimately modify assoc/auth/table bodies.
 # Exact generated outer wrappers and included helper fragments must match.
 for name in ('include/ra2-association-owner.h','include/ra2-mutation-admission-kernel.h',
              'include/ra2-rekey-peer-scope.h','include/ra2-gtk-request-kernel.h',
              'include/wr-iot-peer-normal-insert.inc','common/cmm_wpa.c','ap/ap_wpa.c'):
  assert (a.prepared_driver/name).read_text()==expected[name],name
 wrappers=runpy.run_path(str(here/'ra2-mutation-wrappers.py'))
 for name in wrappers['SITES']:
  _,receipts=wrappers['compose'](name,base.get(name,(a.source/name).read_text()))
  actual=(a.prepared_driver/name).read_text()
  for wrapper,_ in receipts:assert actual.count(wrapper)==1,name
 header=(a.prepared_driver/'include/rtmp.h').read_text()
 assert header.count('struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')==1
 assert '#include "ra2-mutation-admission-kernel.h"' in (a.prepared_driver/'mgmt/mgmt_entrytb.c').read_text()
report={'scope':'Complete arbitration source composition; execution fixtures run separately',
 'expected_sha256':{name:hashlib.sha256(text.encode()).hexdigest() for name,text in expected.items()},
 'prepared_file_sha256':{name:hashlib.sha256((a.prepared_driver/name).read_bytes()).hexdigest()
     for name in expected if (a.prepared_driver/name).is_file()} if a.prepared_driver else {},
 'insertion_predecessor_negative_controls':True,
 'prepared_source_verified':a.prepared_driver is not None,'production_installed':False,'target_compiled':False,'runtime_verified':False}
if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
print('Combined arbitration source anchors and duplicate refusal: PASS')
