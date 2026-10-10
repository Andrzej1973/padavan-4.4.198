#!/usr/bin/env python3
"""Candidate matched-entry clearing evidence; requires identity/decision prep.

Legacy deletion callers retain their signature and behavior. Observation
context does not authorize or prevent deletion. No roam/air ACK claim.
"""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
planned=[]
for radio in ('mt76x2','mt76x3'):
 root=a.source/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/radio
 header=root/'include/rtmp.h';table=root/'mgmt/mgmt_entrytb.c';ap=root/'ap/ap.c'
 h=header.read_text();t=table.read_text();s=ap.read_text()
 signature='BOOLEAN MacTableDeleteEntry(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr)'
 evidence='BOOLEAN wr_rssi_delete_entry(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr, const struct wr_rssi_identity *identity, const struct wr_rssi_record *attempt)'
 if t.count(signature)!=1 or h.count(signature+';')!=1 or 'wr_rssi_delete_entry' in t or 'wr_rssi_client' not in s:
  raise ValueError('Removal anchors changed; no files written')
 begin=t.index(signature);body=t.index('{',begin);depth=1;end=body+1
 while depth:
  depth+=(t[end]=='{')-(t[end]=='}');end+=1
 function=t[begin:end]
 match=re.search(r'if \(MAC_ADDR_EQUAL\(pEntry->Addr, pAddr\)\)\s*\{',function)
 if not match or function.count('SET_ENTRY_NONE(pEntry);')!=1:raise ValueError('Matched clearing branch changed')
 capture='''
            if (identity && attempt && identity->wcid == wcid &&
                wr_rssi_identity_matches(identity, &pEntry->wr_rssi_identity) &&
                MAC_ADDR_EQUAL(attempt->mac, pEntry->Addr)) {
                wr_cleared = *attempt;
                wr_clearing_matches = 1;
            }
'''
 function=function[:match.end()]+capture+function[match.end():]
 function=function.replace('SET_ENTRY_NONE(pEntry);','''SET_ENTRY_NONE(pEntry);
            if (wr_clearing_matches) {
                wr_cleared.stage = WR_RSSI_ENTRY_CLEARED;
                wr_cleared.uptime_ms = ktime_to_ms(ktime_get());
                wr_rssi_kernel_append(&pAd->wr_rssi_observer, &wr_cleared);
            }''')
 function=function.replace(signature,evidence,1)
 opening=function.index('{')+1
 function=function[:opening]+'\n    struct wr_rssi_record wr_cleared = {0};\n    int wr_clearing_matches = 0;\n'+function[opening:]
 wrapper=signature+'\n{\n    return wr_rssi_delete_entry(pAd, wcid, pAddr, NULL, NULL);\n}\n\n'
 t='#include <linux/ktime.h>\n'+t[:begin]+wrapper+function+t[end:]
 h=h.replace(signature+';',signature+';\n'+evidence+';')
 start=s.index('if (bDisconnectSta)',s.index('wr_rssi_kernel_begin('))
 call='MacTableDeleteEntry(pAd, pEntry->wcid, pEntry->Addr);'
 block=s.index('{',start);depth=1;finish=block+1
 while depth:
  depth+=(s[finish]=='{')-(s[finish]=='}');finish+=1
 segment=s[start:finish]
 if segment.count(call)!=(2 if radio=='mt76x3' else 1):raise ValueError('Disconnect deletion branches changed')
 replacement='wr_rssi_delete_entry(pAd, pEntry->wcid, pEntry->Addr, wr_rssi_tracking ? &wr_rssi_client : NULL, wr_rssi_tracking ? &wr_rssi_attempt : NULL);'
 s=s[:start]+segment.replace(call,replacement)+s[finish:]
 planned.extend([(header,h),(table,t),(ap,s)])
for path,text in planned:path.write_text(text)
print('Prepared matched-generation actual entry-clearing evidence; compilation and runtime unverified')
