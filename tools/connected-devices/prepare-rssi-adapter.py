#!/usr/bin/env python3
"""Candidate only: attach embedded observation storage to actual adapters.

Not called by the production source preparation yet. Requires kernel/driver
compile verification before enabling. No events, queries or teardown hooks.
"""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
tools=Path(__file__).parent
planned=[]
for radio in ('mt76x2','mt76x3'):
 root=a.source/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio
 header=root/'include/rtmp.h';init=root/'common/rtmp_init.c'
 h=header.read_text();s=init.read_text()
 field='\tNDIS_SPIN_LOCK MacTabLock;'
 publish='\t\t*ppAdapter = (VOID *)pAd;'
 if h.count(field)!=1 or s.count(publish)!=1 or 'wr_rssi_observer' in h or 'wr_rssi_kernel_init' in s:
  raise ValueError('Adapter source anchors changed; no files written: '+radio)
 h='#include "wr-rssi-kernel.h"\n'+h.replace(field,field+'\n\tstruct wr_rssi_kernel wr_rssi_observer;')
 s=s.replace(publish,'\t\twr_rssi_kernel_init(&pAd->wr_rssi_observer);\n'+publish)
 planned.extend([(header,h),(init,s),
                 (root/'include/wr-rssi-kernel.h',(tools/'rssi-kernel.h').read_text().replace('"rssi-record.h"','"wr-rssi-record.h"').replace('"rssi-query-request.h"','"wr-rssi-query-request.h"')),
                 (root/'include/wr-rssi-record.h',(tools/'rssi-record.h').read_text()),
                 (root/'include/wr-rssi-query-request.h',(tools/'rssi-query-request.h').read_text())])
for path,text in planned:path.write_text(text)
print('Prepared embedded per-adapter RSSI storage before adapter publication; driver compile and runtime unverified')
