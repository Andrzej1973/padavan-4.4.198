#!/usr/bin/env python3
"""Expose MT WCID pre-write versus partial-write failures; legacy ABI retained."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
pins={'hw_ctrl/cmm_asic_mt.c':'70ccd1974ca06350ad62b0a157c334b8a538ccc463155c4f34f666d4686fc5bb',
      'include/rtmp.h':'04152e5b0e7c164cfc5a193b7d29843324adeac0617bec2987ce15cf08b0e5ce'}
for name,sha in pins.items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=sha:p.error('unreviewed source: '+name)
s=(src/'hw_ctrl/cmm_asic_mt.c').read_text()
signature='VOID AsicUpdateRxWCIDTable(RTMP_ADAPTER *pAd, USHORT WCID, UCHAR *pAddr)'
start=s.index(signature);end=s.index('\n}',start)+2
body=s[start:end]
assert body.count('return;')==6
first_write=body.index('RTMP_IO_WRITE32(')
before=body[:first_write].replace('return;','return WR_IOT_WCID_NOT_WRITTEN;')
after=body[first_write:].replace('return;','return WR_IOT_WCID_PARTIAL;')
body=before+after
body=body.replace(signature,'INT wr_iot_update_rx_wcid_checked(RTMP_ADAPTER *pAd, USHORT WCID, UCHAR *pAddr)',1)
clamp='\tif (wtbl_ctrl->wtbl_entry_cnt[0] > 0)\n\t\tWCID = (WCID < wtbl_ctrl->wtbl_entry_cnt[0] ? WCID : MCAST_WCID);'
assert body.count(clamp)==1
body=body.replace(clamp,'\tif (wtbl_ctrl->wtbl_entry_cnt[0] > 0) {\n\t\tif (WCID >= wtbl_ctrl->wtbl_entry_cnt[0])\n\t\t\treturn WR_IOT_WCID_NOT_WRITTEN;\n\t}',1)
body=body[:-1]+'    return WR_IOT_WCID_APPLIED;\n}'
wrapper='\n\n'+signature+'\n{\n    /* Legacy API historically maps invalid indices to multicast. */\n    if (pAd->mac_ctrl.wtbl_entry_cnt[0] > 0 &&\n        WCID >= pAd->mac_ctrl.wtbl_entry_cnt[0])\n        WCID = MCAST_WCID;\n    (void)wr_iot_update_rx_wcid_checked(pAd, WCID, pAddr);\n}\n'
s=s[:start]+body+wrapper+s[end:]
h=(src/'include/rtmp.h').read_text()
anchor=signature+';';assert h.count(anchor)==1
decl='''#ifdef MT_MAC
/* APPLIED means observed command completion, not a verified peer lifetime. */
#define WR_IOT_WCID_APPLIED 0
#define WR_IOT_WCID_NOT_WRITTEN (-1)
#define WR_IOT_WCID_PARTIAL (-2)
INT wr_iot_update_rx_wcid_checked(RTMP_ADAPTER *pAd, USHORT WCID, UCHAR *pAddr);
#endif
'''
h=h.replace(anchor,decl+anchor,1)
shutil.copytree(src,out)
for name,text in [('hw_ctrl/cmm_asic_mt.c',s),('include/rtmp.h',h)]:
    (out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-hardware-result.json').write_text(json.dumps({
    'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
    'scope':'MT result exposure only; insertion not bound, partial-write recovery absent',
    'legacy_wrapper_preserved':True,'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged MT WCID result split; no insertion binding or partial-write recovery')
