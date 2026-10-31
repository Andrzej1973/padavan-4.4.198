#!/usr/bin/env python3
"""Expose checked deletion result without claiming DMA/completion retirement."""
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
pins={'hw_ctrl/cmm_asic_mt.c':'7966898b96e8219c4a38e85f4831be1ddfc2f2436d7a81772314b5319241d3e7',
      'include/rtmp.h':'eab43b3b130e29e8ce8efc2010e9e2079fce27ab49d31ab3dc3e654520db66e5'}
for name,sha in pins.items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=sha:p.error('unreviewed input: '+name)
layout=(src/'include/mac/mac_mt/wf_wtblon.h').read_text()
# Existing target register layout: address bytes 4/5 occupy DW0 low 16 bits;
# DW1 contains bytes 0..3. Refuse an unknown layout before applying masks.
if layout.count('UINT32 addr_4:8;')!=2 or layout.count('UINT32 addr_5:8;')!=2 or 'UINT32 addr_0;' not in layout:
    p.error('unreviewed WTBL address layout')
s=(src/'hw_ctrl/cmm_asic_mt.c').read_text()
signature='VOID AsicDelWcidTab(RTMP_ADAPTER *pAd, UCHAR wcid_idx)'
start=s.index(signature);end=s.index('\n}',start)+2;body=s[start:end]
assert body.count('return;')==4
body=body.replace(signature,'INT wr_iot_delete_wcid_checked(RTMP_ADAPTER *pAd, UCHAR wcid_idx)',1)
body=body.replace('\n{','\n{\n    INT wr_iot_wrote = 0;',1)
anchor='    if (wcid_idx == WCID_ALL) {'
assert body.count(anchor)==1
body=body.replace(anchor,'''    /* Reject aliases before the address helper can clamp an invalid WCID. */
    if (!pAd->mac_ctrl.wtbl_entry_cnt[0] ||
        (wcid_idx != WCID_ALL && wcid_idx >= pAd->mac_ctrl.wtbl_entry_cnt[0]))
        return WR_IOT_WCID_NOT_WRITTEN;

'''+anchor,1)
assert body.count('cnt_e = (WCID_ALL - 1);')==1
body=body.replace('cnt_e = (WCID_ALL - 1);','cnt_e = pAd->mac_ctrl.wtbl_entry_cnt[0] - 1;',1)
# ALL may fail at a later entry: preserve partial status across iterations.
body=body.replace('return;','return wr_iot_wrote ? WR_IOT_WCID_PARTIAL : WR_IOT_WCID_NOT_WRITTEN;')
write='        RTMP_IO_WRITE32(pAd, tb_entry.wtbl_addr[0], tb_entry.wtbl_1.wtbl_1_d0.word);'
assert body.count(write)==1
body=body.replace(write,'        wr_iot_wrote = 1;\n'+write,1)
last_release=body.rfind('#ifdef RTMP_PCI_SUPPORT\n\t\tNdisReleaseSpinLock(&pAd->IndirectUpdateLock);')
assert last_release>body.index('/* Admission Control Counter Clear */')
readback='''        /* Address-clear readback only; old DMA/TxS ownership is separate. */
        RTMP_IO_READ32(pAd, tb_entry.wtbl_addr[0], &Value);
        if (Value & 0x0000ffffU) {
#ifdef RTMP_PCI_SUPPORT
            NdisReleaseSpinLock(&pAd->IndirectUpdateLock);
#endif
            return WR_IOT_WCID_PARTIAL;
        }
        RTMP_IO_READ32(pAd, tb_entry.wtbl_addr[0] + 4, &Value);
        if (Value != 0) {
#ifdef RTMP_PCI_SUPPORT
            NdisReleaseSpinLock(&pAd->IndirectUpdateLock);
#endif
            return WR_IOT_WCID_PARTIAL;
        }

'''
body=body[:last_release]+readback+body[last_release:]
body=body[:-1]+'    return WR_IOT_WCID_APPLIED;\n}'
wrapper='\n\n'+signature+'\n{\n    (void)wr_iot_delete_wcid_checked(pAd, wcid_idx);\n}\n'
s=s[:start]+body+wrapper+s[end:]
h=(src/'include/rtmp.h').read_text();anchor='INT wr_iot_update_rx_wcid_checked(RTMP_ADAPTER *pAd, USHORT WCID, UCHAR *pAddr);'
assert h.count(anchor)==1
h=h.replace(anchor,anchor+'\nINT wr_iot_delete_wcid_checked(RTMP_ADAPTER *pAd, UCHAR wcid_idx);',1)
shutil.copytree(src,out)
for n,t in [('hw_ctrl/cmm_asic_mt.c',s),('include/rtmp.h',h)]:
    (out/n).write_text(t,encoding='utf-8',newline='\n')
out.with_name(out.name+'-delete-result.json').write_text(json.dumps({
    'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
    'scope':'delete result plus address-clear readback; no completion drain or peer recovery binding',
    'target_compiled':False,'production_installed':False},indent=2)+'\n')
print('Staged checked WCID deletion result; legacy wrapper retained')
