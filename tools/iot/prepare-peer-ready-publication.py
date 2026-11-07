#!/usr/bin/env python3
"""Defer unicast queue admission to insertion completion in isolated source."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path); p.add_argument('output', type=Path)
a = p.parse_args(); src = a.source.resolve(strict=True); out = a.output.resolve()
if out.exists() or src == out or src in out.parents or out in src.parents:
    p.error('new separate output required')
rel = 'mgmt/mgmt_entrytb.c'; raw = (src/rel).read_bytes()
pin = '32c93095fbabf050487df01cdfcb1efbe193980e86aa6b4422998eef81fb10dc'
if hashlib.sha256(raw).hexdigest() != pin:
    p.error('unreviewed source')
s = raw.decode(); start = s.index('BOOLEAN tr_tb_set_entry(')
end = s.index('VOID tr_tb_set_mcast_entry(', start)
body = s[start:end]
marker = '\t\t/* Publish initialized TR queues under their admission lock. */'
begin = body.index(marker); finish = body.index('\n\t\t}', begin) + len('\n\t\t}')
block = body[begin:finish]
body = body[:begin] + body[finish:]
# Explicitly deny stale admission before reinitializing any TR fields.
anchor = '\t\ttr_entry = &pAd->MacTab.tr_entry[tr_tb_idx];'
assert body.count(anchor) == 1
deny = block.replace('/* Publish initialized TR queues under their admission lock. */',
                     '/* Keep admission closed until the insertion caller is ready. */').replace(', TRUE)', ', FALSE)')
body = body.replace(anchor, anchor + '\n' + deny, 1)
s = s[:start] + body + s[end:]
start = s.index('MAC_TABLE_ENTRY *MacTableInsertEntry(')
end = s.index('\nINT mac_tb_del_from_hash(', start)
body = s[start:end]
anchor = '\tNdisReleaseSpinLock(&pAd->MacTabLock);\n\t\n\t/*update tx burst'
assert body.count(anchor) == 1
publish = ('\t/* Publish peer admission only after insertion initialization. */\n'
           '\tif (pEntry) {\n'
           + '\n'.join(line[1:] for line in block.splitlines()) + '\n\t}\n\n')
body = body.replace(anchor, publish + anchor, 1)
s = s[:start] + body + s[end:]
shutil.copytree(src, out); (out/rel).write_text(s, encoding='utf-8', newline='\n')
out.with_name(out.name+'-peer-ready.json').write_text(json.dumps({
    'input_sha256':{rel:pin},'output_sha256':{rel:hashlib.sha256((out/rel).read_bytes()).hexdigest()},
    'scope':'unicast insertion admission order; callback side effects/reuse unproved',
    'target_compiled':False,'production_installed':False,'runtime_verified':False},indent=2)+'\n')
print('Staged caller-ready unicast publication; multicast path unchanged')
