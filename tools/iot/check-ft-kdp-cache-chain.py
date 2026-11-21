#!/usr/bin/env python3
"""Compose actual cache snapshot/API predecessors with KDP on pinned sources.

Association-owner fields are a stand-in; this does not establish full adapter
predecessor/target correctness.
"""
import argparse,hashlib,json,runpy
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path);p.add_argument('--prepared-owner',action='store_true');a=p.parse_args()
here=Path(__file__).resolve().parent

def module(name):return runpy.run_path(str(here/name))
changes=module('assoc-generation-composition.py')['compose']({},a.source,here)
if not a.prepared_owner:
 anchor='\tMAC_TABLE MacTab;'
 assert changes['include/rtmp.h'].count(anchor)==1
 changes['include/rtmp.h']=changes['include/rtmp.h'].replace(anchor,
  ' struct wr_iot_peer_table_owner wr_iot_peer_table_owner;\n'
  ' struct wr_iot_peer_close_executor wr_iot_peer_close_executor;\n'+anchor,1)
else:
 for field in ('struct wr_iot_peer_table_owner wr_iot_peer_table_owner;', 'struct wr_iot_peer_close_executor wr_iot_peer_close_executor;'):
  assert field in changes['include/rtmp.h']
for name in ('ft-pending-insert-composition.py','ft-iapp-request-state-composition.py'):
 changes=module(name)['compose'](changes,a.source,here)
changes=module('ft-cache-storage-composition.py')['compose'](changes,here)
snapshot=module('ft-r1kh-snapshot-composition.py')
source,header=snapshot['compose']((a.source/'common/ft.c').read_text(),(a.source/'include/ft.h').read_text())
api=module('ft-cache-api-lifetime-composition.py')
changes['common/ft.c']=api['compose_maintenance'](api['compose_api'](source))
changes['include/ft.h']=header
related=snapshot['compose_related']({name:(a.source/name).read_text(encoding='latin1') for name in ('ap/ap_ftkd.c','common/cmm_wpa.c')})
changes.update(related)
package=module('ft-kdp-package-composition.py')['compose'](changes,a.source,here)
lifecycle=module('ft-cache-native-lifecycle-composition.py')['compose_map']
package=lifecycle(package,a.source)
for symbol in ('wr_ft_cache_initialize_checked','wr_ft_cache_release_checked'):
 assert package['common/ft.c'].count('BOOLEAN '+symbol+'(')==1
 assert package['include/ft.h'].count('BOOLEAN '+symbol+'(')==1
try:lifecycle(package,a.source)
except ValueError:pass
else:raise AssertionError('duplicate lifecycle map accepted')
assert 'wr_ft_r1kh_snapshot(' in package['ap/ap_ftkd.c']
assert 'wr_ft_kdp_encrypt_checked(' in package['ap/ap_ftkd.c']
assert package['common/rtmp_init.c'].count('wr_ft_cache_lifetime_init(')==1
assert package['include/rtmp.h'].count('wr_ft_cache_lifetime_initialized;')==1
assert package['include/ft.h'].count('BOOLEAN wr_ft_kdp_encrypt_checked(')==1
for n in ('ap/ap_ftkd.c','common/cmm_wpa.c'):
 assert 'FT_R1khEntryTabLookup(' not in package[n]
if a.output:
 a.output.write_text(json.dumps({'scope':'actual snapshot/cache API/storage and KDP source-map composition', 'prepared_owner_input':a.prepared_owner, 'owner_schema_standin':not a.prepared_owner,'exit_code':0,'prepared_sha256':{n:hashlib.sha256(v.encode('latin1')).hexdigest() for n,v in package.items()},'producer_installed':False,'target_compiled':False,'remaining':([] if a.prepared_owner else ['actual association-owner predecessor'])+['KDP full-operation admission/release','native AP lifecycle and target compile','image/device']},indent=2)+'\n')
print('PASS | FT cache/KDP chain | actual snapshot/API/storage and checked KDP callers compose; '+('actual prepared owner input' if a.prepared_owner else 'owner schema stand-in')+'; no target compile')
