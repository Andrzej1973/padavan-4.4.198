#!/usr/bin/env python3
"""Check actual source preparation and rejection without partial mutation."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
tools=Path(__file__).parent
if a.output.exists():raise ValueError('Fresh output directory required')
a.output.mkdir(parents=True)
paths=[Path('trunk/linux-4.4.x/drivers/net/wireless/mediatek')/r/f
       for r in ('mt76x2','mt76x3') for f in ('include/rtmp.h','common/rtmp_init.c')]
def fixture(name):
 root=a.output/name
 for rel in paths:
  dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((a.source/rel).read_bytes())
 return root
def run(root):
 return subprocess.run([sys.executable,str(tools/'prepare-rssi-adapter.py'),str(root)],capture_output=True,text=True)
def snapshot(root):return {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
good=fixture('good');result=run(good);assert result.returncode==0,result.stderr
for radio in ('mt76x2','mt76x3'):
 root=good/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio
 h=(root/'include/rtmp.h').read_text();s=(root/'common/rtmp_init.c').read_text()
 assert h.count('struct wr_rssi_kernel wr_rssi_observer;')==1
 assert s.count('wr_rssi_kernel_init(&pAd->wr_rssi_observer);')==1
 assert '\t\twr_rssi_kernel_init(&pAd->wr_rssi_observer);\n\t\t*ppAdapter = (VOID *)pAd;' in s
 assert (root/'include/wr-rssi-record.h').read_text()==(tools/'rssi-record.h').read_text()
before=snapshot(good);assert run(good).returncode!=0;assert snapshot(good)==before
bad=fixture('changed-second-radio');path=bad/paths[-1]
path.write_text(path.read_text().replace('*ppAdapter = (VOID *)pAd;','*ppAdapter = NULL;'))
before=snapshot(bad);assert run(bad).returncode!=0;assert snapshot(bad)==before
print('PASS actual per-adapter storage preparation, initialization placement and all-source rejection without mutation')
