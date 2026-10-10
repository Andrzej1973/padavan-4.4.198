#!/usr/bin/env python3
"""Check actual station generation preparation; not a runtime test."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
tools=Path(__file__).parent
if a.output.exists():raise ValueError('Fresh output required')
a.output.mkdir(parents=True)
for radio in ('mt76x2','mt76x3'):
 for file in ('include/rtmp.h','common/rtmp_init.c','mgmt/mgmt_entrytb.c'):
  rel=Path('trunk/linux-4.4.x/drivers/net/wireless/mediatek')/radio/file
  dest=a.output/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((a.source/rel).read_bytes())
for script in ('prepare-rssi-adapter.py','prepare-rssi-identity.py'):
 subprocess.run([sys.executable,str(tools/script),str(a.output)],check=True)
for radio in ('mt76x2','mt76x3'):
 root=a.output/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio
 s=(root/'mgmt/mgmt_entrytb.c').read_text();start=s.index('MAC_TABLE_ENTRY *MacTableInsertEntry(')
 create=s.index('wr_rssi_identity_create(',start)
 assert s.index('NdisAcquireSpinLock(&pAd->MacTabLock)',start)<create<s.index('return pEntry;',start)
 assert s.index('COPY_MAC_ADDR(pEntry->Addr, pAddr);',start)<create
 assert s.count('wr_rssi_identity_create(')==1
 h=(root/'include/rtmp.h').read_text();assert h.count('struct wr_rssi_identity wr_rssi_identity;')==1
 init=(root/'common/rtmp_init.c').read_text();assert init.index('pAd->wr_rssi_birth = 0;')<init.index('*ppAdapter = (VOID *)pAd;')
before={p:p.read_bytes() for p in a.output.rglob('*') if p.is_file()}
r=subprocess.run([sys.executable,str(tools/'prepare-rssi-identity.py'),str(a.output)],capture_output=True)
assert r.returncode!=0 and all(p.read_bytes()==data for p,data in before.items())
print('PASS actual station identity field, locked creation placement, adapter initialization and repeat rejection')
