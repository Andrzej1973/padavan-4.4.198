#!/usr/bin/env python3
"""Report actual TR insertion readiness gaps; --require-ready fails closed."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--require-ready', action='store_true')
a = p.parse_args()
if a.output.exists():
    p.error('new report required')
path = a.source / 'mgmt/mgmt_entrytb.c'
raw = path.read_bytes()
s = raw.decode()
start = s.index('BOOLEAN tr_tb_set_entry(')
end = s.index('VOID tr_tb_set_mcast_entry(', start)
body = s[start:end]
call = s.index('if (!tr_tb_set_entry(pAd, i, pEntry))', end)
uapsd = s.index('UAPSD_MR_ENTRY_INIT(pEntry);', call)
hash_start = s.index('/* add this MAC entry into HASH table */', call)
wtbl = body.index('if (mt_wtbl_get_entry234(')
failure_return = body.index('return FALSE;', wtbl)
queue_init = body.index('InitializeQueueHeader(&tr_entry->tx_queue[qidx])')
publication = s.index('WRITE_ONCE(tr_entry->enq_cap, TRUE)', uapsd)
findings = [
    {'id': 'wtbl-status-not-propagated',
     'observed': failure_return < queue_init and body.startswith('VOID '),
     'detail': 'WTBL failure returns before queues exist; insertion caller receives no status.'},
    {'id': 'uapsd-initialized-after-tr-publication',
     'observed': publication < uapsd or uapsd > hash_start,
     'detail': 'TR publishes inside callee before caller initializes UAPSD; feature guards require target review.'},
]
report = {'source_sha256': hashlib.sha256(raw).hexdigest(), 'findings': findings,
          'ready': not any(f['observed'] for f in findings),
          'scope': 'source-order audit, not concurrency/target acceptance',
          'next': 'propagate setup failure with reviewed unwind and publish only after all required initialization'}
a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
active = ', '.join(f['id'] for f in findings if f['observed'])
print('SOURCE-ORDER READY; remaining concurrency/lifetime proof open' if not active else 'NOT READY: ' + active)
if a.require_ready:
    raise SystemExit(1)
