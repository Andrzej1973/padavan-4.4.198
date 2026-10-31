#!/usr/bin/env python3
"""Replace rejected delete57 with a synchronous lease preserving WDS recovery."""
import argparse,hashlib,shutil,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={
 'mgmt/mgmt_entrytb.c':'508de7330f243a1e3ea8ef20df177a8ab1e39b9a8fcb9c38939e636207af020e',
 'include/rtmp.h':'717ae4be4d7b4ccf61e19283182ff1a4e1f9e27bc0034d8b11f64fdd7647e083',
 'common/rtmp_init.c':'ffac1cd5c048aa423cc5eb55a830276a173c62a59b32e2a5c76d92f810bd9b1d',
 'include/wr-iot-peer-normal-insert.inc':'36a9adc5beeff3afb274f4cd299ad0dbc7e1df037948e0d1fb0253ea59a58cef',
 'include/wr-iot-wds-table-transaction.inc':'4dcc5e33814caae4abb5b2235a0eb6918e7b73838a2857d1e696875608502e27',
 'include/wr-iot-peer-table-reset-owner.inc':'ecf2d81abfc653e93b9158b8066067500c2ccbd247a3ea75b5bdc0b11491afe7',
 'include/wr-iot-peer-open-dispatch.inc':'a3091b2b862243c7ecbb15f049c73fbd756c4b669dd6c5de1b7bcfc0e6c9c76f',
 'include/wr-iot-peer-close-executor.inc':'134c2110611b6180a006c085c690cf79b8fcaea663bbaa49098a0ee83ca47120',
 'include/wr-iot-reset-admission.inc':'200ccfb4467ac90680d132e30da131c6173ab3b160e055a977ac36b32329ad5c',
 'include/wr-iot-peer-table-insertion-gate.inc':'d44df2c6696dbb6ed4be57d4ce19e5abdf20aae29ba058dbf128fc99599566b3',
 'include/wr-iot-peer-startup-insertion-gate.inc':'3d1e232197d4d8ee34c5ceaa467d2c91c23a85ac261a699da6d0a105dc124c52',
 'easy_setup/mt7603_chip_ops.c':'d1f25668cba023f8ca975ff707d8872e8b42870be9e27ccb0789b3f754772204'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(name,old,new,count=1):
 if texts[name].count(old)!=count:p.error('changed anchor: '+name+': '+old)
 texts[name]=texts[name].replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_peer_legacy_close_state;',
 'unsigned int wr_iot_peer_legacy_close_state;\n unsigned int wr_iot_peer_delete_active;')
one('common/rtmp_init.c','pAd->wr_iot_peer_legacy_close_state=0;',
 'pAd->wr_iot_peer_legacy_close_state=0;\n\t\tpAd->wr_iot_peer_delete_active=0;')
name='mgmt/mgmt_entrytb.c';s=texts[name];sig='static BOOLEAN wr_iot_mac_delete_entry('
start=s.index(sig);end=s.index('\n}',start)+2
texts[name]=s[:start]+s[start:end].replace(sig,'static BOOLEAN wr_iot_mac_delete_entry_body(',1)+'\n#include "wr-iot-peer-normal-delete.inc"'+s[end:]
for name in ['include/wr-iot-peer-normal-insert.inc','include/wr-iot-wds-table-transaction.inc']:
 one(name,'entered=wr_iot_peer_close_executor_idle(',
  'entered=!pAd->wr_iot_peer_delete_active && wr_iot_peer_close_executor_idle(')
for name in ['include/wr-iot-peer-table-reset-owner.inc','include/wr-iot-peer-table-insertion-gate.inc']:
 one(name,'if (!wr_iot_peer_table_allows(', 'if (pAd->wr_iot_peer_delete_active || !wr_iot_peer_table_allows(')
one('include/wr-iot-peer-startup-insertion-gate.inc','if (wr_open_ticket || wr_open_lease) {',
 '''if(pAd->wr_iot_peer_delete_active){NdisReleaseSpinLock(&pAd->MacTabLock);return NULL;}
 if (wr_open_ticket || wr_open_lease) {''')
one('include/wr-iot-peer-open-dispatch.inc','if (request->serial || pAd->MacTab.Size ||',
 'if (pAd->wr_iot_peer_delete_active || request->serial || pAd->MacTab.Size ||')
one('include/wr-iot-peer-close-executor.inc','accepted=!pAd->wr_iot_peer_table_owner.transactions &&',
 '''accepted=!pAd->wr_iot_peer_delete_active && !pAd->wr_iot_peer_table_owner.transactions &&
  !pAd->wr_iot_peer_table_owner.retained && !pAd->wr_iot_peer_table_owner.poisoned &&
  (!pAd->wr_iot_peer_table_owner.active ||
   (pAd->wr_iot_peer_close_serial && pAd->wr_iot_peer_close_serial==pAd->wr_iot_peer_table_owner.serial)) &&''',2)
one('include/wr-iot-reset-admission.inc','admitted=!pAd->wr_iot_peer_table_owner.transactions &&',
 'admitted=!pAd->wr_iot_peer_delete_active && !pAd->wr_iot_peer_table_owner.transactions &&')
one('easy_setup/mt7603_chip_ops.c','if (!wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0)) {',
 'if (pAd->wr_iot_peer_delete_active || !wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0)) {')
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('peer-delete-execution.inc'),out/'include/wr-iot-peer-normal-delete.inc')
out.with_name(out.name+'-manifest.json').write_text(json.dumps({'input_sha256':pins,
 'scope':'synchronous deletion lease; existing per-entry WDS recovery unchanged',
 'target_compiled':False,'runtime_verified':False,'adapter_release_bound':False},indent=2)+'\n')
print('Staged deletion execution lease preserving WDS checkpoint resume')
