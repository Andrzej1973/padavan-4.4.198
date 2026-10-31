#!/usr/bin/env python3
"""Exclude counted WDS transactions from raw reset and close admission."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'wr-iot-wds-table-transaction.inc':'480d486d1d1fe051e6fd7b866f53761f744a9fa8af1d0eb6a4bfc715678f7a3d',
 'wr-iot-peer-close-executor.inc':'dd0e987aeeab120628bdae1268c9f045c3f65f2eb096295d0046b840f7d3c282',
 'wr-iot-reset-admission.inc':'33561d4e878a63d5bac225af818f69d2db3a514386266082ac02bbca6d77afef'}
texts={}
for name,digest in pins.items():
 f=src/'include'/name
 if hashlib.sha256(f.read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=f.read_text()
s=texts['wr-iot-wds-table-transaction.inc']
old='entered=wr_iot_peer_table_transaction_enter(&pAd->wr_iot_peer_table_owner);'
if s.count(old)!=1:p.error('changed WDS admission')
s=s.replace(old,'entered=wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor) &&\n  '+old[len('entered='):],1)
texts['wr-iot-wds-table-transaction.inc']='#define WR_IOT_WDS_EXECUTOR_GUARD 1\n'+s
s=texts['wr-iot-reset-admission.inc']
old='admitted=wr_iot_peer_close_executor_enter('
if s.count(old)!=1:p.error('changed reset admission')
s=s.replace(old,'admitted=!pAd->wr_iot_peer_table_owner.transactions &&\n  wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0) &&\n  wr_iot_peer_close_executor_enter(',1)
texts['wr-iot-reset-admission.inc']=s
s=texts['wr-iot-peer-close-executor.inc']
old='accepted=wr_iot_peer_close_executor_enter('
if s.count(old)!=2:p.error('changed close admission')
s=s.replace(old,'accepted=!pAd->wr_iot_peer_table_owner.transactions &&\n  wr_iot_peer_close_executor_enter(')
texts['wr-iot-peer-close-executor.inc']=s
shutil.copytree(src,out)
for name,text in texts.items():(out/'include'/name).write_text(text,encoding='utf-8',newline='\n')
print('Staged atomic counted-WDS exclusion against close/reset; other peer writers remain open')
