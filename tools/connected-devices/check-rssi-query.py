#!/usr/bin/env python3
"""Exact-source query preparation checks, not ioctl execution proof."""
import argparse,subprocess,sys,shutil,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
tools=Path(__file__).parent
subprocess.run([sys.executable,str(tools/'check-rssi-removal.py'),str(a.source),str(a.output)],check=True)
for radio in ('mt76x2','mt76x3'):
 rel=Path('trunk/linux-4.4.x/drivers/net/wireless/mediatek')/radio/'ap/ap_cfg.c'
 (a.output/rel).write_bytes((a.source/rel).read_bytes())
bad=a.output.with_name(a.output.name+'-conflict');shutil.copytree(a.output,bad)
changed=bad/'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_cfg.c'
changed.write_text(changed.read_text()+'\n#define CONFLICTING_QUERY 0x7e01\n')
def snapshot(root):return {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
def run(root):return subprocess.run([sys.executable,str(tools/'prepare-rssi-query.py'),str(root)],capture_output=True,text=True)
before=snapshot(bad);r=run(bad);assert r.returncode and snapshot(bad)==before
r=run(a.output);assert not r.returncode,r.stderr
for radio,band in (('mt76x2',1),('mt76x3',0)):
 root=a.output/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio
 text=(root/'ap/ap_cfg.c').read_text()
 assert text.count('case WR_RSSI_QUERY_OID:')==1
 assert text.index('INT RTMPAPQueryInformation(')<text.index('case WR_RSSI_QUERY_OID:')
 assert str(band)+', wrq->u.data.pointer' in text
 assert 'if (wr_status == 0) wrq->u.data.length = wr_written;' in text
 for name in ('wr-rssi-query-handler.h','wr-rssi-query-response.h','wr-rssi-query-record.h'):
  header=(root/'include'/name).read_text()
  for include in re.findall(r'#include "([^"]+)"',header):assert (root/'include'/include).is_file(),include
before=snapshot(a.output);assert run(a.output).returncode and snapshot(a.output)==before
print('PASS actual query dispatch/radio/header closure, repeat rejection and second-radio conflict without writes')
