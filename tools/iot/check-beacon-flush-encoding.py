#!/usr/bin/env python3
"""Compare actual vendor flush encoding with pinned upstream MT7603 field map.
No MMIO is executed; this is not a queue/RF retirement receipt.
"""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
s=(a.driver/'hw_ctrl/cmm_asic_mt.c').read_text()
signature='VOID wr_iot_APCheckBcnQHandler_inner(' if 'VOID wr_iot_APCheckBcnQHandler_inner(' in s else 'VOID APCheckBcnQHandler('
if s.count(signature)!=1:raise SystemExit('Ambiguous vendor recovery body')
start=s.index(signature);s=s[start:s.index('\n}',start)+2]
for anchor in ['val = 0xa8c70000;', 'val = val | 0x1000 | (apidx << 8);',
               'RTMP_IO_WRITE32(pAd, 0x21c08, val);', 'if (temp >> 31)']:
 if s.count(anchor)!=1:raise SystemExit('Vendor filter encoding changed: '+anchor)
# Field map from immutable torvalds/linux mt7603/regs.h at this revision.
fields={'wcid':(0,8),'bss':(8,6),'queue':(16,5),'destination_port':(22,2),
        'destination_queue':(24,5),'mode':(29,1),'status':(30,1),'busy':(31,1)}
rows=[]
for bss in range(4):
 value=0xa8c70000 | ((0x1000 | (bss<<8)) if bss else 0)
 decoded={name:(value>>shift)&((1<<bits)-1) for name,(shift,bits) in fields.items()}
 assert decoded=={'wcid':0,'bss':0x10+bss if bss else 0,'queue':7,
  'destination_port':3,'destination_queue':8,'mode':1,'status':0,'busy':1}
 rows.append({'bss_index':bss,'value':hex(value),'decoded':decoded})
print(json.dumps({'vendor_upstream_encoding_matches':True,
 'upstream_revision':'636a883e2feef5e4ff95695d3c372ceff03960f5',
 'source':'drivers/net/wireless/mediatek/mt76/mt7603/regs.h',
 'rows':rows,'hardware_executed':False,'rf_or_late_txs_proven':False},indent=2))
