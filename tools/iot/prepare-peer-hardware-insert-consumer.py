#!/usr/bin/env python3
"""Prevent unicast peer publication after failed checked MT hardware insertion."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
receipt=json.loads(src.with_name(src.name+'-ageout-recovery.json').read_text())
if hashlib.sha256((src/'include/wr-iot-wds-ageout-transaction.inc').read_bytes()).hexdigest()!=receipt['output_sha256']:
    p.error('age-out recovery predecessor mismatch')
rel='mgmt/mgmt_entrytb.c';raw=(src/rel).read_bytes();s=raw.decode()
pins={rel:'e88da24c3eb70dfde742bbf1384b24ec0e831884bb18c633672eb57c4f6fad2b',
      'include/rtmp.h':'95599cd547a5b88b3164af646dacb7c2a9aedb721d6c9631a3fec4eca8af8f23'}
for name,digest in pins.items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed insertion input: '+name)
start=s.index('MAC_TABLE_ENTRY *MacTableInsertEntry(');end=s.index('INT mac_tb_del_from_hash(',start)
body=s[start:end];anchor='RTMP_STA_ENTRY_ADD(pAd, pEntry);'
if body.count(anchor)!=1:p.error('unreviewed insertion hardware call')
body=body.replace(anchor,'\n#include "wr-iot-peer-hardware-insert-result.inc"',1)
s=s[:start]+body+s[end:]
start=s.index('BOOLEAN tr_tb_set_entry(');end=s.index('VOID tr_tb_set_mcast_entry(',start)
body=s[start:end];anchor='\t\ttr_entry->EntryType = pEntry->EntryType;'
if body.count(anchor)!=1:p.error('unreviewed TR setup')
body=body.replace(anchor,'\t\ttr_entry->wr_iot_setup_observed = FALSE;\n\t\ttr_entry->wr_iot_setup_result = 0;\n'+anchor,1)
s=s[:start]+body+s[end:]
h=(src/'include/rtmp.h').read_text();anchor='typedef struct _STA_TR_ENTRY{'
if h.count(anchor)!=1:p.error('unreviewed TR layout')
h=h.replace(anchor,anchor+'\n\tUINT32 wr_iot_setup_observed;\n\tINT wr_iot_setup_result;',1)
shutil.copytree(src,out)
(out/rel).write_text(s,encoding='utf-8',newline='\n')
(out/'include/rtmp.h').write_text(h,encoding='utf-8',newline='\n')
helper=Path(__file__).with_name('peer-hardware-insert-result.inc')
shutil.copyfile(helper,out/'include/wr-iot-peer-hardware-insert-result.inc')
out.with_name(out.name+'-hardware-insert-consumer.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in (rel,'include/rtmp.h')},
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'scope':'unicast MT failure closes admission and prevents hash publication; retained insertion cleanup unbound',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged MT insertion failure retention before peer publication')
