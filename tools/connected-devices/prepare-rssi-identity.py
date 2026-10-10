#!/usr/bin/env python3
"""Candidate station birth identity, after adapter preparation; no events.

Exhaustion disables observation identity, never changes station insertion.
"""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
tools=Path(__file__).parent;planned=[]
for radio in ('mt76x2','mt76x3'):
 root=a.source/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio
 header=root/'include/rtmp.h';init=root/'common/rtmp_init.c';table=root/'mgmt/mgmt_entrytb.c'
 h=header.read_text();s=init.read_text();t=table.read_text()
 station='typedef struct _MAC_TABLE_ENTRY {'
 observer='\tstruct wr_rssi_kernel wr_rssi_observer;'
 initialize='\t\twr_rssi_kernel_init(&pAd->wr_rssi_observer);'
 if h.count(station)!=1 or h.count(observer)!=1 or s.count(initialize)!=1 or 'wr_rssi_birth' in h:
  raise ValueError('Adapter/entry anchors changed; no files written')
 begin=t.index('MAC_TABLE_ENTRY *MacTableInsertEntry(')
 end=t.index('return pEntry;',begin)
 segment=t[begin:end];copy='COPY_MAC_ADDR(pEntry->Addr, pAddr);'
 if segment.count(copy)!=1 or 'NdisAcquireSpinLock(&pAd->MacTabLock)' not in segment:
  raise ValueError('Station insertion anchors changed; no files written')
 addition='''COPY_MAC_ADDR(pEntry->Addr, pAddr);
            memset(&pEntry->wr_rssi_identity, 0, sizeof(pEntry->wr_rssi_identity));
            wr_rssi_identity_create(&pAd->wr_rssi_birth, pEntry->wcid,
                                    pEntry->Addr, &pEntry->wr_rssi_identity);'''
 t=t[:begin]+segment.replace(copy,addition)+t[end:]
 h='#include "wr-rssi-identity.h"\n'+h.replace(station,station+'\n    struct wr_rssi_identity wr_rssi_identity;').replace(observer,observer+'\n    unsigned long long wr_rssi_birth;')
 s=s.replace(initialize,'\t\tpAd->wr_rssi_birth = 0;\n'+initialize)
 planned.extend([(header,h),(init,s),(table,t),(root/'include/wr-rssi-identity.h',(tools/'rssi-identity.h').read_text())])
for path,text in planned:path.write_text(text)
print('Prepared candidate birth identity at actual locked station insertion; compile/runtime unverified')
