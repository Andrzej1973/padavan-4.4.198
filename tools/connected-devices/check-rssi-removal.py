#!/usr/bin/env python3
"""Source preparation checks; no runtime deletion/roaming proof."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
tools=Path(__file__).parent
subprocess.run([sys.executable,str(tools/'check-rssi-decision.py'),str(a.source),str(a.output)],check=True)
subprocess.run([sys.executable,str(tools/'prepare-rssi-removal.py'),str(a.output)],check=True)
for radio in ('mt76x2','mt76x3'):
 root=a.output/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio
 t=(root/'mgmt/mgmt_entrytb.c').read_text();s=(root/'ap/ap.c').read_text()
 assert 'return wr_rssi_delete_entry(pAd, wcid, pAddr, NULL, NULL);' in t
 assert t.count('wr_rssi_identity_matches(identity, &pEntry->wr_rssi_identity)')==1
 capture=t.index('wr_cleared = *attempt;');clear=t.index('SET_ENTRY_NONE(pEntry);',capture)
 assert capture<clear<t.index('wr_cleared.stage = WR_RSSI_ENTRY_CLEARED;',clear)<t.index('NdisReleaseSpinLock(&pAd->MacTabLock)',clear)
 assert s.count('wr_rssi_delete_entry(pAd, pEntry->wcid')==(2 if radio=='mt76x3' else 1)
before={p:p.read_bytes() for p in a.output.rglob('*') if p.is_file()}
r=subprocess.run([sys.executable,str(tools/'prepare-rssi-removal.py'),str(a.output)],capture_output=True)
assert r.returncode!=0 and all(p.read_bytes()==v for p,v in before.items())
# A changed second radio must reject the whole operation before first-radio writes.
negative=a.output.with_name(a.output.name+'-changed-second-radio')
assert not negative.exists()
subprocess.run([sys.executable,str(tools/'check-rssi-decision.py'),str(a.source),str(negative)],check=True)
changed=negative/'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/mgmt/mgmt_entrytb.c'
text=changed.read_text()
anchor='BOOLEAN MacTableDeleteEntry(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr)'
assert text.count(anchor)==1
changed.write_text(text.replace(anchor,anchor.replace('UCHAR *pAddr','UCHAR *changedAddr'),1))
before={p:p.read_bytes() for p in negative.rglob('*') if p.is_file()}
r=subprocess.run([sys.executable,str(tools/'prepare-rssi-removal.py'),str(negative)],capture_output=True)
assert r.returncode!=0
assert before=={p:p.read_bytes() for p in negative.rglob('*') if p.is_file()}
print('PASS changed second radio rejects all removal preparation writes')
print('PASS legacy delete wrapper, matched-generation clearing evidence and both conditional deletion branches')
