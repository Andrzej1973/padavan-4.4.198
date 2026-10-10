#!/usr/bin/env python3
"""Candidate RSSI-only intent capture; requires prepare-rssi-adapter first.

Preserves original decision logic. Not production-enabled; no outcome events.
"""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
planned=[]
for driver,radio,bss,marker in (
 ('mt76x2',1,'apidx','if (overRssiThresCount >= CHECK_DATA_RSSI_UP_BOUND)'),
 ('mt76x3',0,'func_tb_idx','if ((pMbss->RssiLowForStaKickOut != 0) &&')):
 root=a.source/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/driver
 path=root/'ap/ap.c';s=path.read_text()
 if 'wr_rssi_observer' not in (root/'include/rtmp.h').read_text():raise ValueError('Adapter preparation required')
 if s.count(marker)!=1 or 'wr_rssi_attempt' in s or s.count('BOOLEAN bDisconnectSta = FALSE;')!=1:
  raise ValueError('RSSI anchors changed; no files written')
 start=s.index(marker);decision=s.index('bDisconnectSta = TRUE;',start)
 capture='''bDisconnectSta = TRUE;
            /* Preserve identity at the RSSI decision, before table deletion. */
            memcpy(wr_rssi_attempt.mac, pEntry->Addr, 6);
            wr_rssi_attempt.radio = RADIO;
            wr_rssi_attempt.bss = pEntry->BSS;
            wr_rssi_attempt.uptime_ms = ktime_to_ms(ktime_get());
            wr_rssi_tracking = wr_rssi_kernel_begin(&pAd->wr_rssi_observer, &wr_rssi_attempt);'''.replace('RADIO',str(radio)).replace('BSS',bss)
 s=s[:decision]+s[decision:].replace('bDisconnectSta = TRUE;',capture,1)
 s=s.replace('BOOLEAN bDisconnectSta = FALSE;','BOOLEAN bDisconnectSta = FALSE;\n        struct wr_rssi_record wr_rssi_attempt = {0};\n        int wr_rssi_tracking = 0;',1)
 # Until later stages consume the capture, retain a clean compiler build.
 s=s.replace('if (bDisconnectSta)','(void)wr_rssi_tracking;\n\t\tif (bDisconnectSta)',1)
 planned.append((path,'#include <linux/ktime.h>\n'+s))
for path,text in planned:path.write_text(text)
print('Prepared RSSI-only decision capture; no removal/roaming outcome claim')
