#!/usr/bin/env python3
"""Candidate synchronous RSSI read query; not production source preparation."""
import argparse,re
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);args=parser.parse_args()
tools=Path(__file__).parent;planned=[]
headers=('rssi-query-handler.h','rssi-query-response.h','rssi-query-record.h')
for driver,radio in (('mt76x2',1),('mt76x3',0)):
 root=args.source/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/driver
 path=root/'ap/ap_cfg.c';text=path.read_text()
 if 'wr_rssi_delete_entry' not in (root/'include/rtmp.h').read_text():
  raise ValueError('Complete RSSI candidate preparation required; no writes')
 if 'WR_RSSI_QUERY_OID' in text:raise ValueError('Query already prepared; no writes')
 # Actual conditional compilation still must reject conflicting case labels.
 for item in root.rglob('*'):
  if item.is_file() and item.suffix in ('.c','.h'):
   if re.search(r'\b(?:0[xX]0*7[eE]01|32257)\b',item.read_text(errors='replace')):
    raise ValueError('Candidate query number already present; no writes')
 start=text.index('INT RTMPAPQueryInformation(')
 match=re.search(r'switch\s*\(cmd\)\s*\{',text[start:])
 if not match:raise ValueError('Query dispatch anchor changed; no writes')
 offset=start+match.end()
 addition="""
        case WR_RSSI_QUERY_OID: {
            unsigned int wr_written = 0;
            int wr_status = wr_rssi_query_handle(&pAd->wr_rssi_observer,
                RADIO, wrq->u.data.pointer, wrq->u.data.length, &wr_written);
            if (wr_status == 0) wrq->u.data.length = wr_written;
            return wr_status;
        }
""".replace('RADIO',str(radio))
 text='#include "wr-rssi-query-handler.h"\n#define WR_RSSI_QUERY_OID 0x7e01\n'+text[:offset]+addition+text[offset:]
 planned.append((path,text))
 for name in headers:
  content=(tools/name).read_text()
  for dependency in ('rssi-kernel.h','rssi-record.h','rssi-query-request.h',*headers):
   content=content.replace('"'+dependency+'"','"wr-'+dependency+'"')
  planned.append((root/'include'/('wr-'+name),content))
for path,text in planned:path.write_text(text)
print('Prepared candidate administrator-only RSSI query; complete driver compile/runtime pending')
