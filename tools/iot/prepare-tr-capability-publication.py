#!/usr/bin/env python3
"""Stage final IRQ-ordered TR capability publication; not a reuse/drain proof."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
src = a.source.resolve(strict=True)
out = a.output.resolve()
if out.exists() or src == out or src in out.parents or out in src.parents:
    p.error('new separate output required')
rel = 'mgmt/mgmt_entrytb.c'
raw = (src / rel).read_bytes()
pin = '7b569ed0998905e6603271fd9a9b305381ce66f0beaba3b60a4f1f2558e85b05'
if hashlib.sha256(raw).hexdigest() != pin:
    p.error('unreviewed TR publication source')
s = raw.decode()
start = s.index('VOID tr_tb_set_entry(')
end = s.index('VOID tr_tb_set_mcast_entry(', start)
# The next function supplies a stable boundary for multicast initialization.
tail = s.index('\n}', end) + 2
unicast, multicast = s[start:end], s[end:tail]
reserve = '#ifdef DATA_QUEUE_RESERVE\n\t\ttr_entry->high_pkt_cnt = 0;\n\t\ttr_entry->high_pkt_drop_cnt = 0;\n#endif /* DATA_QUEUE_RESERVE */\n'
for body, indent in [(unicast, '\t\t'), (multicast, '\t')]:
    assert body.count(indent + 'tr_entry->enq_cap = TRUE;') == 1
    assert body.count(indent + 'tr_entry->deq_cap = TRUE;') == 1
def publish(indent):
    return (indent + '/* Publish initialized TR queues under their admission lock. */\n'
            + indent + '{\n' + indent + '\tULONG wr_iot_flags;\n'
            + indent + '\tRTMP_IRQ_LOCK(&pAd->irq_lock, wr_iot_flags);\n'
            + indent + '\tWRITE_ONCE(tr_entry->enq_cap, TRUE);\n'
            + indent + '\tWRITE_ONCE(tr_entry->deq_cap, TRUE);\n'
            + indent + '\tRTMP_IRQ_UNLOCK(&pAd->irq_lock, wr_iot_flags);\n'
            + indent + '}\n')
unicast = unicast.replace('\t\ttr_entry->enq_cap = TRUE;\n\t\ttr_entry->deq_cap = TRUE;\n', '')
anchor = '\t\tNdisMoveMemory(tr_entry->bssid, pEntry->wdev->bssid, MAC_ADDR_LEN);\n'
assert unicast.count(anchor) == 1
unicast = unicast.replace(anchor, reserve + anchor + publish('\t\t'))
multicast = multicast.replace('\ttr_entry->enq_cap = TRUE;\n\ttr_entry->deq_cap = TRUE;\n', '')
anchor = '\tNdisMoveMemory(tr_entry->bssid, wdev->bssid, MAC_ADDR_LEN);\n'
assert multicast.count(anchor) == 1
multicast = multicast.replace(anchor, anchor + publish('\t'))
s = s[:start] + unicast + multicast + s[tail:]
# Remove the old post-publication counter writes from the sole insertion caller.
old = '\t\t\ttr_tb_set_entry(pAd, i, pEntry);\n#ifdef DATA_QUEUE_RESERVE\n\t\t\ttr_entry->high_pkt_cnt = 0;\n\t\t\ttr_entry->high_pkt_drop_cnt = 0;\n#endif /* DATA_QUEUE_RESERVE */'
assert s.count(old) == 1
s = s.replace(old, '\t\t\ttr_tb_set_entry(pAd, i, pEntry);')
shutil.copytree(src, out)
(out / rel).write_text(s, encoding='utf-8', newline='\n')
out.with_name(out.name + '-tr-publication.json').write_text(json.dumps({
    'input_sha256': {rel: pin}, 'output_sha256': {rel: hashlib.sha256((out / rel).read_bytes()).hexdigest()},
    'scope': 'unicast/multicast initialization publication only; caller lifetime/reuse open',
    'target_compiled': False, 'production_installed': False, 'runtime_verified': False
}, indent=2) + '\n', encoding='utf-8')
print('Staged final TR capability publication; reuse/drain acceptance remains open')
