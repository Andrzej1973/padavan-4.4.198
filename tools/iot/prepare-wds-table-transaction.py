#!/usr/bin/env python3
"""Exclude reset/delete while synchronous normal WDS transaction uses peer."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
name='ap/ap_wds.c';raw=(src/name).read_bytes()
pin='a339900429a921a4678c6c21d4b6fa84fb347dc7ebe866e89d55f955abff50a9'
if hashlib.sha256(raw).hexdigest()!=pin:p.error('unreviewed WDS predecessor')
s=raw.decode();anchor='static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_identity('
if s.count(anchor)!=1:p.error('unique identity body required')
start=s.index(anchor);end=s.index('\n}',start)+2
body=s[start:end].replace(anchor,'static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_identity_body(',1)
s=s[:start]+body+'\n#include "wr-iot-wds-table-transaction.inc"\n'+s[end:]
shutil.copytree(src,out);(out/name).write_text(s,encoding='utf-8',newline='\n')
for local,target in [('peer-table-owner.h','peer-table-owner.h'),('peer-table-delete-gate.inc','wr-iot-peer-table-delete-gate.inc'),('wds-table-transaction.inc','wr-iot-wds-table-transaction.inc')]:
 shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-wds-table-transaction.json').write_text(json.dumps({
 'input_sha256':{name:pin},'output_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest()},
 'scope':'synchronous normal WDS transaction versus exclusive reset/ordinary delete; full clears unbound',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged whole normal WDS transaction admission against table reset/delete')
