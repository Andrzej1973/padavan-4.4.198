#!/usr/bin/env python3
"""Verify actual RSSI enforcement boundaries before adding action events."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
for radio in ('mt76x2','mt76x3'):
 root=a.source/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio/'ap'
 s=(root/'ap.c').read_text(encoding='utf-8')
 if radio=='mt76x2':
  start=s.index('//YF: kickout sta when 3 of 5 exceeds the threshold.')
  expected=['CHECK_DATA_RSSI_UP_BOUND 3','pEntry->LastDataRssi[rssiIndex] !=0','overRssiThresCount >= CHECK_DATA_RSSI_UP_BOUND']
 else:
  start=s.index('if ((pMbss->RssiLowForStaKickOut != 0) &&')
  expected=['RTMPAvgRssi(pAd, &pEntry->RssiSample)','avgRssi=','bDisconnectSta = TRUE;']
 body=s[start:];end=body.index('if (bDisconnectSta)');condition=body[:end]
 for token in expected:assert token in condition,(radio,token)
 disconnect=body[end:];allocation=disconnect.index('NStatus = MlmeAllocateMemory')
 failed=disconnect.index('NStatus != NDIS_STATUS_SUCCESS',allocation)
 continuation=disconnect.index('continue;',failed)
 send=disconnect.index('MiniportMMRequest',continuation)
 deletion=disconnect.index('MacTableDeleteEntry',send)
 assert send<deletion
 assert 'pEntry->wcid, pEntry->Addr' in disconnect[deletion:deletion+100]
 if radio=='mt76x3':
  assert 'WH_EZ_SETUP' in disconnect[send:deletion]
  assert 'ez_set_delete_peer_in_differed_context' in disconnect[send:deletion]
 assert allocation<failed<continuation<send
 assert 'IW_AGEOUT_EVENT_FLAG' in disconnect[:allocation]
 print('PASS',radio,'RSSI decision precedes generic ageout; allocation failure skips deauth submission')
 print('PASS',radio,'deauth submission precedes table deletion call; call alone is not completion evidence')
print('Source evidence only: no client removal, frame acknowledgement or runtime result verified')
