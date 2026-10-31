#!/usr/bin/env python3
"""Reserve whole ordinary deletion and preserve parent-reset serial ownership."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'mgmt/mgmt_entrytb.c':'508de7330f243a1e3ea8ef20df177a8ab1e39b9a8fcb9c38939e636207af020e',
 'include/wr-iot-peer-close-executor.inc':'134c2110611b6180a006c085c690cf79b8fcaea663bbaa49098a0ee83ca47120'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
name='mgmt/mgmt_entrytb.c';s=texts[name];signature='static BOOLEAN wr_iot_mac_delete_entry('
if s.count(signature)!=1:p.error('changed private deletion')
start=s.index(signature);end=s.index('\n}',start)+2
body=s[start:end].replace(signature,'static BOOLEAN wr_iot_mac_delete_entry_body(',1)
texts[name]=s[:start]+body+'\n#include "wr-iot-peer-normal-delete.inc"'+s[end:]
name='include/wr-iot-peer-close-executor.inc';s=texts[name]
old='accepted=!pAd->wr_iot_peer_table_owner.transactions &&'
if s.count(old)!=2:p.error('changed close admission')
# Exact retained close serial may continue; an unrelated delete/open/reset may not.
new=old+'''
  !pAd->wr_iot_peer_table_owner.retained && !pAd->wr_iot_peer_table_owner.poisoned &&
  (!pAd->wr_iot_peer_table_owner.active ||
   (pAd->wr_iot_peer_close_serial && pAd->wr_iot_peer_close_serial==pAd->wr_iot_peer_table_owner.serial)) &&'''
texts[name]=s.replace(old,new)
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('peer-normal-delete.inc'),out/'include/wr-iot-peer-normal-delete.inc')
print('Staged whole ordinary deletion reservation; failures retain table, recovery still unbound')
