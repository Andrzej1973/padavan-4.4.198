#!/usr/bin/env python3
"""Verify exact-source decision preparation without changing original logic."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
tools=Path(__file__).parent
if a.output.exists():raise ValueError('Fresh output required')
a.output.mkdir(parents=True)
original={}
for radio in ('mt76x2','mt76x3'):
 for file in ('include/rtmp.h','common/rtmp_init.c','ap/ap.c'):
  rel=Path('trunk/linux-4.4.x/drivers/net/wireless/mediatek')/radio/file
  dest=a.output/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((a.source/rel).read_bytes())
  if file=='ap/ap.c':original[radio]=dest.read_text()
for script in ('prepare-rssi-adapter.py','prepare-rssi-decision.py'):
 subprocess.run([sys.executable,str(tools/script),str(a.output)],check=True)
for radio,band,bss in (('mt76x2',1,'apidx'),('mt76x3',0,'func_tb_idx')):
 path=a.output/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio/'ap/ap.c';s=path.read_text()
 assert s.count('wr_rssi_kernel_begin(')==1
 assert s.count('bDisconnectSta = TRUE;')==original[radio].count('bDisconnectSta = TRUE;')
 assert s.count('MiniportMMRequest(')==original[radio].count('MiniportMMRequest(')
 assert f'wr_rssi_attempt.radio = {band};' in s and f'wr_rssi_attempt.bss = pEntry->{bss};' in s
 marker='if (overRssiThresCount >= CHECK_DATA_RSSI_UP_BOUND)' if band==1 else 'if ((pMbss->RssiLowForStaKickOut != 0) &&'
 assert s.index(marker)<s.index('wr_rssi_kernel_begin(')<s.index('(void)wr_rssi_tracking;')
before={p:p.read_bytes() for p in a.output.rglob('*') if p.is_file()}
r=subprocess.run([sys.executable,str(tools/'prepare-rssi-decision.py'),str(a.output)],capture_output=True)
assert r.returncode!=0 and all(p.read_bytes()==data for p,data in before.items())
print('PASS actual RSSI decision-only identity/radio capture, original decisions/transports and repeat rejection')
